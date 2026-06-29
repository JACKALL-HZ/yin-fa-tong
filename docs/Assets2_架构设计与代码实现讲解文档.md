# Assets2 — 银发通架构设计与代码实现讲解文档

> 版本：v1.0 | 更新日期：2026-06-27 | 适用范围：银发通适老化智慧就医服务平台

---

## 一、技术架构全景

### 1.1 整体架构图

```mermaid
graph TB
    subgraph 前端层
        A[Vue3 + TypeScript] --> B[Element Plus UI]
        A --> C[Pinia 状态管理]
        A --> D[Vue Router 路由]
        A --> E[Axios HTTP 客户端]
    end

    subgraph 反向代理
        F[Nginx]
    end

    subgraph 应用层
        G[FastAPI + Uvicorn ASGI]
        G --> H[中间件: CORS / RequestID / Logging]
        G --> I[依赖注入: DbSession / Pagination]
        G --> J[全局异常处理]
    end

    subgraph 业务模块层
        K[Auth] --> L[User]
        M[Hospital] --> N[Department] --> O[Doctor]
        O --> P[Schedule] --> Q[Reserve] --> R[Queue]
        Q --> S[Payment]
        T[Guide] --> U[Search]
        V[Accompany] --> W[Reminder]
        X[Message] --> Y[Report] --> Z[Statistics]
    end

    subgraph 基础设施层
        AA[MySQL 8.0]
        BB[Redis 7]
        CC[RabbitMQ]
        DD[Elasticsearch 8]
    end

    A --> F
    F --> G
    K --> AA
    Q --> BB
    Q --> CC
    U --> DD
```

### 1.2 技术栈版本

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.111.0 | 异步Web框架，自动OpenAPI文档 |
| ASGI 服务器 | Uvicorn | 0.30.1 | 异步HTTP服务器 |
| ORM | SQLAlchemy | 2.0.31 | 异步ORM，声明式映射 |
| 数据库驱动 | aiomysql | 0.2.0 | MySQL异步驱动 |
| 数据库迁移 | Alembic | 1.13.1 | 数据库版本管理 |
| 数据校验 | Pydantic v2 | 2.7.4 | 请求/响应Schema校验 |
| 认证 | python-jose + bcrypt | 3.3.0 / 4.1.3 | JWT签发 + 密码哈希 |
| 缓存 | redis[async] | 5.0.7 | Redis异步客户端 |
| 消息队列 | aio-pika | 9.4.2 | RabbitMQ异步客户端 |
| 搜索引擎 | elasticsearch[async] | 8.14.0 | ES异步客户端 |
| 定时任务 | APScheduler | 3.10.4 | 异步调度器 |
| AI集成 | httpx | 0.27.0 | Dify API调用 |
| 支付 | alipay-sdk-python | 3.7.33 | 支付宝SDK |
| 前端框架 | Vue 3 | 3.x | 渐进式前端框架 |
| 状态管理 | Pinia | - | Vue3官方状态管理 |
| HTTP客户端 | Axios | - | Promise-based HTTP |
| UI组件 | Element Plus | - | Vue3组件库 |

---

## 二、后端分层架构详解

### 2.1 分层模型

```
┌─────────────────────────────────────────────┐
│  Router (router.py)                         │  路由层：定义API端点，参数校验，调用Service
├─────────────────────────────────────────────┤
│  Service (service.py)                       │  业务层：核心业务逻辑，事务边界
├─────────────────────────────────────────────┤
│  Repository (repository.py)                 │  数据层：SQLAlchemy ORM查询，数据访问
├─────────────────────────────────────────────┤
│  Models (models.py)                         │  模型层：数据库表结构定义
├─────────────────────────────────────────────┤
│  Schemas (schemas.py)                       │  Schema层：Pydantic请求/响应模型
└─────────────────────────────────────────────┘
```

### 2.2 源码示例：预约挂号的分层调用链

**Router 层** — `backend/app/reserve/router.py`

