# 支付宝扫码登录 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 把登录页的"模拟微信登录"替换为真实的支付宝 OAuth2.0 扫码登录

**架构：** 前端点击支付宝登录 → 跳转支付宝授权页 → 用户扫码授权 → 支付宝回调带回 `auth_code` → 前端提取 `auth_code` 调后端 → 后端用 `auth_code` 换取 `access_token` + `user_id` → 查库匹配或自动创建用户 → 返回 JWT

**技术栈：** Vue3 + FastAPI + alipay-sdk-python（已有） + MySQL

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/auth/models.py:20` | 修改 | 新增 `alipay_user_id` 字段 |
| `backend/app/alembic/versions/xxxx_add_alipay_user_id.py` | 创建 | 数据库迁移 |
| `backend/app/config.py:70` | 修改 | 新增 `ALIPAY_OAUTH_REDIRECT_URI` |
| `backend/app/auth/schemas.py` | 修改 | 新增 `AlipayLoginRequest` |
| `backend/app/auth/repository.py` | 修改 | 新增 `get_user_by_alipay_user_id()` |
| `backend/app/auth/service.py` | 修改 | 新增 `alipay_login()` 业务逻辑 |
| `backend/app/auth/router.py` | 修改 | 新增 `POST /api/auth/alipay-login` 端点 |
| `frontend/src/types/index.ts` | 修改 | 新增 `AlipayLoginRequest` 类型 |
| `frontend/src/api/auth.ts` | 修改 | 新增 `alipayLogin()` 方法 |
| `frontend/src/router/index.ts` | 修改 | 新增 `/auth/callback` 路由 |
| `frontend/src/views/login/AuthCallback.vue` | 创建 | 支付宝回调处理页 |
| `frontend/src/views/login/LoginView.vue` | 修改 | 替换微信按钮为支付宝按钮 |
| `frontend/src/stores/user.ts` | 修改 | 新增 `alipayLogin()` action |

---

## 任务 1：UserModel 新增 alipay_user_id 字段

**文件：**
- 修改：`backend/app/auth/models.py:20`
- 创建：`backend/app/alembic/versions/c1d2e3f4a5b6_add_alipay_user_id.py`

- [ ] **步骤 1：在 UserModel 添加字段**

```python
# backend/app/auth/models.py，在 wx_openid 字段后添加
alipay_user_id: Mapped[str | None] = mapped_column(
    String(128), unique=True, nullable=True, comment="支付宝用户唯一标识"
)
```

- [ ] **步骤 2：创建 Alembic 迁移**

```bash
cd backend && alembic revision --autogenerate -m "add alipay_user_id to tb_user"
```

生成的迁移文件应包含：
```python
def upgrade() -> None:
    op.add_column('tb_user', sa.Column('alipay_user_id', sa.String(length=128), nullable=True, comment='支付宝用户唯一标识'))
    op.create_unique_constraint('uq_tb_user_alipay_user_id', 'tb_user', ['alipay_user_id'])

def downgrade() -> None:
    op.drop_constraint('uq_tb_user_alipay_user_id', 'tb_user', type_='unique')
    op.drop_column('tb_user', 'alipay_user_id')
```

- [ ] **步骤 3：执行迁移验证**

```bash
cd backend && alembic upgrade head
```

预期：迁移成功，`tb_user` 表新增 `alipay_user_id` 列

---

## 任务 2：Config + Schema + Repository

**文件：**
- 修改：`backend/app/config.py:70`
- 修改：`backend/app/auth/schemas.py`
- 修改：`backend/app/auth/repository.py`

- [ ] **步骤 1：config.py 添加 OAuth 回调地址**

```python
# backend/app/config.py，在 ALIPAY_RETURN_URL 后添加
ALIPAY_OAUTH_REDIRECT_URI: str = "http://localhost:5173/auth/callback"
```

- [ ] **步骤 2：schemas.py 添加请求模型**

```python
# backend/app/auth/schemas.py
class AlipayLoginRequest(BaseModel):
    auth_code: str = Field(description="支付宝授权码")
```

- [ ] **步骤 3：repository.py 添加查询函数**

```python
# backend/app/auth/repository.py
async def get_user_by_alipay_user_id(session: AsyncSession, alipay_user_id: str) -> UserModel | None:
    result = await session.execute(
        select(UserModel).where(UserModel.alipay_user_id == alipay_user_id)
    )
    return result.scalar_one_or_none()
```

---

## 任务 3：Service 层支付宝登录逻辑

**文件：**
- 修改：`backend/app/auth/service.py`

- [ ] **步骤 1：实现 alipay_login 函数**

```python
# backend/app/auth/service.py
from app.auth.repository import get_user_by_alipay_user_id

