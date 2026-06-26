<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scheduleApi } from '@/api/schedule'
import { doctorApi } from '@/api/doctor'

const list = ref<any[]>([])
const doctors = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editId = ref<number | null>(null)
const submitting = ref(false)
const form = ref<{ doctor_id?: number; work_date: string; time_period: string; normal_num: number; elder_priority_num: number }>({ doctor_id: undefined, work_date: '', time_period: 'AM', normal_num: 20, elder_priority_num: 5 })

const periodMap: Record<string, string> = { AM: '上午', PM: '下午', ALL: '全天' }

function getDoctorName(doctorId: number) {
  const d = doctors.value.find((x: any) => x.id === doctorId)
  return d ? (d.doctor_name || d.doc_name) : '-'
}

async function load() {
  loading.value = true
  try {
    const [r, d] = await Promise.all([scheduleApi.list(), doctorApi.list()])
    list.value = r.data.data || []
    doctors.value = d.data.data || []
  } finally { loading.value = false }
}

function openCreate() {
  editId.value = null
  form.value = { doctor_id: undefined, work_date: '', time_period: 'AM', normal_num: 20, elder_priority_num: 5 }
  dialogVisible.value = true
}

function openEdit(row: any) {
  editId.value = row.id
  form.value = {
    doctor_id: row.doctor_id,
    work_date: row.work_date || row.schedule_date || '',
    time_period: row.time_period || 'AM',
    normal_num: row.normal_num || 0,
    elder_priority_num: row.elder_priority_num || 0,
  }
  dialogVisible.value = true
}

async function handleDelete(row: any) {
  const doctorName = row.doctor_name || getDoctorName(row.doctor_id) || '未知'
  const date = row.work_date || row.schedule_date || '未知'
  try {
    await ElMessageBox.confirm(`确定删除「${doctorName}」在「${date}」的排班？`, '确认删除', { type: 'warning' })
  } catch { return }
  try {
    await scheduleApi.delete(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

async function submit() {
  if (!form.value.doctor_id) { ElMessage.warning('请选择医生'); return }
  if (!form.value.work_date) { ElMessage.warning('请选择出诊日期'); return }
  submitting.value = true
  try {
    if (editId.value) {
      await scheduleApi.update(editId.value, { normal_num: form.value.normal_num, elder_priority_num: form.value.elder_priority_num })
      ElMessage.success('已更新')
    } else {
      await scheduleApi.create(form.value as any)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '操作失败') }
  finally { submitting.value = false }
}

onMounted(load)
</script>
<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2 class="admin-title serif">排班管理</h2>
      <el-button type="primary" @click="openCreate">+ 发布排班</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="医生" width="120">
        <template #default="{ row }">{{ row.doctor_name || getDoctorName(row.doctor_id) }}</template>
      </el-table-column>
      <el-table-column label="出诊日期" width="130">
        <template #default="{ row }">{{ row.work_date || row.schedule_date }}</template>
      </el-table-column>
      <el-table-column label="时段" width="80">
        <template #default="{ row }">
          <el-tag size="small">{{ periodMap[row.time_period] || row.time_period }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="普通号" width="100" prop="normal_num" />
      <el-table-column label="老年号" width="100" prop="elder_priority_num" />
      <el-table-column label="普通剩余" width="100" prop="normal_remain" />
      <el-table-column label="老年剩余" width="100" prop="elder_remain" />
      <el-table-column label="操作" min-width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">调整号源</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editId ? '调整号源' : '发布排班'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="出诊医生" required>
          <el-select v-model="form.doctor_id" style="width:100%" placeholder="选择医生" :disabled="!!editId">
            <el-option v-for="d in doctors" :key="d.id" :label="d.doctor_name || d.doc_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="出诊日期" required>
          <el-date-picker v-model="form.work_date" type="date" placeholder="选择日期" style="width:100%" value-format="YYYY-MM-DD" :disabled="!!editId" />
        </el-form-item>
        <el-form-item label="时段">
          <el-select v-model="form.time_period" style="width:100%" :disabled="!!editId">
            <el-option label="上午" value="AM" />
            <el-option label="下午" value="PM" />
            <el-option label="全天" value="ALL" />
          </el-select>
        </el-form-item>
        <el-form-item label="普通号数量">
          <el-input-number v-model="form.normal_num" :min="0" :step="5" style="width:100%" />
        </el-form-item>
        <el-form-item label="老年优先号数量">
          <el-input-number v-model="form.elder_priority_num" :min="0" :step="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin-title { font-size: 26px; font-weight: 900; margin: 0; color: var(--c-ink-900); }
</style>