```python
@router.post("", response_model=ApiResponse)
async def create_reserve(
    req: CreateReserveRequest,
    current_user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建预约挂号订单"""
    svc = ReserveService(db)
    data = await svc.create_reserve(current_user.id, req)
    return ok(data=data)
```

关键设计：
- `Depends(get_current_user)` — 自动从JWT提取用户信息
- `Depends(get_db)` — 自动管理数据库会话生命周期
- 返回统一的 `ApiResponse` 结构

**Service 层** — `backend/app/reserve/service.py`

```python
async def create_reserve(self, user_id: int, req: CreateReserveRequest):
    # 1. 校验排班存在
    schedule = await self.repo.get_schedule_with_doctor(req.schedule_id)
    if not schedule:
        raise NotFoundException("排班不存在")

    # 2. Redis SET NX 预约去重
    dedup_key = f"reserve_dedup:{req.schedule_id}:{user_id}"
    is_new = await redis_client.set(dedup_key, "1", nx=True, ex=900)
    if not is_new:
        raise ConflictException("请勿重复预约")

    # 3. Lua脚本原子扣减号源
    source_key = f"source:{req.schedule_id}:{source_type}"
    ok = await decrease_source(source_key)
    if not ok:
        await redis_client.delete(dedup_key)
        raise BadRequestException("号源不足")

    # 4. 创建数据库订单
    reserve = await self.repo.create_reserve(user_id, req)

    # 5. 生成候诊编号
    queue_code = f"NK{reserve.create_time.strftime('%Y%m%d')}{reserve.id:04d}"
    await self.repo.update_queue_code(reserve.id, queue_code)

    # 6. 注册Redis候诊队列
    await register_queue(req.schedule_id, queue_code, reserve.id)

    # 7. RabbitMQ发送延时取消消息
    await publish_delay("delay.task", {"reserve_id": reserve.id}, 900_000)
```

关键设计：
- **事务边界**：数据库操作在Service层统一管理
- **分布式锁**：Redis SET NX 实现预约去重
- **原子操作**：Lua脚本保证号源扣减原子性
- **异常回滚**：扣减失败时清除去重标记

**Repository 层** — `backend/app/reserve/repository.py`

```python
async def get_schedule_with_doctor(self, schedule_id: int):
    stmt = (
        select(ScheduleModel)
        .options(selectinload(ScheduleModel.doctor).selectinload(DoctorModel.department))
        .where(ScheduleModel.id == schedule_id, ScheduleModel.is_deleted == 0)
    )
    result = await self.db.execute(stmt)
    return result.scalar_one_or_none()
```

关键设计：
- `selectinload` — 预加载关联数据，避免N+1查询
- `is_deleted == 0` — 全局软删除过滤

**Models 层** — `backend/app/reserve/models.py`

```python
class ReserveModel(Base):
    __tablename__ = "tb_reserve"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_user.id"))
    schedule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_schedule.id"))
    elder_bind_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("tb_elder_bind.id"))
    source_type: Mapped[str] = mapped_column(String(10), default="normal")
    queue_code: Mapped[Optional[str]] = mapped_column(String(20))
    queue_status: Mapped[int] = mapped_column(Integer, default=1)
    pay_status: Mapped[int] = mapped_column(Integer, default=1)
    order_status: Mapped[int] = mapped_column(Integer, default=1)
```

关键设计：
- `Mapped[Optional[int]]` — SQLAlchemy 2.0 新语法，类型注解驱动
- 继承 `TimestampMixin` 自动获得 `create_time`, `update_time`, `is_deleted`

---

## 三、FastAPI 应用生命周期管理

### 3.1 lifespan 源码分析

