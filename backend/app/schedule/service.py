"""排班号源业务逻辑层"""

from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.schedule.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.schedule import repository as repo
from app.shared.redis import get_redis, adjust_source_redis
from app.exception.base import NotFoundException


async def _fill_redis_remain(data: dict) -> dict:
    """从 Redis 查询号源实时剩余量，回填到排班数据"""
    r = await get_redis()
    normal_key = f"source:{data['id']}:normal"
    elder_key = f"source:{data['id']}:elder"

    normal_remain = await r.get(normal_key)
    elder_remain = await r.get(elder_key)

    # Redis 无数据时从 MySQL 初始值加载
    if normal_remain is None:
        normal_remain = data["normal_num"]
        await r.set(normal_key, normal_remain)
    if elder_remain is None:
        elder_remain = data["elder_priority_num"]
        await r.set(elder_key, elder_remain)

    data["normal_remain"] = int(normal_remain)
    data["elder_remain"] = int(elder_remain)
    return data


async def list_schedules(session: AsyncSession, doctor_id: int | None = None,
                         from_date: date | None = None) -> list[ScheduleResponse]:
    rows = await repo.list_with_relations(session, doctor_id, from_date)
    results = []
    for r in rows:
        r = await _fill_redis_remain(r)
        results.append(ScheduleResponse(**r))
    return results


async def get_schedule_by_id(session: AsyncSession, schedule_id: int) -> ScheduleResponse:
    """按 ID 查询单个排班（含四级联表 + Redis 实时剩余号源）"""
    row = await repo.get_by_id_with_relations(session, schedule_id)
    if not row:
        raise NotFoundException("排班不存在")
    row = await _fill_redis_remain(row)
    return ScheduleResponse(**row)


async def create_schedule(session: AsyncSession, req: ScheduleCreate) -> ScheduleResponse:
    s = await repo.create(session, doctor_id=req.doctor_id, work_date=req.work_date,
                          time_period=req.time_period, normal_num=req.normal_num,
                          elder_priority_num=req.elder_priority_num)

    # 同步号源到 Redis
    r = await get_redis()
    await r.set(f"source:{s.id}:normal", req.normal_num)
    await r.set(f"source:{s.id}:elder", req.elder_priority_num)

    return ScheduleResponse(id=s.id, doctor_id=s.doctor_id, work_date=s.work_date,
                            time_period=s.time_period, normal_num=s.normal_num,
                            elder_priority_num=s.elder_priority_num,
                            normal_remain=s.normal_num, elder_remain=s.elder_priority_num)


async def update_schedule(session: AsyncSession, schedule_id: int, req: ScheduleUpdate) -> ScheduleResponse:
    s = await repo.get_by_id(session, schedule_id)
    if not s:
        raise NotFoundException("排班不存在")

    # 保存旧值，用于计算 Redis 增量
    old_normal = s.normal_num
    old_elder = s.elder_priority_num

    update_kwargs = {}
    if req.normal_num is not None:
        update_kwargs["normal_num"] = req.normal_num
    if req.elder_priority_num is not None:
        update_kwargs["elder_priority_num"] = req.elder_priority_num

    s = await repo.update(session, s, **update_kwargs)

    # 同步 Redis：用增量调整而非直接覆盖，防止已扣减号源"凭空回来"
    r = await get_redis()
    if req.normal_num is not None:
        delta = req.normal_num - old_normal
        if delta != 0:
            await adjust_source_redis(s.id, "normal", delta)
    if req.elder_priority_num is not None:
        delta = req.elder_priority_num - old_elder
        if delta != 0:
            await adjust_source_redis(s.id, "elder", delta)

    return ScheduleResponse(id=s.id, doctor_id=s.doctor_id, work_date=s.work_date,
                            time_period=s.time_period, normal_num=s.normal_num,
                            elder_priority_num=s.elder_priority_num,
                            normal_remain=req.normal_num if req.normal_num is not None else s.normal_num,
                            elder_remain=req.elder_priority_num if req.elder_priority_num is not None else s.elder_priority_num)


async def delete_schedule(session: AsyncSession, schedule_id: int):
    s = await repo.get_by_id(session, schedule_id)
    if not s:
        raise NotFoundException("排班不存在")
    await repo.soft_delete(session, s)