async def alipay_login(session: AsyncSession, auth_code: str) -> TokenResponse:
    """
    支付宝 OAuth 登录流程：
    1. 用 auth_code 换取 access_token + user_id
    2. 用 access_token 获取用户信息（昵称等）
    3. 按 alipay_user_id 查库：找到则登录，未找到则自动注册
    """
    from alipay.aop.api.AlipayClientFactory import AlipayClientFactory
    from alipay.aop.api.domain.AlipaySystemOauthTokenRequest import AlipaySystemOauthTokenRequest
    from alipay.aop.api.domain.AlipayUserInfoShareRequest import AlipayUserInfoShareRequest
    from app.config import settings

    # 初始化客户端（复用 payment 的配置）
    factory = AlipayClientFactory(
        alipay_public_key=settings.ALIPAY_PUBLIC_KEY,
        app_private_key=settings.ALIPAY_PRIVATE_KEY,
        app_id=settings.ALIPAY_APP_ID,
        sign_type="RSA2",
    )
    client = factory.get_client()
    client.server_url = settings.ALIPAY_GATEWAY

    # Step 1: auth_code 换 token
    token_req = AlipaySystemOauthTokenRequest()
    token_req.grant_type = "authorization_code"
    token_req.code = auth_code
    token_resp = client.execute(token_req)

    if not token_resp or token_resp.get("code") != "10000":
        msg = token_resp.get("msg", "未知错误") if token_resp else "支付宝服务无响应"
        raise BadRequestException(f"支付宝授权失败: {msg}")

    alipay_user_id = token_resp.get("user_id")
    access_token = token_resp.get("access_token")

    if not alipay_user_id:
        raise BadRequestException("支付宝未返回用户标识")

    # Step 2: 获取用户信息
    nickname = "支付宝用户"
    try:
        info_req = AlipayUserInfoShareRequest()
        info_req.auth_token = access_token
        info_resp = client.execute(info_req)
        if info_resp and info_resp.get("code") == "10000":
            user_name = info_resp.get("user_name")
            if user_name:
                nickname = user_name
    except Exception:
        pass  # 获取昵称失败不阻断登录

    # Step 3: 查库或创建
    user = await get_user_by_alipay_user_id(session, alipay_user_id)
    if not user:
        user = UserModel(
            alipay_user_id=alipay_user_id,
            nickname=nickname,
            user_type=1,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)

    # 签发 JWT
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        nickname=user.nickname,
        user_type=user.user_type,
    )