**文件**: `backend/app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== 启动阶段 =====
    # 1. Redis（必须成功）
    await init_redis()

    # 2. RabbitMQ（可降级）
    try:
        await init_rabbitmq()
    except Exception as e:
        logger.error(f"RabbitMQ不可用: {e}")

    # 3. 延时队列消费者（后台协程）
    consumer_task = asyncio.create_task(start_consumer())
    consumer_task.add_done_callback(_on_consumer_done)

    # 4. Dify AI客户端（可降级）
    try:
        await dify_client.start()
    except Exception as e:
        logger.error(f"Dify不可用: {e}")

    # 5. Elasticsearch（可降级）
    try:
        es = await init_es()
        await ensure_indexes(es)
    except Exception as e:
        logger.error(f"ES不可用: {e}")

    # 6. 定时任务调度器
    start_scheduler()

    yield  # ===== 应用运行 =====

    # ===== 关闭阶段（反序释放）=====
    consumer_task.cancel()
    shutdown_scheduler()
    await close_redis()
    await close_rabbitmq()
    await dify_client.close()
    await close_es()
```

### 3.2 降级策略

| 组件 | 降级行为 |
|------|----------|
| Redis | 不可降级，启动失败则号源/排队/Token全部不可用 |
| RabbitMQ | 可降级，MQ不可用时预约创建不阻断，定时任务兜底处理超时 |
| Dify AI | 可降级，不可用时自动回退到本地规则引擎 |
| Elasticsearch | 可降级，搜索功能不可用，不影响核心挂号流程 |

### 3.3 中间件注册

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.add_middleware(RequestIDMiddleware)      # 为每个请求生成唯一ID
app.add_middleware(RequestLoggingMiddleware)  # 记录请求耗时和状态码
```

### 3.4 路由注册

```python
for prefix, router in [
    ("/auth", auth_router),
    ("/user", user_router),
    ("/hospitals", hospital_router),
    ("/departments", department_router),
    ("/doctors", doctor_router),
    ("/schedules", schedule_router),
    ("/reserves", reserve_router),
    ("/queue", queue_router),
    ("/payment", payment_router),
    ("/messages", message_router),
    ("/guide", guide_router),
    ("/reminders", reminder_router),
    ("/statistics", statistics_router),
    ("/volunteers", volunteer_router),
    ("/accompany-orders", accompany_router),
    ("/reports", report_router),
    ("/search", search_router),
]:
    app.include_router(router, prefix=f"/api{prefix}")
```

---

## 四、数据库连接池管理

### 4.1 SQLAlchemy Async 引擎配置

**文件**: `backend/app/shared/database.py`

```python
engine = create_async_engine(
    settings.MYSQL_URL,       # mysql+aiomysql://user:pass@host:port/db
    pool_size=20,              # 连接池大小
    max_overflow=40,           # 最大溢出连接（总上限60）
    pool_recycle=3600,         # 连接回收时间（秒）
    echo=False,                # 不打印SQL
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,    # commit后属性不过期，避免懒加载异常
)
```

### 4.2 get_db 依赖注入

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session_factory()
    try:
        yield session
        await session.commit()      # 成功则提交
    except Exception:
        await session.rollback()    # 失败则回滚
        raise
    finally:
        await session.close()       # 释放连接
```

### 4.3 Post-Commit ES 同步钩子（核心设计亮点）

```python
# 注册钩子
def register_es_hook(session: AsyncSession, coro_factory: Callable):
    hooks = session.info.setdefault("es_hooks", [])
    hooks.append(coro_factory)

# get_db 中，commit成功后执行
async def get_db():
    ...
    yield session
    await session.commit()
    # 执行所有ES同步钩子
    for hook in session.info.get("es_hooks", []):
        try:
            await hook()
        except Exception as e:
            logger.warning(f"ES hook执行失败: {e}")
```

**设计优势**：
- 保证DB和ES的**最终一致性**，避免双写不一致
- hook失败仅warning日志，不影响主流程
- 漏同步由下次全量同步补齐

---

## 五、Redis 缓存与 Lua 原子脚本

### 5.1 客户端初始化

**文件**: `backend/app/shared/redis.py`

```python
redis_client: redis.asyncio.Redis = None

async def init_redis():
    global redis_client
    redis_client = redis.asyncio.from_url(
        settings.REDIS_URL,       # redis://host:port/db
        decode_responses=True,    # 自动UTF-8解码
    )
```

### 5.2 三大 Lua 原子脚本

