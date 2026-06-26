<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accompanyApi } from '@/api/accompany'

const list = ref<any[]>([])
const loading = ref(false)

const statusMap: Record<number, string> = { 1: '待审核', 2: '待服务', 3: '服务中', 4: '已完成', 5: '已取消' }

async function load() {
  loading.value = true
  try {
    const r = await accompanyApi.listAll()
    list.value = r.data.data || []
  } finally { loading.value = false }
}

async function handleApprove(row: any) {
  try {
    await ElMessageBox.confirm(`确定通过陪诊申请（订单 #${row.id}）？`, '审核通过', { type: 'success' })
  } catch { return }
  try {
    await accompanyApi.approve(row.id)
    ElMessage.success('已通过')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '审核失败') }
}

async function handleReject(row: any) {
  try {
    await ElMessageBox.confirm(`确定拒绝陪诊申请（订单 #${row.id}）？`, '审核拒绝', { type: 'warning' })
  } catch { return }
  try {
    await accompanyApi.reject(row.id)
    ElMessage.success('已拒绝')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '拒绝操作失败') }
}

async function handleStart(row: any) {
  try {
    await ElMessageBox.confirm(`确定开始服务（订单 #${row.id}）？`, '开始服务')
  } catch { return }
  try {
    await accompanyApi.start(row.id)
    ElMessage.success('服务已开始')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '操作失败') }
}

async function handleComplete(row: any) {
  try {
    await ElMessageBox.confirm(`确定完成服务（订单 #${row.id}）？`, '完成服务', { type: 'success' })
  } catch { return }
  try {
    await accompanyApi.complete(row.id)
    ElMessage.success('服务已完成')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '操作失败') }
}

onMounted(load)
</script>
<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2 class="admin-title serif">陪诊管理</h2>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="长辈" width="100">
        <template #default="{ row }">{{ row.elder_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="志愿者" width="100">
        <template #default="{ row }">{{ row.vol_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="陪诊日期" width="130" prop="accompany_date" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.order_status === 1 ? 'warning' : row.order_status === 2 ? '' : row.order_status === 4 ? 'success' : 'info'">
            {{ row.status_text || statusMap[row.order_status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="评价" min-width="160">
        <template #default="{ row }">{{ row.service_comment || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <template v-if="row.order_status === 1">
            <el-button size="small" type="success" @click="handleApprove(row)">通过</el-button>
            <el-button size="small" type="danger" @click="handleReject(row)">拒绝</el-button>
          </template>
          <template v-else-if="row.order_status === 2">
            <el-button size="small" type="primary" @click="handleStart(row)">开始服务</el-button>
          </template>
          <template v-else-if="row.order_status === 3">
            <el-button size="small" type="success" @click="handleComplete(row)">完成服务</el-button>
          </template>
          <span v-else style="color:#999">—</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.admin-title { font-size: 26px; font-weight: 900; margin: 0; color: var(--c-ink-900); }
</style>