```

- [ ] **步骤 2：在 router.py 添加端点**

```python
# backend/app/auth/router.py
@router.post("/alipay-login", response_model=ApiResponse[TokenResponse])
async def alipay_login(
    req: AlipayLoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """支付宝 OAuth 扫码登录"""
    data = await service.alipay_login(session, req.auth_code)
    return ApiResponse.ok(data)
```

记得在文件顶部 import `AlipayLoginRequest`。

---

## 任务 4：前端类型 + API + Store

**文件：**
- 修改：`frontend/src/types/index.ts`
- 修改：`frontend/src/api/auth.ts`
- 修改：`frontend/src/stores/user.ts`

- [ ] **步骤 1：types/index.ts 添加类型**

```typescript
// frontend/src/types/index.ts
export interface AlipayLoginRequest { auth_code: string }
```

- [ ] **步骤 2：api/auth.ts 添加方法**

```typescript
// frontend/src/api/auth.ts
alipayLogin: (auth_code: string) =>
  http.post<ApiResponse<TokenResponse>>('/auth/alipay-login', { auth_code }),
```

- [ ] **步骤 3：stores/user.ts 添加 action**

```typescript
// frontend/src/stores/user.ts
async function alipayLogin(authCode: string) {
  const r = await authApi.alipayLogin(authCode)
  if (r.data?.code === 200 && r.data.data) {
    const d = r.data.data
    token.value = d.access_token
    localStorage.setItem('token', d.access_token)
    localStorage.setItem('user_type', String(d.user_type))
    await fetchMe()
  }
  return r
}
```

确保 `authApi` 在文件顶部被 import，并在 return 中导出 `alipayLogin`。

---

## 任务 5：前端回调页 + 路由

**文件：**
- 创建：`frontend/src/views/login/AuthCallback.vue`
- 修改：`frontend/src/router/index.ts`

- [ ] **步骤 1：创建 AuthCallback.vue**

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  const authCode = route.query.auth_code as string
  if (!authCode) {
    ElMessage.error('支付宝授权失败：未收到授权码')
    return router.replace('/login')
  }
  try {
    await userStore.alipayLogin(authCode)
    ElMessage.success('登录成功')
    router.replace('/home')
  } catch {
    ElMessage.error('支付宝登录失败，请重试')
    router.replace('/login')
  }
})
</script>

<template>
  <div class="callback-wrap">
    <div class="callback-card">
      <div class="spinner"></div>
      <p>正在完成支付宝登录...</p>
    </div>
  </div>
</template>

<style scoped>
.callback-wrap { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: var(--c-bg); }
.callback-card { text-align: center; padding: 40px; }
.callback-card p { margin-top: 16px; font-size: 16px; color: var(--c-ink-700); }
.spinner { width: 40px; height: 40px; margin: 0 auto; border: 4px solid var(--c-ink-100); border-top-color: var(--c-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
```

- [ ] **步骤 2：router/index.ts 添加路由**

```typescript
// 在 login 路由后面添加
{
  path: '/auth/callback',
  name: 'AuthCallback',
  component: () => import('@/views/login/AuthCallback.vue'),
  meta: { title: '支付宝登录', guest: true },
},
```

---

## 任务 6：替换登录页微信按钮为支付宝按钮

**文件：**
- 修改：`frontend/src/views/login/LoginView.vue:100-103`

- [ ] **步骤 1：替换按钮代码**

将：
```html
<el-divider>其他方式</el-divider>
<button class="btn-wx" @click="ElMessage.info('模拟微信授权登录成功')">
  💬 微信一键登录
</button>
```

替换为：
```html
<el-divider>其他方式</el-divider>
<button class="btn-alipay" @click="goAlipayLogin">
  支付宝扫码登录
</button>
```

- [ ] **步骤 2：添加 goAlipayLogin 方法**

在 `<script setup>` 中添加：

```typescript
import { useUserStore } from '@/stores/user'
import { settings } from '@/config'  // 或直接硬编码

const ALIPAY_OAUTH_URL = 'https://openauth.alipay.com/oauth2/publicAppAuthorize.htm'
const ALIPAY_APP_ID = '9021000164696230'  // 与后端 config 一致
const ALIPAY_REDIRECT_URI = encodeURIComponent(window.location.origin + '/auth/callback')

function goAlipayLogin() {
  const url = `${ALIPAY_OAUTH_URL}?app_id=${ALIPAY_APP_ID}&scope=auth_user&redirect_uri=${ALIPAY_REDIRECT_URI}`
  window.location.href = url
}
```

- [ ] **步骤 3：替换样式**

将 `.btn-wx` 样式替换为：

```css
.btn-alipay {
  width: 100%; height: 52px; border: none; border-radius: var(--r-pill);
  background: #1677FF; color: #fff; font-size: 17px; font-weight: 700;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: .2s;
}
.btn-alipay:hover { background: #4096ff; }
```

---

## 任务 7：编译验证 + 端到端测试

- [ ] **步骤 1：后端迁移验证**

```bash
docker compose exec backend alembic upgrade head
```

预期：迁移成功

- [ ] **步骤 2：前端类型检查 + 构建**

```bash
cd frontend && npx vue-tsc --noEmit && npx vite build
```

预期：零错误

- [ ] **步骤 3：重建后端**

```bash
docker compose up -d --build backend
```

- [ ] **步骤 4：端到端测试**

1. 打开登录页，确认"支付宝扫码登录"按钮显示（蓝色，支付宝蓝 #1677FF）
2. 点击按钮 → 跳转到支付宝沙箱授权页
3. 在沙箱页扫码/确认授权 → 回调到 `/auth/callback?auth_code=xxx`
4. 页面显示"正在完成支付宝登录..." → 自动跳转首页
5. 确认用户已登录（顶部显示昵称）

---

## 自检

1. **规格覆盖度：** ✅ 登录页微信按钮替换 → 支付宝按钮；OAuth 全流程（前端跳转 → 后端换码 → 自动注册 → JWT）；回调页处理
2. **占位符扫描：** ✅ 所有步骤包含完整代码
3. **类型一致性：** ✅ `AlipayLoginRequest.auth_code` 前后端一致；`TokenResponse` 复用已有

---

## 前置条件

> **重要：** 支付宝 OAuth 登录需要在[支付宝开放平台](https://open.alipay.com)完成以下配置：
> 1. 应用需开通"第三方应用"功能
> 2. 功能列表中添加 `alipay.system.oauth.token` 和 `alipay.user.info.share`
> 3. 授权回调地址设置为 `http://localhost:5173/auth/callback`（开发环境）
> 4. 沙箱环境下，同一 APP_ID 通常已支持 OAuth，但需在沙箱工具中确认