**脚本1：原子扣减号源**

```lua
-- KEYS[1] = source:{schedule_id}:normal
-- KEYS[2] = source:{schedule_id}:elder
-- ARGV[1] = source_type ("normal" or "elder")
-- ARGV[2] = delta (扣减数量)
local key = (ARGV[1] == "elder") and KEYS[2] or KEYS[1]
local current = tonumber(redis.call("GET", key) or "0")
if current >= tonumber(ARGV[2]) then
    redis.call("DECRBY", key, ARGV[2])
    return 1
else
    return 0
end
```

**设计要点**：
- `GET` + `DECRBY` 在同一个Lua脚本中执行，保证**原子性**
- 先检查余量再扣减，防止并发超卖
- 返回 1=成功 / 0=号源不足

**脚本2：号源回滚**

```lua
-- 取消预约时恢复号源
local key = (ARGV[1] == "elder") and KEYS[2] or KEYS[1]
redis.call("INCRBY", key, ARGV[2])
return 1
```

**脚本3：管理员增量调整**

```lua
-- 管理员修改号源总量，支持正/负增量，下限为0
local key = (ARGV[1] == "elder") and KEYS[2] or KEYS[1]
local current = tonumber(redis.call("GET", key) or "0")
local new_val = current + tonumber(ARGV[2])
if new_val < 0 then new_val = 0 end
redis.call("SET", key, new_val)
return new_val
```

### 5.3 缓存 Key 设计

| Key | 类型 | TTL | 说明 |
|-----|------|-----|------|
| `source:{schedule_id}:normal` | String(int) | 无 | 普通号实时剩余量 |
| `source:{schedule_id}:elder` | String(int) | 无 | 老年优先号实时剩余量 |
| `reserve_dedup:{schedule_id}:{user_id}` | String | 900s | 预约去重标记 |
| `queue:{schedule_id}:total` | String(int) | 无 | 候诊总人数 |
| `queue:{schedule_id}:current` | String(int) | 无 | 当前叫号数 |
| `queue_item:{queue_code}` | Hash | 无 | 个人排队信息 |

---

## 六、RabbitMQ 消息队列

### 6.1 连接与交换机配置

**文件**: `backend/app/shared/rabbitmq.py`

```python
connection: RobustConnection = None  # 支持自动重连
channel: AbstractChannel = None

# 四个交换机
EX_RESERVE  = "ex_reserve"   # Direct - 挂号通知
EX_QUEUE    = "ex_queue"     # Direct - 候诊通知
EX_ACCOMPANY = "ex_accompany" # Direct - 陪诊通知
EX_DELAY    = "ex_delay"     # X_DELAYED_MESSAGE - 延时任务

# 四个队列
Q_RESERVE_NOTIFY   = "q_reserve_notify"
Q_QUEUE_NOTIFY     = "q_queue_notify"
Q_ACCOMPANY_NOTIFY = "q_accompany_notify"
Q_DELAY_TASKS      = "q_delay_tasks"
```

### 6.2 延迟交换机实现

```python
# 使用 RabbitMQ x-delayed-message 插件
delay_exchange = await channel.declare_exchange(
    EX_DELAY,
    ExchangeType.X_DELAYED_MESSAGE,  # 特殊交换机类型
    durable=True,
    arguments={"x-delayed-type": "direct"},  # 内部路由类型
)

# 发送延迟消息
async def publish_delay(routing_key: str, body: dict, delay_ms: int):
    message = Message(
        json.dumps(body).encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
        headers={"x-delay": delay_ms},  # 延迟毫秒数
    )
    await delay_exchange.publish(message, routing_key=routing_key)
```

### 6.3 消费者实现

```python
# 延时任务消费者
async def on_delay_task(message: AbstractIncomingMessage):
    async with message.process():
        body = json.loads(message.body)
        task_type = body.get("task_type")

        if task_type == "reserve_timeout":
            # 支付超时取消
            await handle_reserve_timeout(body["reserve_id"])
        elif task_type == "health_reminder":
            # 健康提醒
            await handle_health_reminder(body["reminder_id"])
```

