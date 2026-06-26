<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { SearchResultItem } from '@/types'

const props = defineProps<{
  results: SearchResultItem[]
  keyword: string
  loading: boolean
  visible: boolean
  error?: boolean
}>()

const emit = defineEmits<{
  close: []
  select: [item: SearchResultItem]
}>()

const router = useRouter()

const typeLabels: Record<string, string> = {
  hospital: '医院',
  department: '科室',
  doctor: '医生',
  symptom: '症状',
}

const typeColors: Record<string, string> = {
  hospital: '#E6A817',
  department: '#389E0D',
  doctor: '#1677FF',
  symptom: '#722ED1',
}

const hasResults = computed(() => props.results.length > 0)

function onSelect(item: SearchResultItem) {
  emit('select', item)
  if (item.extra?.route) {
    router.push(item.extra.route)
  }
}
</script>

<template>
  <div v-if="visible" class="search-overlay" @click.self="emit('close')">
    <div class="search-dropdown" role="listbox" aria-label="搜索结果" @click.stop>
      <!-- 加载中 -->
      <div v-if="loading" class="dropdown-loading" role="status">
        <span class="loading-spin"></span>
        搜索中...
      </div>

      <!-- 错误态 -->
      <div v-else-if="error" class="dropdown-empty dropdown-error" role="alert">
        搜索服务暂时不可用，请稍后重试
      </div>

      <!-- 空结果 -->
      <div v-else-if="!hasResults && keyword" class="dropdown-empty">
        未找到与「<strong>{{ keyword }}</strong>」相关的结果
        <p class="empty-hint">试试其他关键词，如"内科"、"人民"、"心血管"</p>
      </div>

      <!-- 结果列表 -->
      <template v-else-if="hasResults">
        <div class="dropdown-header">
          搜索「{{ keyword }}」共 {{ results.length }} 条结果
        </div>
        <div
          v-for="(item, index) in results"
          :key="`${item.type}-${item.id}`"
          class="result-item"
          role="option"
          :aria-selected="false"
          tabindex="0"
          @click="onSelect(item)"
          @keyup.enter="onSelect(item)"
        >
          <span
            class="type-badge"
            :style="{ background: typeColors[item.type] || '#999' }"
          >
            {{ typeLabels[item.type] || item.type }}
          </span>
          <div class="result-text">
            <div class="result-title">{{ item.title }}</div>
            <div class="result-sub">{{ item.subtitle }}</div>
          </div>
          <span class="result-arrow">→</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.15);
}

.search-dropdown {
  position: absolute;
  top: 64px;
  left: 50%;
  transform: translateX(-50%);
  width: 520px;
  max-height: 420px;
  overflow-y: auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 1000;
}

.dropdown-loading,
.dropdown-empty {
  padding: 32px 16px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.loading-spin {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #eee;
  border-top-color: #1677FF;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #bbb;
}

.dropdown-error {
  color: #ff4d4f;
}

.dropdown-header {
  padding: 10px 16px;
  font-size: 12px;
  color: #999;
  border-bottom: 1px solid #f0f0f0;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
}

.result-item:hover {
  background: #f5f7fa;
}

.type-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
}

.result-text {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-sub {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-arrow {
  flex-shrink: 0;
  color: #ccc;
  font-size: 14px;
}
</style>
