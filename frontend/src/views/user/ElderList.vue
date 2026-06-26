<script setup lang="ts">
import { ref } from 'vue'
import { userApi } from '@/api/user'
import type { TodoItem, AlertItem } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ElderBind } from '@/types'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

const elders = ref<ElderBind[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref<{ elder_name: string; elder_phone: string; elder_id_card: string; gender: number; birthday: string | null; medical_card: string }>({ elder_name: '', elder_phone: '', elder_id_card: '', gender: 1, birthday: null, medical_card: '' })
const submitting = ref(false)
const editingId = ref(0)

const todos = ref<TodoItem[]>([])
const alerts = ref<AlertItem[]>([])
const remindersLoading = ref(false)

async function load() {
  loading.value = true
  try { const r = await userApi.listElders(); elders.value = r.data.data || [] }
  finally { loading.value = false }
}
function openAdd() {
  isEdit.value = false; editingId.value = 0
  form.value = { elder_name: '', elder_phone: '', elder_id_card: '', gender: 1, birthday: null, medical_card: '' }
  dialogVisible.value = true
}
function openEdit(e: ElderBind) {
  isEdit.value = true; editingId.value = e.id
  form.value = { elder_name: e.elder_name, elder_phone: e.elder_phone || '', elder_id_card: e.elder_id_card || '', gender: e.gender, birthday: e.birthday || null, medical_card: e.medical_card || '' }
  dialogVisible.value = true
}
async function handleDelete(id: number) {
  try { await ElMessageBox.confirm('确定移除该长辈？', '提示', { type: 'warning' }) } catch { return }
  try { await userApi.deleteElder(id); ElMessage.success('已移除'); load() }
  catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}
async function handleSubmit() {
  if (!form.value.elder_name || !form.value.elder_phone) return ElMessage.warning('请填写姓名和电话')
  submitting.value = true
  try {
    const payload: any = { ...form.value }
    if (!payload.medical_card) payload.medical_card = null
    if (!payload.birthday) payload.birthday = null
    if (isEdit.value) await userApi.updateElder(editingId.value, payload)
    else await userApi.createElder(payload)
    ElMessage.success(isEdit.value ? '已更新' : '已添加')
    dialogVisible.value = false
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '保存失败') }
  finally { submitting.value = false }
}

async function loadReminders() {
  remindersLoading.value = true
  try {
    const r = await userApi.getElderReminders()
    const data = r.data.data
    todos.value = data?.todos || []
    alerts.value = data?.alerts || []
  } catch { /* 静默失败 */ }
  finally { remindersLoading.value = false }
}

load()
loadReminders()
</script>

