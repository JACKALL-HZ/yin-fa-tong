<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportApi } from '@/api/report'
import type { ReportDetail } from '@/types'
import { formatDate } from '@/utils'

const route = useRoute()
const router = useRouter()
const detail = ref<ReportDetail | null>(null)
const loading = ref(true)
const deleting = ref(false)
const imgError = ref(false)

async function load() {
  const id = Number(route.params.id)
  if (!id) return router.back()
  loading.value = true
  try {
    const r = await reportApi.getById(id)
    if (r.data?.code === 200) {
      detail.value = r.data.data || null
    } else {
      ElMessage.error(r.data?.message || '加载失败')
      router.back()
    }
  } catch {
    ElMessage.error('网络错误')
    router.back()
  } finally {
    loading.value = false
  }
}

async function handleDelete() {
  if (!detail.value || deleting.value) return
  try {
    await ElMessageBox.confirm('确定删除该体检报告？删除后不可恢复。', '确认删除', { type: 'warning' })
  } catch { return }
  deleting.value = true
  try {
    await reportApi.delete(detail.value.id)
    ElMessage.success('报告已删除')
    router.replace('/reports')
  } catch (e: any) {
    // 拦截器已弹出后端错误信息，此处不重复提示
  } finally {
    deleting.value = false
  }
}

const indicators = ref<[string, number][]>([])
onMounted(async () => {
  await load()
  if (detail.value?.ocr_result?.indicators) {
    indicators.value = Object.entries(detail.value.ocr_result.indicators) as [string, number][]
  }
})
</script>

<template>
  <div class="page-wrap" v-loading="loading">
    <div v-if="detail" class="detail-card">
      <!-- 头部 -->
      <div class="detail-header">
        <div class="header-left">
          <div class="detail-title">📋 体检报告详情</div>
          <div class="detail-date">{{ formatDate(detail.create_time) }}</div>
        </div>
        <el-button type="danger" plain size="small" :loading="deleting" @click="handleDelete">🗑️ 删除</el-button>
      </div>

      <!-- 报告图片 -->
      <div class="section" v-if="detail.report_url">
        <div class="section-title">报告图片</div>
        <div class="img-wrap">
          <img
            v-if="!imgError"
            :src="detail.report_url"
            alt="体检报告"
            class="report-img"
            @error="imgError = true"
          />
          <div v-else class="img-fail">图片加载失败</div>
        </div>
      </div>

      <!-- 识别指标 -->
      <div class="section" v-if="indicators.length > 0">
        <div class="section-title">识别指标</div>
        <div class="indicator-grid">
          <div v-for="[name, val] in indicators" :key="name" class="indicator-item">
            <span class="ind-name">{{ name }}</span>
            <span class="ind-val">{{ val }}</span>
          </div>
        </div>
      </div>

      <!-- 通俗解读 -->
      <div class="section" v-if="detail.interpretation">
        <div class="section-title">通俗解读</div>
        <div class="interp-text">{{ detail.interpretation }}</div>
      </div>

      <!-- OCR 原始文本 -->
      <div class="section" v-if="detail.ocr_result?.text">
        <div class="section-title">OCR 原始文本</div>
        <div class="ocr-text">{{ detail.ocr_result.text }}</div>
      </div>
    </div>

    <div v-else-if="!loading" class="empty">报告不存在</div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.detail-card { background: var(--c-paper); border-radius: var(--r-lg); box-shadow: var(--shadow-2); padding: 28px; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.detail-title { font-size: 22px; font-weight: 800; color: var(--c-ink-900); }
.detail-date { font-size: 14px; color: var(--c-ink-500); margin-top: 4px; }
.section { margin-bottom: 24px; }
.section-title { font-size: 16px; font-weight: 700; color: var(--c-ink-700); margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--c-ink-100); }
.img-wrap { text-align: center; }
.report-img { max-width: 100%; max-height: 600px; border-radius: var(--r-md); box-shadow: var(--shadow-1); }
.img-fail { padding: 40px; color: var(--c-ink-300); font-size: 15px; }
.indicator-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.indicator-item { display: flex; justify-content: space-between; padding: 10px 14px; background: var(--c-cream); border-radius: var(--r-sm); }
.ind-name { font-size: 14px; color: var(--c-ink-700); }
.ind-val { font-size: 14px; font-weight: 700; color: var(--c-ink-900); }
.interp-text { font-size: 15px; line-height: 1.8; color: var(--c-ink-700); white-space: pre-wrap; }
.ocr-text { font-size: 13px; line-height: 1.7; color: var(--c-ink-500); background: var(--c-cream); padding: 14px; border-radius: var(--r-sm); white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }
</style>
