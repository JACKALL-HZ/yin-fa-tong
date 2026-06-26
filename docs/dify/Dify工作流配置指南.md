# 银发通 AI 智能导诊 — Dify Chatflow 配置指南

## 架构总览

采用 Dify **Chatflow（advanced-chat）** 模式，工作流结构：

```
[用户症状输入] → [医学知识库检索(RAG)] → [通义千问 AI分析] → [JSON解析校验] → [输出诊断结果]
   Start              Knowledge Retrieval           LLM (Qwen)           Code (Python)         Answer
```

对比之前的聊天助手模式，Chatflow 优势：

| 维度 | 聊天助手 (Chatbot) | Chatflow（本方案） |
|------|-------------------|--------------------|
| 配置方式 | 一个 Prompt + 知识库 | 可视化节点编排，流程可控 |
| 知识库检索 | 黑盒 RAG | 可调 Top-K、阈值、重排序 |
| 输出格式化 | 依赖 Prompt 约束 | Code 节点强制校验 JSON |
| 扩展性 | 难以加逻辑 | 可随时插入分支/并行节点 |
| 调试 | 只能看最终结果 | 每个节点可单独查看输出 |

---

## 第一步：上传知识库

### 1.1 创建知识库

Dify Cloud 左侧菜单 → **知识库** → **创建知识库**

| 配置项 | 值 |
|--------|-----|
| 名称 | `银发通-老年医学知识库` |
| 描述 | 银发通智慧就医平台医学知识库，涵盖16个科室的常见老年疾病、症状、用药信息 |
| 索引方式 | **高质量**（推荐） |
| 分段方式 | 自动分段与清洗 |

### 1.2 上传文档

进入知识库 → **添加文档** → 批量上传以下目录下所有 `.md` 文件：

```
docs/knowledge-base/
├── 01_心血管科/
│   ├── 高血压.md
│   └── 冠心病.md
├── 02_内分泌科/
│   └── 糖尿病.md
├── 03_神经内科/
│   └── 脑卒中.md
├── 04_呼吸科/
│   └── 慢性阻塞性肺病.md
├── 05_消化科/
│   └── 消化系统常见病.md
├── 06_骨科/
│   └── 老年骨关节病.md
├── 12_老年病科/
│   └── 老年综合征.md
└── 99_老年用药安全手册/
    ├── OTC药品清单.md
    ├── 老年人用药原则.md
    └── 常见药物相互作用.md
```

> **注意**：上传后等待向量化完成（状态变为"已完成"），再进行下一步。

---

## 第二步：导入 Chatflow DSL

### 2.1 导入工作流

Dify Cloud → **Studio** → **导入应用** → 选择文件：

```
docs/dify/银发通-AI智能导诊.yml
```

导入成功后会自动创建应用，包含 5 个节点：

| 节点 | 类型 | 说明 |
|------|------|------|
| 用户症状输入 | Start | 接收 `symptom_text` 文本输入 |
| 医学知识库检索 | Knowledge Retrieval | RAG 检索，Top-K=8，阈值 0.55 |
| AI导诊分析 | LLM (qwen-plus) | 通义千问分析症状 + 知识库内容，输出 JSON |
| JSON解析与校验 | Code (Python3) | 解析 LLM 输出，校验 JSON 完整性，兜底默认值 |
| 输出诊断结果 | Answer | 将 JSON 结果返回给调用方 |

### 2.2 绑定知识库

导入后，**医学知识库检索节点** 中的 `dataset_ids` 为空，需要手动绑定：

1. 点击 **医学知识库检索** 节点
2. 在右侧配置面板 → **知识库** → 选择 `银发通-老年医学知识库`
3. 确认以下参数（可在右侧面板调整）：

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 检索模式 | 混合检索 | 兼顾关键词匹配和语义理解 |
| Top-K | 8 | 返回最相关的 8 个文档片段 |
| 分数阈值 | 0.55 | 低于此分数的结果丢弃 |
| 重排序 | 开启 | 使用 Rerank 模型优化排序 |

### 2.3 确认 LLM 模型配置

点击 **AI导诊分析** 节点 → 确认模型配置：

| 配置项 | 值 |
|--------|-----|
| 模型提供商 | 通义千问 (Tongyi) |
| 模型名称 | qwen-plus |
| Temperature | 0.3 |
| 最大 Token | 2000 |
| 上下文 | `{{#医学知识库检索.result#}}`（自动绑定） |

### 2.4 配置建议问题（可选）

点击应用顶部 **功能** → 开启 **建议问题**，已预置 5 条老年常见症状问法：

- "我头疼、有点发烧，浑身没劲，应该挂什么科？"
- "膝盖疼了好几个月，走路都困难，有什么药可以缓解吗？"
- "最近总是胸闷气短、心跳快，是不是心脏有问题？"
- "晚上睡不着，白天头昏，血压也有点高，怎么办？"
- "吃完饭后胃胀、反酸，有时候还想吐，该看哪个科室？"

### 2.5 预览调试

右上角 **预览** → 输入症状测试，例如：

> "头疼三天，伴有发烧38度，浑身酸痛没力气"

