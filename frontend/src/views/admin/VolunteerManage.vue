<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { volunteerApi } from '@/api/volunteer'

const list = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const submitting = ref(false)
const form = ref({ vol_name: '', vol_phone: '', service_dept: '', service_desc: '', avatar: '', status: 1 })

async function load() {
  loading.value = true
  try {
    const r = await volunteerApi.list()
    list.value = r.data.data || []
  } finally { loading.value = false }
}

function openCreate() {
  isEdit.value = false; editId.value = null
  form.value = { vol_name: '', vol_phone: '', service_dept: '', service_desc: '', avatar: '', status: 1 }
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id
  form.value = {
    vol_name: row.vol_name || '',
    vol_phone: row.vol_phone || '',
    service_dept: row.service_dept || '',
    service_desc: row.service_desc || '',
    avatar: row.avatar || '',
    status: row.status ?? 1,
  }
  dialogVisible.value = true
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除志愿者「${row.vol_name}」？`, '确认删除', { type: 'warning' })
  } catch { return }
  try {
    await volunteerApi.delete(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

async function handleToggleStatus(row: any) {
  const newStatus = row.status === 1 ? 0 : 1
  const label = newStatus === 1 ? '上架' : '下架'
  try {
    await ElMessageBox.confirm(`确定${label}志愿者「${row.vol_name}」？`, '确认操作', { type: 'warning' })
  } catch { return }
  try {
    await volunteerApi.update(row.id, { status: newStatus })
    ElMessage.success(`已${label}`)
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || `${label}失败`) }
}

async function submit() {
  if (!form.value.vol_name.trim()) { ElMessage.warning('请输入姓名'); return }
  if (!form.value.vol_phone.trim()) { ElMessage.warning('请输入手机号'); return }
  submitting.value = true
  try {
    if (isEdit.value && editId.value) {
      await volunteerApi.update(editId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await volunteerApi.create(form.value)
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
      <h2 class="admin-title serif">志愿者管理</h2>
      <el-button type="primary" @click="openCreate">+ 添加志愿者</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="vol_name" label="姓名" width="100" />
      <el-table-column prop="vol_phone" label="手机号" width="140" />
      <el-table-column label="服务科室" min-width="140">
        <template #default="{ row }">{{ row.service_dept || '-' }}</template>
      </el-table-column>
      <el-table-column label="评分" width="80">
        <template #default="{ row }">⭐{{ Number(row.service_score || 0).toFixed(1) }}</template>
      </el-table-column>
      <el-table-column label="服务次数" width="90" prop="service_count" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '可预约' : '已下架' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" :type="row.status === 1 ? 'warning' : 'success'" @click="handleToggleStatus(row)">
            {{ row.status === 1 ? '下架' : '上架' }}
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑志愿者' : '添加志愿者'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.vol_name" placeholder="志愿者姓名" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="form.vol_phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="服务科室">
          <el-input v-model="form.service_dept" placeholder="如：心血管内科" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.service_desc" type="textarea" :rows="2" placeholder="陪诊服务简介" />
        </el-form-item>
        <el-form-item label="头像URL">
          <el-input v-model="form.avatar" placeholder="https://..." />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="可预约" inactive-text="已下架" />
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
