"""Redis 客户端 + Lua 脚本执行器

用于：号源缓存、候诊排队、Token 缓存、接口限流
"""

import redis.asyncio as aioredis
from app.config import settings

# 全局 Redis 客户端
redis_client: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """初始化 Redis 客户端（应用启动时调用）"""
    global redis_client
    redis_client = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        password=settings.REDIS_PASSWORD or None,
        encoding="utf-8",
        decode_responses=True,
    )
    await redis_client.ping()
    return redis_client


async def close_redis():
    """关闭 Redis 连接（应用关闭时调用）"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def get_redis() -> aioredis.Redis:
    """返回 Redis 客户端（未初始化则自动连接）"""
    global redis_client
    if redis_client is None:
        redis_client = await init_redis()
    return redis_client


# ---- Lua 脚本 ----

# 原子扣减号源脚本
LUA_DECREASE_SOURCE = """
local normal_key = KEYS[1]
local elder_key = KEYS[2]
local source_type = ARGV[1]  -- "normal" | "elder"
local delta = tonumber(ARGV[2])

if source_type == "normal" then
    local current = tonumber(redis.call('GET', normal_key) or 0)
    if current >= delta then
        redis.call('DECRBY', normal_key, delta)
        return 1
    else
        return 0
    end
elseif source_type == "elder" then
    local current = tonumber(redis.call('GET', elder_key) or 0)
    if current >= delta then
        redis.call('DECRBY', elder_key, delta)
        return 1
    else
        return 0
    end
end
return 0
"""

# 号源回滚脚本
LUA_ROLLBACK_SOURCE = """
local normal_key = KEYS[1]
local elder_key = KEYS[2]
local source_type = ARGV[1]
local delta = tonumber(ARGV[2])

if source_type == "normal" then
    redis.call('INCRBY', normal_key, delta)
elseif source_type == "elder" then
    redis.call('INCRBY', elder_key, delta)
end
return 1
"""


async def decrease_source_redis(schedule_id: int, source_type: str) -> bool:
    """Redis Lua 原子扣减号源。成功返回 True，不足返回 False"""
    r = await get_redis()
    normal_key = f"source:{schedule_id}:normal"
    elder_key = f"source:{schedule_id}:elder"
    result = await r.eval(LUA_DECREASE_SOURCE, 2, normal_key, elder_key, source_type, 1)
    return result == 1


async def rollback_source_redis(schedule_id: int, source_type: str):
    """Redis Lua 回滚号源"""
    r = await get_redis()
    normal_key = f"source:{schedule_id}:normal"
    elder_key = f"source:{schedule_id}:elder"
    await r.eval(LUA_ROLLBACK_SOURCE, 2, normal_key, elder_key, source_type, 1)


# 增量调整号源脚本（管理员修改号源总量时使用，下限为 0）
LUA_ADJUST_SOURCE = """
local key = KEYS[1]
local delta = tonumber(ARGV[1])
local current = tonumber(redis.call('GET', key) or 0)
local new_val = current + delta
if new_val < 0 then new_val = 0 end
redis.call('SET', key, new_val)
return new_val
"""


async def adjust_source_redis(schedule_id: int, source_type: str, delta: int):
    """增量调整号源（管理员改号源总量时用）"""
    r = await get_redis()
    key = f"source:{schedule_id}:{source_type}"
    await r.eval(LUA_ADJUST_SOURCE, 1, key, delta)
