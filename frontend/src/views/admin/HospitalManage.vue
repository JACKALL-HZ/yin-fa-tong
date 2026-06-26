<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { hospitalApi } from '@/api/hospital'

const list = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const submitting = ref(false)
const form = ref({ hospital_name: '', hospital_level: '', address: '', phone: '' })

const levelMap: Record<string, string> = { '三级甲等': '三甲', '二级甲等': '二甲', '一级': '社区' }

async function load() {
  loading.value = true
  try {
    const r = await hospitalApi.list()
    list.value = r.data.data || []
  } finally { loading.value = false }
}

function openCreate() {
  isEdit.value = false; editId.value = null
  form.value = { hospital_name: '', hospital_level: '', address: '', phone: '' }
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id
  form.value = { hospital_name: row.hospital_name || row.name, hospital_level: row.hospital_level || row.level || '', address: row.address || '', phone: row.phone || '' }
  dialogVisible.value = true
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除医院「${row.hospital_name || row.name}」？`, '确认删除', { type: 'warning' })
  } catch { return }
  try {
    await hospitalApi.delete(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '删除失败') }
}

async function submit() {
  if (!form.value.hospital_name.trim()) { ElMessage.warning('请输入医院名称'); return }
  submitting.value = true
  try {
    if (isEdit.value && editId.value) {
      await hospitalApi.update(editId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await hospitalApi.create(form.value)
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
      <h2 class="admin-title serif">医院管理</h2>
      <el-button type="primary" @click="openCreate">+ 添加医院</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="hospital_name" label="医院名称">
        <template #default="{ row }">{{ row.hospital_name || row.name }}</template>
      </el-table-column>
      <el-table-column prop="address" label="地址" />
      <el-table-column prop="hospital_level" label="等级" width="100">
        <template #default="{ row }">
          <el-tag :type="(row.hospital_level || row.level) === '三级甲等' ? 'danger' : (row.hospital_level || row.level) === '二级甲等' ? 'warning' : ''">
            {{ levelMap[row.hospital_level || row.level] || row.hospital_level || row.level || '-' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑医院' : '添加医院'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="医院名称" required>
          <el-input v-model="form.hospital_name" placeholder="如：社区合作医院" />
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="form.hospital_level" style="width:100%" placeholder="选择等级">
            <el-option label="三级甲等" value="三级甲等" />
            <el-option label="二级甲等" value="二级甲等" />
            <el-option label="一级" value="一级" />
          </el-select>
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" placeholder="医院地址" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" placeholder="联系电话" />
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
