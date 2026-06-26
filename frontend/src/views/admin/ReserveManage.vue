<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reserveApi } from '@/api/reserve'
import type { ReserveOrder } from '@/types'

const list = ref<ReserveOrder[]>([])
const loading = ref(false)

const statusMap: Record<number, string> = { 1: '待支付', 2: '已预约', 3: '已就诊', 4: '已取消' }
const sourceMap: Record<string, string> = { normal: '普通', elder: '老年优先' }

async function load() {
  loading.value = true
  try {
    const r = await reserveApi.listAll()
    list.value = r.data.data || []
  } catch {
    ElMessage.error('加载挂号记录失败')
  } finally { loading.value = false }
}

async function handleCancel(row: ReserveOrder) {
  if (row.order_status === 4) { ElMessage.warning('该订单已取消'); return }
  try {
    await ElMessageBox.confirm(`确定取消订单「${row.queue_code}」？号源将自动回收。`, '取消订单', { type: 'warning' })
  } catch { return }
  try {
    await reserveApi.cancel(row.id)
    ElMessage.success('已取消，号源已回收')
    load()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '取消失败') }
}

onMounted(load)
</script>
<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2 class="admin-title serif">挂号管理</h2>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="queue_code" label="候诊编号" width="180" />
      <el-table-column label="号源类型" width="100">
        <template #default="{ row }">{{ sourceMap[row.source_type] || row.source_type }}</template>
      </el-table-column>
      <el-table-column label="医生" width="100">
        <template #default="{ row }">{{ row.doctor_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="科室" width="120">
        <template #default="{ row }">{{ row.dept_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="医院" min-width="140">
        <template #default="{ row }">{{ row.hospital_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="出诊日期" width="120" prop="work_date" />
      <el-table-column label="就诊时段" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.time_period_text" :type="row.time_period === 'AM' ? '' : row.time_period === 'PM' ? 'success' : 'warning'" size="small">
            {{ row.time_period_text }}
          </el-tag>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column label="就诊人" width="100">
        <template #default="{ row }">{{ row.elder_name || '本人' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.order_status === 2 ? 'success' : row.order_status === 4 ? 'info' : ''">
            {{ statusMap[row.order_status] || row.order_status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="row.order_status !== 4" size="small" type="danger" @click="handleCancel(row)">取消</el-button>
          <span v-else style="color:#999">—</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.admin-title { font-size: 26px; font-weight: 900; margin: 0; color: var(--c-ink-900); }
</style>