<template>
  <div class="page-wrap">
    <!-- Family Dashboard Hero -->
    <div class="family-hero dark-card-accent">
      <span class="watermark" style="right:30px;bottom:-30px;font-size:200px">家</span>
      <div class="grid-hero">
        <div>
          <span class="display" style="font-size:14px;color:var(--c-gold);display:block;margin-bottom:8px">Family Dashboard</span>
          <h1 class="serif" style="font-size:32px;font-weight:900;color:var(--c-cream)">爸妈今天都挺好的</h1>
          <p style="color:rgba(255,232,184,0.85);margin-top:8px">相隔千里，牵挂常在，多一份关心，少一份担忧</p>
          <div class="hero-summary">
            <div class="hsum"><span class="num" style="font-size:24px;color:var(--c-gold)">{{ elders.length }}</span><span>已绑定家人</span></div>
            <div class="hsum"><span class="num" style="font-size:24px;color:var(--c-rose)">{{ alerts.length }}</span><span>智能提醒</span></div>
          </div>
        </div>
        <div class="hero-overview" style="background:rgba(255,247,232,.06);border-radius:var(--r-lg);padding:20px">
          <div class="ov-item"><span class="num" style="font-size:28px;color:var(--c-gold)">{{ todos.length }}</span><span>待办任务</span></div>
          <div class="ov-item"><span class="num" style="font-size:28px;color:var(--c-rose)">{{ alerts.filter(a => a.title.includes('待支付') || a.title.includes('候诊')).length }}</span><span>需处理</span></div>
          <div class="ov-item"><span class="num" style="font-size:28px;color:var(--c-gold)">{{ alerts.filter(a => a.title.includes('提醒')).length }}</span><span>就诊提醒</span></div>
        </div>
      </div>
    </div>

    <!-- 家庭成员卡片 -->
    <section style="margin:32px 0">
      <div class="sec-head">
        <span class="sec-head-zh">亲情成员</span>
        <span class="sec-head-en">Family Members</span>
        <el-button :icon="Plus" type="primary" size="large" round @click="openAdd" style="margin-left:auto">添加长辈</el-button>
      </div>

      <div v-loading="loading">
        <div v-if="elders.length === 0 && !loading" class="empty-card card" style="text-align:center;padding:48px">
          <span style="font-size:48px">👨‍👩‍👧</span>
          <h3 class="serif" style="font-size:22px;margin:12px 0 8px">绑定父母信息</h3>
          <p style="color:var(--c-ink-500);margin-bottom:16px">绑定后可帮长辈挂号、缴费、查报告</p>
          <button class="btn-primary" @click="openAdd">+ 添加第一位家人</button>
        </div>

        <div class="family-grid">
          <div v-for="e in elders" :key="e.id" class="family-card card-hover">
            <div class="fam-av-lg">{{ e.elder_name?.charAt(0) || '长' }}</div>
            <div class="fam-info-lg">
              <span class="fam-name-lg">{{ e.elder_name }}</span>
              <span class="fam-rel-lg">{{ e.gender === 1 ? '男' : '女' }} · {{ e.age || '?' }}岁</span>
              <span class="fam-status-ok">● 状态良好</span>
            </div>
            <div class="fam-actions">
              <button class="fam-btn fam-btn-edit" @click="openEdit(e)">✏️ 编辑</button>
              <button class="fam-btn fam-btn-del" @click="handleDelete(e.id)">🗑️ 移除</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 健康提醒 -->
    <div class="grid-hero" style="margin-top:32px">
      <div class="card">
        <h3 class="widget-title serif">代办任务</h3>
        <div v-if="todos.length === 0 && !remindersLoading" style="text-align:center;padding:24px;color:var(--c-ink-500)">
          <span style="font-size:36px;display:block;margin-bottom:8px">🎉</span>
          暂无待办事项
        </div>
        <div class="todo-list">
          <div v-for="t in todos" :key="t.text" class="todo-item" :class="{urgent: t.urgent}">
            <span class="todo-icon">{{ t.icon }}</span>
            <div class="todo-body">
              <span class="todo-text">{{ t.text }}</span>
              <span class="todo-time">{{ t.time }}</span>
            </div>
            <span v-if="t.urgent" class="pill pill-rose" style="font-size:10px">紧急</span>
          </div>
        </div>
      </div>
      <div class="card" style="background:var(--c-accent);color:var(--c-cream);border:none">
        <h3 class="widget-title serif" style="color:var(--c-cream)">智能提醒</h3>
        <div v-if="alerts.length === 0 && !remindersLoading" style="text-align:center;padding:24px;opacity:.6">
          <span style="font-size:36px;display:block;margin-bottom:8px">🔔</span>
          暂无提醒
        </div>
        <div class="alert-list">
          <div v-for="a in alerts" :key="a.title + a.desc" class="alert-item">
            <span class="alert-icon">{{ a.icon }}</span>
            <div class="alert-body">
              <strong>{{ a.title }}</strong>
              <p>{{ a.desc }}</p>
              <span class="alert-time">{{ a.time }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑长辈' : '添加长辈'" width="90%">
      <el-form label-position="top" size="large">
        <el-form-item label="姓名"><el-input v-model="form.elder_name" placeholder="长辈姓名" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.elder_phone" placeholder="长辈手机号" /></el-form-item>
        <el-form-item label="身份证号"><el-input v-model="form.elder_id_card" placeholder="用于实名认证" /></el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender"><el-radio :value="1">男</el-radio><el-radio :value="2">女</el-radio></el-radio-group>
        </el-form-item>
        <el-form-item label="出生日期"><el-date-picker v-model="form.birthday" type="date" placeholder="选择日期" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="医保卡号"><el-input v-model="form.medical_card" placeholder="选填" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button size="large" @click="dialogVisible = false">取消</el-button>
        <el-button size="large" type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 1320px; margin: 0 auto; padding: 32px 32px 80px; }

