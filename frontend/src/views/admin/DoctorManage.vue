<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { doctorApi } from '@/api/doctor'
import { deptApi } from '@/api/department'

const list = ref<any[]>([])
const departments = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const submitting = ref(false)
const form = ref<{ dept_id?: number; doctor_name: string; doctor_title: string; specialty: string; register_fee: number }>({ dept_id: undefined, doctor_name: '', doctor_title: '', specialty: '', register_fee: 0 })

function getDeptName(deptId: number) {
  const d = departments.value.find((x: any) => x.id === deptId)
  return d ? d.dept_name : '-'
}

async function load() {
  loading.value = true
  try {
    const [r, d] = await Promise.all([doctorApi.list(), deptApi.list()])
    list.value = r.data.data || []
    departments.value = d.data.data || []
  } finally { loading.value = false }
}

function openCreate() {
  isEdit.value = false; editId.value = null
  form.value = { dept_id: undefined, doctor_name: '', doctor_title: '', specialty: '', register_fee: 0 }
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id
  form.value = {
    dept_id: row.dept_id ?? row.dept_id,
    doctor_name: row.doctor_name || row.doc_name || '',
    doctor_title: row.doctor_title || row.title || '',
    specialty: row.specialty || '',
    register_fee: Number(row.register_fee) || 0,
  }
  dialogVisible.value = true
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除医生「${row.doctor_name || row.doc_name}」？`, '确认删除', { type: 'warning' })
  } catch { return }
  try {
    await doctorApi.delete(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

async function submit() {
  if (!form.value.doctor_name.trim()) { ElMessage.warning('请输入医生姓名'); return }
  if (!form.value.dept_id) { ElMessage.warning('请选择所属科室'); return }
  const data = { ...form.value, dept_id: form.value.dept_id! }
  submitting.value = true
  try {
    if (isEdit.value && editId.value) {
      await doctorApi.update(editId.value, data)
      ElMessage.success('已更新')
    } else {
      await doctorApi.create(data as any)
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
      <h2 class="admin-title serif">医生管理</h2>
      <el-button type="primary" @click="openCreate">+ 添加医生</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="姓名">
        <template #default="{ row }">{{ row.doctor_name || row.doc_name }}</template>
      </el-table-column>
      <el-table-column label="职称" width="100">
        <template #default="{ row }">{{ row.doctor_title || row.title || '-' }}</template>
      </el-table-column>
      <el-table-column label="所属科室" width="150">
        <template #default="{ row }">{{ row.dept_name || getDeptName(row.dept_id) }}</template>
      </el-table-column>
      <el-table-column label="擅长" min-width="180">
        <template #default="{ row }">{{ row.specialty || '-' }}</template>
      </el-table-column>
      <el-table-column label="挂号费" width="100">
        <template #default="{ row }">¥{{ row.register_fee || 0 }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑医生' : '添加医生'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="所属科室" required>
          <el-select v-model="form.dept_id" style="width:100%" placeholder="选择科室" :disabled="isEdit">
            <el-option v-for="d in departments" :key="d.id" :label="d.dept_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="医生姓名" required>
          <el-input v-model="form.doctor_name" placeholder="如：王主任" />
        </el-form-item>
        <el-form-item label="职称">
          <el-select v-model="form.doctor_title" style="width:100%" placeholder="选择职称">
            <el-option label="主任医师" value="主任医师" />
            <el-option label="副主任医师" value="副主任医师" />
            <el-option label="主治医师" value="主治医师" />
            <el-option label="住院医师" value="住院医师" />
          </el-select>
        </el-form-item>
        <el-form-item label="擅长">
          <el-input v-model="form.specialty" type="textarea" :rows="2" placeholder="如：冠心病、高血压诊治" />
        </el-form-item>
        <el-form-item label="挂号费(元)">
          <el-input-number v-model="form.register_fee" :min="0" :step="5" style="width:100%" />
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