---

## 七、Elasticsearch 搜索引擎集成

### 7.1 索引映射定义

**文件**: `backend/app/search/mappings.py`

```python
# 通用 settings 模板
INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "ik_index_analyzer": {"type": "custom", "tokenizer": "ik_max_word"},
                "ik_search_analyzer": {"type": "custom", "tokenizer": "ik_smart"},
            }
        }
    }
}

# 医院索引映射
INDEX_HOSPITAL = {
    **INDEX_SETTINGS,
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "hospital_name": {"type": "text", "analyzer": "ik_index_analyzer", "search_analyzer": "ik_search_analyzer"},
            "hospital_level": {"type": "keyword"},  # 精确匹配，不分词
            "address": {"type": "text", "analyzer": "ik_index_analyzer", "search_analyzer": "ik_search_analyzer"},
        }
    }
}
```

**分词策略**：
- **索引时** `ik_max_word`：最大切分，高召回率（"心血管科"→"心血管/心血/血管/心/血/管/科"）
- **搜索时** `ik_smart`：粗粒度切分，高精度（"心血管科"→"心血管/科"）

### 7.2 查询构建

**文件**: `backend/app/search/repository.py`

```python
async def search(self, keyword: str, search_type: str = "all"):
    # 1. 确定目标索引
    indices = TYPE_INDEX_MAP.get(search_type, list(TYPE_INDEX_MAP.values()))

    # 2. 合并搜索字段（带权重）
    fields = []
    for t in (search_type if search_type != "all" else TYPE_INDEX_MAP):
        fields.extend(TYPE_FIELDS_MAP[t])
    # hospital: ["hospital_name^3", "address"]
    # doctor: ["doctor_name^3", "specialty^2", "dept_name", ...]

    # 3. multi_match + best_fields 查询
    body = {
        "query": {
            "multi_match": {
                "query": keyword,
                "fields": fields,
                "type": "best_fields",  # 每文档取最佳匹配字段分数
            }
        },
        "size": 20,
    }
    resp = await self.es.search(index=",".join(indices), body=body)

    # 4. 归一化结果
    return [_hit_to_result(hit) for hit in resp["hits"]["hits"]]
```

### 7.3 全量同步

**文件**: `backend/app/search/sync/service.py`

```python
async def full_sync_all(self):
    # 1. 删除旧索引 + 重建
    for index_name in INDEX_MAPPINGS:
        await self.es.indices.delete(index=index_name, ignore=[404])
        await self.es.indices.create(index=index_name, body=INDEX_MAPPINGS[index_name])

    # 2. 从DB查询数据 + bulk写入
    hospitals = await self._get_hospital_docs()
    await self._bulk_index("yft_hospital", hospitals)

    departments = await self._get_department_docs()  # JOIN医院名
    await self._bulk_index("yft_department", departments)

    doctors = await self._get_doctor_docs()  # JOIN科室名+医院名
    await self._bulk_index("yft_doctor", doctors)

    symptoms = self._get_symptom_docs()  # 从SYMPTOM_MAP直接生成
    await self._bulk_index("yft_symptom", symptoms)

    # 3. refresh确保立即可搜
    await self.es.indices.refresh(index="yft_*")
```

---

## 八、JWT 认证与鉴权

### 8.1 Token 生成

**文件**: `backend/app/auth/utils.py`

```python
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
```

### 8.2 依赖注入鉴权

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException()
    user = await db.get(UserModel, int(user_id))
    if not user:
        raise UnauthorizedException()
    return user

async def require_admin(current_user: UserModel = Depends(get_current_user)):
    if current_user.user_type != 3:
        raise ForbiddenException("需要管理员权限")
    return current_user
```

### 8.3 使用方式

```python
# 需要登录
@router.get("/me")
async def get_me(current_user: UserModel = Depends(get_current_user)): ...

