<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { msgApi } from '@/api/message'
import type { Message } from '@/types'
import { formatDate } from '@/utils'
import { ElMessage } from 'element-plus'

const list = ref<Message[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const r = await msgApi.list()
    list.value = r.data.data || []
  } catch (e: any) {
    console.error('加载消息失败:', e)
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

async function readMsg(id: number) {
  try {
    await msgApi.read(id)
    await load()
  } catch (e) {
    console.error('标记已读失败:', e)
  }
}

onMounted(() => load())
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">消息中心</span>
      <span class="sec-head-en">Messages</span>
    </div>

    <div v-if="list.length === 0 && !loading" class="empty">暂无消息</div>
    <div v-for="m in list" :key="(m as any).id" class="msg-item card-hover" :class="{ unread: (m as any).read_status === 0 }" @click="readMsg((m as any).id)">
      <span class="pill pill-accent msg-type-pill">{{ ['','系统','挂号','候诊','健康提醒','陪诊'][(m as any).msg_type] || '通知' }}</span>
      <div class="msg-body">
        <div class="msg-text">{{ (m as any).msg_content }}</div>
        <div class="msg-time">{{ formatDate((m as any).create_time, 'MM-DD HH:mm') }}</div>
      </div>
      <div v-if="(m as any).read_status === 0" class="unread-dot"></div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }
.msg-item {
  display: flex; align-items: center; gap: 14px; padding: 18px 20px;
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-md); box-shadow: var(--shadow-1);
  margin-bottom: 10px; cursor: pointer;
}
.msg-item.unread { border-left: 4px solid var(--c-primary); }
.msg-type-pill { flex-shrink: 0; font-size: 12px; }
.msg-body { flex: 1; min-width: 0; }
.msg-text { font-size: 16px; font-weight: 600; color: var(--c-ink-700); }
.msg-time { font-size: 13px; color: var(--c-ink-300); margin-top: 4px; }
.unread-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--c-primary); flex-shrink: 0; }
</style>
