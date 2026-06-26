<script setup lang="ts">
import { ref } from 'vue'
import { reminderApi } from '@/api/reminder'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Reminder } from '@/types'

const list = ref<Reminder[]>([])
const loading = ref(false)
const showAdd = ref(false)
const form = ref({ remind_type: 'medicine', remind_time: '', remind_content: '' })

async function load() {
  loading.value = true
  try {
    const r = await reminderApi.list()
    list.value = r.data.data || []
  } finally {
    loading.value = false
  }
}

async function add() {
  if (!form.value.remind_time || !form.value.remind_content) return ElMessage.warning('请填写药品名和提醒时间')
  try {
    await reminderApi.create(form.value)
    ElMessage.success('提醒已创建')
    showAdd.value = false
    form.value = { remind_type: 'medicine', remind_time: '', remind_content: '' }
    load()
  } catch { /* 拦截器已提示 */ }
}

async function toggleItem(r: Reminder) {
  const old = r.is_active
  const newActive = old === 1 ? 0 : 1
  r.is_active = newActive
  try {
    await reminderApi.toggle(r.id, newActive)
    ElMessage.success(newActive ? '已启用' : '已停用')
  } catch {
    r.is_active = old
  }
}

async function deleteItem(r: Reminder) {
  try {
    await ElMessageBox.confirm('确定删除该提醒？', '提示', { type: 'warning' })
    await reminderApi.remove(r.id)
    ElMessage.success('已删除')
    load()
  } catch { /* 用户取消或拦截器已提示 */ }
}

load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">用药提醒</span>
      <span class="sec-head-en">Medication Reminders</span>
      <span class="sec-head-more">
        <el-button type="primary" size="large" @click="showAdd = true">+ 新建提醒</el-button>
      </span>
    </div>

    <div v-loading="loading">
      <div v-if="list.length === 0 && !loading" class="empty">暂无提醒，点击上方按钮创建</div>
      <div v-for="r in list" :key="r.id" class="reminder-card card-hover" :class="{ stopped: r.is_active === 0 }">
        <div class="r-top">
          <span class="pill" :class="r.is_active === 1 ? 'pill-green' : 'pill-grey'">
            {{ r.is_active === 1 ? '✅ 启用中' : '⏸ 已停用' }}
          </span>
          <span class="r-time">⏰ 每日 {{ r.remind_time }}</span>
        </div>
        <div class="r-content">💊 {{ r.remind_content }}</div>
        <div class="r-actions">
          <el-switch :model-value="r.is_active === 1" @change="toggleItem(r)" active-text="启用" inactive-text="停用" />
          <el-button type="danger" text size="small" @click="deleteItem(r)">删除</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="showAdd" title="新建用药提醒" width="90%">
      <el-form label-position="top" size="large">
        <el-form-item label="药品名称">
          <el-input v-model="form.remind_content" placeholder="如：阿托伐他汀 1片" />
        </el-form-item>
        <el-form-item label="每日提醒时间">
          <el-time-picker v-model="form.remind_time" format="HH:mm" value-format="HH:mm" placeholder="选择时间" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="large" @click="showAdd = false">取消</el-button>
        <el-button size="large" type="primary" @click="add">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }
.reminder-card {
  background: var(--c-paper); border-radius: var(--r-md); padding: 18px 20px;
  box-shadow: var(--shadow-1); margin-bottom: 10px;
  border-left: 4px solid var(--c-gold);
}
.reminder-card.stopped { opacity: 0.6; border-left-color: var(--c-ink-300); }
.r-top { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.r-content { font-size: 20px; font-weight: 700; color: var(--c-ink-900); }
.r-time { font-size: 14px; color: var(--c-ink-500); }
.r-actions { display: flex; align-items: center; gap: 12px; margin-top: 10px; }
.pill-green { background: #e8f5e9; color: #2e7d32; padding: 2px 10px; border-radius: 12px; font-size: 13px; }
.pill-grey { background: #eeeeee; color: #757575; padding: 2px 10px; border-radius: 12px; font-size: 13px; }
</style>