# 需要管理员
@router.post("/admin/xxx")
async def admin_action(admin: UserModel = Depends(require_admin)): ...
```

---

## 九、全局异常处理

### 9.1 异常类层次

**文件**: `backend/app/exception/base.py`

```python
class AppException(Exception):
    def __init__(self, code: int = 400, message: str = "错误", status_code: int = None):
        self.code = code
        self.message = message
        self.status_code = status_code if (100 <= (status_code or 0) <= 599) else 400

class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message, status_code=404)

class UnauthorizedException(AppException):
    def __init__(self, message: str = "未登录或Token已过期"):
        super().__init__(code=401, message=message, status_code=401)

class ForbiddenException(AppException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(code=403, message=message, status_code=403)

class BadRequestException(AppException):
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(code=400, message=message, status_code=400)

class ConflictException(AppException):
    def __init__(self, message: str = "数据冲突"):
        super().__init__(code=409, message=message, status_code=409)
```

### 9.2 全局处理器

**文件**: `backend/app/exception/handler.py`

```python
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"[{request.state.request_id}] {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"[{request.state.request_id}] 未处理异常")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},  # 隐藏真实错误
    )
```

---

## 十、前端架构详解

### 10.1 HTTP 客户端配置

**文件**: `frontend/src/api/index.ts`

```typescript
const api = axios.create({
  baseURL: '/api',
  timeout: 60000,  // 60秒，适配Dify AI长链路
})

// 请求拦截器：注入Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body.code !== 200 && body.code !== 0) {
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(body)
    }
    return body
  },
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
    }
    ElMessage.error(err.response?.data?.message || '网络错误')
    return Promise.reject(err)
  }
)
```

### 10.2 路由守卫

**文件**: `frontend/src/router/index.ts`

```typescript
router.beforeEach((to, from, next) => {
  document.title = (to.meta.title as string) || '银发通'
  const token = localStorage.getItem('token')

  if (to.meta.guest) {
    // 登录/注册页：已登录则跳首页
    token ? next('/home') : next()
  } else if (!token) {
    // 非guest页：无Token跳登录
    next('/login')
  } else if (to.meta.admin && localStorage.getItem('user_type') !== '3') {
    // 管理员页面：非管理员跳首页
    next('/home')
  } else {
    next()
  }
})
```

### 10.3 Pinia 状态管理

**App Store** — 长者/子女模式切换：

```typescript
export const useAppStore = defineStore('app', () => {
  const mode = ref<'elder' | 'normal'>(
    (localStorage.getItem('app_mode') as 'elder' | 'normal') || 'normal'
  )
  const isElderMode = computed(() => mode.value === 'elder')

  function toggleMode() {
    mode.value = mode.value === 'elder' ? 'normal' : 'elder'
    localStorage.setItem('app_mode', mode.value)
  }
  return { mode, isElderMode, toggleMode }
})
```

**User Store** — 用户认证状态：

```typescript
export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const info = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => info.value?.user_type === 3)

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    token.value = res.data.token
    localStorage.setItem('token', res.data.token)
    await fetchMe()
  }

  function logout() {
    token.value = ''
    info.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user_type')
    router.push('/login')
  }

  return { token, info, isLoggedIn, isAdmin, login, logout, fetchMe }
})
```

### 10.4 组合式函数

**useRequest** — 通用异步请求封装：

```typescript
export function useRequest<T>(fn: () => Promise<any>) {
  const loading = ref(false)
  const data = ref<T | null>(null)
  const error = ref<string | null>(null)

  async function run() {
    loading.value = true
    error.value = null
    try {
      const res = await fn()
      data.value = res.data?.data ?? res.data
    } catch (e: any) {
      error.value = e.message || '请求失败'
    } finally {
      loading.value = false
    }
  }

  return { loading, data, error, run }
}
```

---

## 十一、支付宝沙箱支付技术实现

### 11.1 客户端初始化

**文件**: `backend/app/payment/service.py`

```python
def _get_alipay_client():
    global _alipay_client
    if _alipay_client is None:
        _alipay_client = DefaultAlipayClient(
            settings.ALIPAY_GATEWAY,
            settings.ALIPAY_APP_ID,
            _format_private_key(settings.ALIPAY_PRIVATE_KEY),  # 支持3种格式
            alipay_public_key=_format_public_key(settings.ALIPAY_PUBLIC_KEY),
        )
    return _alipay_client