查看各节点输出：
- **医学知识库检索** → 看检索到的文档片段是否相关
- **AI导诊分析** → 看 LLM 输出的 JSON 格式是否正确
- **JSON解析与校验** → 看最终输出的结构化结果

### 2.6 发布

点击右上角 **发布** → 确认发布。

---

## 第三步：配置后端

### 3.1 获取 API Key

Dify Cloud 左侧菜单 → **API 访问** → **创建密钥** → 复制 `app-xxxxxx`

### 3.2 写入 .env

编辑 `backend/.env`，添加以下配置：

```ini
# ── Dify AI Chatflow ──
DIFY_API_KEY=app-xxxxxx
DIFY_BASE_URL=https://api.dify.ai
DIFY_APP_MODE=chatflow
DIFY_TIMEOUT=30
DIFY_MAX_RETRIES=1
```

| 配置项 | 说明 |
|--------|------|
| `DIFY_API_KEY` | 从 API 访问页面获取的密钥 |
| `DIFY_BASE_URL` | Dify 服务地址（Cloud SaaS 默认 `https://api.dify.ai`） |
| `DIFY_APP_MODE` | `chatflow` = Chatflow/Advanced-Chat 模式；`chatbot` = 聊天助手模式 |
| `DIFY_TIMEOUT` | 单次 API 调用超时秒数 |
| `DIFY_MAX_RETRIES` | 超时后重试次数 |

### 3.3 重启后端

```bash
docker compose -p yft up -d --build backend
```

---

## 第四步：验证

### 4.1 API 测试

```bash
curl -X POST http://localhost:8000/api/guide/diagnose \
  -H "Content-Type: application/json" \
  -d '{"symptom_text":"头疼发烧浑身没劲"}'
```

期望返回（Dify 模式）：

```json
{
  "code": 200,
  "message": "导诊完成",
  "data": {
    "symptom_text": "头疼发烧浑身没劲",
    "results": [
      {
        "dept_name": "内科",
        "confidence": 0.85,
        "reasoning": "头疼、发热、乏力是典型的上呼吸道感染症状..."
      }
    ],
    "suggestion": "根据AI分析，建议优先挂【内科】（置信度 85%）...",
    "medications": [
      {
        "drug_name": "对乙酰氨基酚",
        "indication": "用于缓解轻至中度疼痛和退热",
        "dosage_note": "成人一次1片，一日不超过4次",
        "elderly_precaution": "老年患者应减量使用，每日不超过2g",
        "contraindication": "严重肝肾功能不全者禁用"
      }
    ],
    "elderly_precautions": "建议老年患者...",
    "emergency_flag": false,
    "general_advice": "多休息、多饮水...",
    "engine": "dify"
  }
}
```

### 4.2 降级验证

临时清空 `DIFY_API_KEY`（或故意写错），重启后端，API 应自动降级为规则引擎：

```json
{
  "engine": "rule",
  "results": [{"dept_name": "内科", ...}]
}
```

前端通过 `engine` 字段区分展示：
- `"dify"` → 显示 AI 分析标签、置信度、用药建议、老年注意事项
- `"rule"` → 仅显示科室推荐（基础关键词匹配）

---

## 降级策略

| 场景 | 行为 |
|------|------|
| `DIFY_API_KEY` 为空 | 跳过 Dify，直接使用本地规则引擎 |
| API 超时 (>30s) | 自动重试 1 次，仍失败则降级规则引擎 |
| HTTP 4xx（如 API Key 无效） | 立即抛出异常，降级规则引擎 |
| HTTP 5xx（服务端错误） | 重试 1 次，再失败降级规则引擎 |
| LLM 返回非标准 JSON | Code 节点的 `_extract_json_from_text()` 兜底 |
| LLM 返回字段缺失 | Code 节点用 `default` 字典补全所有字段 |
| 网络不可达 | 连接超时后降级 |

降级对用户透明——始终返回 200，通过 `engine` 字段告知前端实际使用的引擎。

---

## Debug 调试技巧

### 查看 Dify 侧日志

Dify Cloud → Studio → 应用 → **日志** → 筛选错误或查看具体调用：

- 每条日志显示节点耗时、Token 消耗
- 可点开 Knowledge Retrieval 节点看检索到的文档内容
- 可点开 LLM 节点看 Prompt 和 Response
- 可点开 Code 节点看输入输出

### 查看后端日志

```bash
docker compose -p yft logs backend --tail=50
```

关键日志行：
```
Dify 客户端已就绪 mode=chatflow base_url=https://api.dify.ai
Dify API 调用成功 mode=chatflow conversation_id=xxx
Dify 诊断失败，降级为规则引擎。错误: ...
```

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 导入 DSL 提示版本不兼容 | 本地 Dify 版本 < 0.6.0 | 升级 Dify 或使用聊天助手模式 |
| 知识库检索无结果 | `dataset_ids` 未绑定 | 点击节点 → 选择知识库 |
| LLM 无法访问知识库 | `context` 变量选择器未绑定 | 检查 LLM 节点上下文配置 |
| 返回 `engine: "rule"` | API Key 未配置或 Dify 不可达 | 检查 `.env` 中的 `DIFY_API_KEY` |
| Code 节点报错 | LLM 输出格式不标准 | 查看日志，调整 System Prompt |
