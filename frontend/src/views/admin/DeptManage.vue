<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deptApi } from '@/api/department'
import { hospitalApi } from '@/api/hospital'

const list = ref<any[]>([])
const hospitals = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const submitting = ref(false)
const form = ref({ hospital_id: null as number | null, dept_name: '' })

async function load() {
  loading.value = true
  try {
    const [r, h] = await Promise.all([deptApi.list(), hospitalApi.list()])
    list.value = r.data.data || []
    hospitals.value = h.data.data || []
  } finally { loading.value = false }
}

function getHospitalName(hospitalId: number) {
  const h = hospitals.value.find((x: any) => x.id === hospitalId)
  return h ? (h.hospital_name || h.name) : '-'
}

function openCreate() {
  isEdit.value = false; editId.value = null
  form.value = { hospital_id: null, dept_name: '' }
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id
  form.value = { hospital_id: row.hospital_id, dept_name: row.dept_name }
  dialogVisible.value = true
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除科室「${row.dept_name}」？`, '确认删除', { type: 'warning' })
  } catch { return }
  try {
    await deptApi.delete(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

async function submit() {
  if (!form.value.dept_name.trim()) { ElMessage.warning('请输入科室名称'); return }
  if (!form.value.hospital_id) { ElMessage.warning('请选择所属医院'); return }
  submitting.value = true
  try {
    if (isEdit.value && editId.value) {
      await deptApi.update(editId.value, { dept_name: form.value.dept_name })
      ElMessage.success('已更新')
    } else {
      await deptApi.create({ hospital_id: form.value.hospital_id, dept_name: form.value.dept_name })
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
      <h2 class="admin-title serif">科室管理</h2>
      <el-button type="primary" @click="openCreate">+ 添加科室</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="dept_name" label="科室名称" />
      <el-table-column label="所属医院" width="200">
        <template #default="{ row }">{{ getHospitalName(row.hospital_id) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑科室' : '添加科室'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="所属医院" required>
          <el-select v-model="form.hospital_id" style="width:100%" placeholder="选择医院" :disabled="isEdit">
            <el-option v-for="h in hospitals" :key="h.id" :label="h.hospital_name || h.name" :value="h.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="科室名称" required>
          <el-input v-model="form.dept_name" placeholder="如：心血管内科" />
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