```

### 11.2 私钥格式处理

```python
def _format_private_key(key: str) -> str:
    """支持裸base64、PKCS#8 PEM、PKCS#1 PEM三种格式"""
    key = key.strip()
    if key.startswith("-----"):
        if "BEGIN PRIVATE KEY" in key:
            # PKCS#8 → PKCS#1：去掉头部，提取base64
            b64 = key.replace("-----BEGIN PRIVATE KEY-----", "")...
            der = base64.b64decode(b64)
            # 提取RSA私钥DER子串
            return f"-----BEGIN RSA PRIVATE KEY-----\n{...}\n-----END RSA PRIVATE KEY-----"
        return key  # 已经是PKCS#1
    # 裸base64 → 加PKCS#1头部
    return f"-----BEGIN RSA PRIVATE KEY-----\n{key}\n-----END RSA PRIVATE KEY-----"
```

### 11.3 创建支付请求

```python
async def create_payment(self, user_id: int, reserve_id: int):
    # ...校验逻辑...

    if settings.PAY_MODE == "sandbox":
        request = AlipayTradePagePayRequest()
        request.notify_url = settings.ALIPAY_NOTIFY_URL
        request.return_url = settings.ALIPAY_RETURN_URL
        request.biz_content = {
            "out_trade_no": out_trade_no,
            "total_amount": str(pay_money),
            "subject": f"银发通挂号-{out_trade_no}",
            "product_code": "FAST_INSTANT_TRADE_PAY",
            "timeout_express": "15m",
        }
        client = _get_alipay_client()
        response = client.page_execute(request, method="GET")
        return {"pay_url": response, "out_trade_no": out_trade_no}
```

### 11.4 异步回调验签

```python
async def handle_alipay_notify(self, form_data: dict) -> str:
    if settings.PAY_MODE == "mock":
        return "success"

    # RSA2验签
    sign = form_data.get("sign", "")
    sign_str = "&".join(f"{k}={form_data[k]}" for k in sorted(form_data) if k not in ("sign", "sign_type"))
    public_key_pem = _format_public_key(settings.ALIPAY_PUBLIC_KEY)
    is_valid = verify_with_rsa(
        public_key_pem.encode(),
        sign_str.encode(),
        sign.encode() if isinstance(sign, str) else sign,
    )
    if not is_valid:
        return "failure"

    # 幂等处理：WHERE pay_status=1 防并发
    trade_status = form_data.get("trade_status")
    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        await self.repo.mark_paid(out_trade_no, trade_no)  # UPDATE SET pay_status=2 WHERE pay_status=1
        await self._complete_payment(reserve_id)
```

---

## 十二、Dify AI 集成技术实现

### 12.1 Dify 客户端

**文件**: `backend/app/shared/dify_client.py`

```python
class DifyClient:
    def __init__(self):
        self._client: httpx.AsyncClient = None
        self._api_key = settings.DIFY_API_KEY
        self._base_url = settings.DIFY_BASE_URL

    async def start(self):
        self._client = httpx.AsyncClient(timeout=60.0)  # 60秒超时

    async def chat(self, query: str, conversation_id: str = "") -> str:
        resp = await self._client.post(
            f"{self._base_url}/chat-messages",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "inputs": {},
                "query": query,
                "response_mode": "blocking",
                "conversation_id": conversation_id,
                "user": "yft-system",
            },
        )
        resp.raise_for_status()
        return resp.json()["answer"]
