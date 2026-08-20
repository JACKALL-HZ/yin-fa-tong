# 银发通 · 老年人智慧健康服务平台

面向老年人的智慧健康服务系统，核心功能为 **AI 智能导诊**（LangGraph 工作流 + RAG 检索增强），同时覆盖陪诊预约、用药提醒、在线挂号、健康报告、消息通知等老年健康场景。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| 前端 | Vue 3 + Vite 5 + Element Plus |
| 数据库 | MySQL 8 + Redis 7 |
| 消息队列 | RabbitMQ 3 |
| 搜索引擎 | Elasticsearch 8（含 IK 中文分词） |
| 导诊引擎 | LangGraph 状态图 + Chroma 向量库 + BGE-M3 embedding + BM25 + Reranker |
| LLM | 通义千问 qwen-plus（OpenAI 兼容接口） |
| 部署 | Docker Compose 一键编排 |

## 导诊架构（LangGraph）

```
START → extract(症状提取+LLM) → triage(紧急分级·纯规则)
                                    │
                          ┌─────────┴──────────┐
                       red 短路                  green/yellow
                          │                        │
                    assemble(只给120)    retrieve → recommend → medication → assemble
                                                    ↑ RAG检索    ↑ 科室推荐    ↑ 用药参考    ↑ 结果组装
```

- **triage 紧急分级**是合规红线：red 级只给"120/立即就医"建议，不提供诊断和用药
- **RAG 检索**：Chroma 语义检索 + BM25 关键词检索 → RRF 融合 → Reranker 精排
- **降级机制**：LLM 不可用时自动降级到词库匹配，链路不中断
- **断点续推**：AsyncSqliteSaver Checkpointer，支持中断后恢复

## 快速启动

### 前置条件

- Docker Desktop 已启动
- 根目录 `.env` 文件已配置（见下方环境变量）

### 一键启动

```bash
cd yin-fa-tong
docker compose up -d
```

启动后访问 `http://localhost:80`。

### 常用命令

```bash
docker compose up -d              # 启动全部服务
docker compose ps                 # 查看服务状态（等 backend 变 healthy）
docker compose logs -f backend    # 查看后端实时日志
docker compose down               # 停止全部服务（数据卷保留）
docker compose up -d --build      # 改了代码后重新构建并启动
docker compose down -v            # 停止并清空数据卷（⚠️ 丢库）
```

## 环境变量

在项目根目录创建 `.env` 文件（**不进仓库**，已 gitignore）：

```env
# 数据库
DB_PASSWORD=root123
DB_NAME=yinfa_tong

# LangGraph 导诊 - LLM（通义千问）
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=你的千问key
LLM_MODEL=qwen-plus

# LangGraph 导诊 - Embedding（硅基流动 BGE-M3 API）
EMBEDDING_PROVIDER=api
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIM=1024
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=你的硅基流动key
```

## 目录结构

```
yin-fa-tong/
├── backend/
│   ├── app/
│   │   ├── guide/              # 导诊模块（LangGraph 工作流）
│   │   │   ├── graph/          # 图构建 + 6 节点 + 条件边路由
│   │   │   ├── symptom_dict/    # 症状词典 + 紧急分级规则
│   │   │   ├── router.py        # 导诊 API（含 SSE 流式）
│   │   │   ├── service.py       # 引擎分派（langgraph/rule）+ 降级
│   │   │   └── models.py        # 导诊结果数据模型
│   │   ├── shared/              # 共享组件
│   │   │   ├── embedding.py     # embedding 选择器（local/api）
│   │   │   ├── vector_store.py  # Chroma + BM25 + RRF + Reranker
│   │   │   └── llm.py           # LLM 客户端
│   │   ├── auth/  hospital/  doctor/  department/
│   │   ├── accompany/  reminder/  report/  payment/  message/
│   │   ├── config.py            # 配置（环境变量驱动）
│   │   └── main.py              # FastAPI 入口
│   ├── alembic/                 # 数据库迁移
│   ├── Dockerfile
│   └── requirements-server.txt  # 瘦镜像依赖（无 torch/FlagEmbedding）
├── frontend/
│   ├── src/
│   │   ├── views/guide/         # 导诊页面（SSE 流式 + AI 分析卡片）
│   │   ├── api/                 # 接口封装
│   │   └── types/
│   ├── Dockerfile               # 多阶段构建（node build → nginx serve）
│   └── package.json
├── docker/                      # ES/RabbitMQ 自定义镜像
├── docker-compose.yml           # 服务编排
└── .env                         # 环境变量（不入仓库）
```

## 测试账号

| 账号 | 密码 | 身份 |
|------|------|------|
| `admin_yft` | 123456 | 管理员 |
| `testuser1` | 123456 | 普通用户 |

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend (Nginx) | **80** | 浏览器访问入口，反代后端 API |
| backend (FastAPI) | 8000 | 仅容器内部，经 Nginx 代理 |
| mysql | 3307→3306 | 本地开发可通过 Navicat 连 3307 |
| redis | 6379 | 容器内部 |
| rabbitmq | 5672 / 15672 | AMQP / 管理界面 |
| elasticsearch | 9200 | REST API |