/* Hero */
.family-hero { padding: 40px; border-radius: var(--r-xl); position: relative; margin-bottom: 8px; }
.hero-summary { display: flex; gap: 24px; margin-top: 20px; }
.hsum { display: flex; flex-direction: column; }
.hsum span:last-child { font-size: 12px; color: rgba(255,247,232,.55); }
.hero-overview { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.ov-item { text-align: center; padding: 12px; }
.ov-item span:last-child { display: block; font-size: 12px; color: rgba(255,247,232,.55); margin-top: 4px; }

/* Family Grid */
.family-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.family-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 24px 16px; background: var(--c-paper);
  border: 1px solid var(--c-line); border-radius: var(--r-lg);
  box-shadow: var(--shadow-1); text-align: center; gap: 10px;
}
.fam-av-lg {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, var(--c-accent), var(--c-accent-d));
  color: var(--c-cream); display: flex; align-items: center; justify-content: center;
  font-family: "Noto Serif SC", serif; font-size: 30px; font-weight: 900;
}
.fam-name-lg { font-size: 18px; font-weight: 800; display: block; }
.fam-rel-lg { font-size: 13px; color: var(--c-ink-500); }
.fam-status-ok { font-size: 12px; color: var(--c-accent); font-weight: 600; }
.fam-actions { display: flex; gap: 8px; margin-top: 4px; }
.fam-btn {
  padding: 6px 14px; border-radius: var(--r-pill);
  font-size: 12px; font-weight: 700; cursor: pointer;
  border: 1.5px solid; transition: all .2s;
}
.fam-btn-edit {
  background: var(--c-paper); color: var(--c-ink-700);
  border-color: var(--c-line-2);
}
.fam-btn-edit:hover { border-color: var(--c-primary); color: var(--c-primary); }
.fam-btn-del {
  background: var(--c-paper); color: var(--c-ink-500);
  border-color: var(--c-line);
}
.fam-btn-del:hover { border-color: var(--c-rose); color: var(--c-rose); background: #FBEFEC; }

/* 代办 */
.widget-title { font-size: 20px; font-weight: 900; margin-bottom: 18px; }
.todo-list { display: flex; flex-direction: column; gap: 10px; }
.todo-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px; border-radius: var(--r-md);
  border-left: 4px solid transparent;
}
.todo-item.urgent { background: var(--c-primary-bg); border-left-color: var(--c-primary); }
.todo-icon { font-size: 28px; flex-shrink: 0; }
.todo-body { flex: 1; }
.todo-text { font-size: 15px; font-weight: 700; color: var(--c-ink-900); display: block; }
.todo-time { font-size: 12px; color: var(--c-ink-500); }

.alert-list { display: flex; flex-direction: column; gap: 12px; }
.alert-item {
  display: flex; gap: 12px; padding: 14px;
  background: rgba(255,247,232,.06); border-radius: var(--r-md);
}
.alert-icon { font-size: 24px; flex-shrink: 0; }
.alert-body strong { font-size: 15px; display: block; }
.alert-body p { font-size: 12px; opacity: .7; margin: 2px 0; }
.alert-time { font-size: 10px; opacity: .5; }

.empty-card { border: 2px dashed var(--c-line-2) !important; }
</style>