```

### 12.2 AI响应解析

```python
async def _diagnose_with_dify(self, symptom_text: str) -> GuideResponse:
    raw_answer = await dify_client.chat(query=symptom_text)

    # 提取JSON：支持 ```json...``` 和裸 {  } 两种格式
    if "```json" in raw_answer:
        json_str = raw_answer.split("```json")[1].split("```")[0].strip()
    else:
        start = raw_answer.find("{")
        end = raw_answer.rfind("}") + 1
        json_str = raw_answer[start:end]

    data = json.loads(json_str)
    # 构建返回结果
    departments = data.get("departments", [])[:3]
    medications = data.get("medications", [])[:3]
    ...
```

---

## 十三、定时任务与数据一致性

### 13.1 APScheduler 调度器

**文件**: `backend/app/shared/scheduler.py`

```python
def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(expire_orders, "cron", hour=2, minute=0)     # 凌晨2点
    scheduler.add_job(reconcile_source, "cron", minute=0)          # 每小时整点
    scheduler.start()

async def expire_orders():
    """批量更新过期订单：已预约(2) → 已就诊(3)"""
    async with async_session_factory() as session:
        today = date.today()
        await session.execute(
            update(ReserveModel)
            .where(ReserveModel.order_status == 2, ...)
            .values(order_status=3, queue_status=3)
        )
        await session.commit()

async def reconcile_source():
    """号源对账：以MySQL为准修复Redis"""
    async with async_session_factory() as session:
        schedules = await session.execute(select(ScheduleModel)...)
        for schedule in schedules:
            # 计算MySQL中有效预约数
            used = await count_valid_reserves(session, schedule.id)
            # 计算Redis中剩余量
            redis_normal = await redis_client.get(f"source:{schedule.id}:normal")
            # 修复：剩余 = 总量 - 已用
            correct = schedule.normal_num - used
            if int(redis_normal or 0) != correct:
                await redis_client.set(f"source:{schedule.id}:normal", correct)
```

### 13.2 号源一致性保障三层机制

```
┌──────────────────────────────────────────┐
│ 第1层：Redis Lua 原子操作（实时扣减）     │  防并发超卖
├──────────────────────────────────────────┤
│ 第2层：RabbitMQ 延时消息（15分钟超时）    │  防支付超时不释放
├──────────────────────────────────────────┤
│ 第3层：APScheduler 定时对账（每小时）     │  修复极端情况数据不一致
└──────────────────────────────────────────┘
```

---

## 十四、部署架构

### 14.1 Docker Compose 编排

```yaml
services:
  mysql:         # MySQL 8.0 - 持久化存储
  redis:         # Redis 7 - 缓存/队列/锁
  rabbitmq:      # RabbitMQ 3 - 消息队列（含x-delayed-message插件）
  elasticsearch: # ES 8 - 全文搜索（含IK分词器）
  backend:       # FastAPI + Uvicorn - 后端API
  frontend:      # Nginx + Vue3 SPA - 前端静态资源
```

### 14.2 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name 118.31.120.180;
    client_max_body_size 20M;

    # 前端静态资源
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_read_timeout 120s;  # 适配AI长链路
    }

    # 上传文件代理
    location /uploads/ {
        proxy_pass http://backend:8000;
    }
}
```

### 14.3 服务依赖链

```
frontend → backend → mysql
                   → redis
                   → rabbitmq
                   → elasticsearch
                   → dify (外部)
                   → alipay (外部)
```

---

## 十五、安全设计总结

| 安全维度 | 实现方案 |
|----------|----------|
| 密码存储 | bcrypt 单向哈希 |
| 接口认证 | JWT (HS256, 24h有效期) |
| 权限控制 | user_type三级 + require_admin依赖 |
| SQL注入 | SQLAlchemy ORM参数化查询 |
| XSS防护 | 前端Vue模板自动转义 |
| CORS | 仅允许配置的域名 |
| 支付验签 | RSA2签名验证（fail-closed） |
| 数据删除 | 全局软删除，不物理删除 |
| 异常信息 | 500错误隐藏真实信息，防止泄露 |
| 配置安全 | 生产环境JWT_SECRET_KEY必须修改，否则拒绝启动 |
| 预约防重 | Redis SET NX + TTL |
| 并发控制 | Lua原子脚本 + SQL WHERE条件 |
