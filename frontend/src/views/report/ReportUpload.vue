<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { reportApi } from '@/api/report'
import { userApi } from '@/api/user'
import { ElMessage } from 'element-plus'
import type { ElderBind, ReportUploadResult } from '@/types'

const router = useRouter()
const elders = ref<ElderBind[]>([])
const elderId = ref(0)
const file = ref<File | null>(null)
const preview = ref('')
const loading = ref(false)
const result = ref<ReportUploadResult | null>(null)

async function loadElders() {
  try {
    const r = await userApi.listElders()
    if (r.data?.code === 200) {
      elders.value = r.data.data || []
      if (elders.value.length === 1) elderId.value = elders.value[0].id
    }
  } catch { /* 网络错误静默处理 */ }
}
loadElders()

function onFileChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (!f) return
  file.value = f
  const reader = new FileReader()
  reader.onload = () => preview.value = reader.result as string
  reader.readAsDataURL(f)
}

async function upload() {
  if (!elderId.value || !file.value) return ElMessage.warning('请选择长辈和图片')
  loading.value = true
  try {
    const form = new FormData()
    form.append('elder_bind_id', String(elderId.value))
    form.append('file', file.value)
    const r = await reportApi.upload(form)
    if (r.data?.code === 200) {
      result.value = r.data.data ?? null
      ElMessage.success('报告上传成功')
    } else {
      ElMessage.error(r.data?.message || '上传失败')
    }
  } catch {
    ElMessage.error('网络错误，请重试')
  } finally { loading.value = false }
}
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">上传体检报告</span>
      <span class="sec-head-en">Upload Report</span>
    </div>

    <div class="card">
      <el-select v-model="elderId" placeholder="选择长辈" size="large" style="width:100%;margin-bottom:16px">
        <el-option v-for="e in elders" :key="e.id" :value="e.id" :label="e.elder_name" />
      </el-select>

      <label class="upload-area">
        <input type="file" accept="image/*" @change="onFileChange" hidden />
        <div v-if="preview" class="preview-wrap">
          <img :src="preview" class="preview-img" />
        </div>
        <div v-else class="placeholder">
          <span style="font-size:48px">📷</span>
          <span>点击拍摄或选择报告图片</span>
          <span style="font-size:14px;color:var(--c-ink-300)">支持 JPG/PNG，不超过 10MB</span>
        </div>
      </label>

      <button class="btn-primary" style="width:100%;font-size:22px;font-weight:800;letter-spacing:2px" :disabled="loading || !file" @click="upload">
        {{ loading ? '识别中...' : '上传并解读' }}
      </button>
    </div>

    <!-- OCR 结果 -->
    <div v-if="result" class="card" style="margin-top:20px">
      <h3 class="serif" style="font-size:22px;font-weight:800;color:var(--c-accent);margin-bottom:14px">解读结果</h3>
      <div class="interp-text">{{ result.interpretation }}</div>
      <div v-if="result.ocr_result?.indicators" class="indicators">
        <h4 style="margin:16px 0 10px;font-size:18px;color:var(--c-ink-900)">识别指标</h4>
        <div class="ind-grid">
          <div v-for="(val, key) in result.ocr_result.indicators" :key="key" class="ind-item">
            <span class="ind-key">{{ key }}</span>
            <span class="ind-val">{{ val }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.upload-area {
  display: block; border: 3px dashed var(--c-line-2); border-radius: var(--r-lg);
  padding: 40px 20px; text-align: center; cursor: pointer; margin-bottom: 16px;
  transition: .2s; background: var(--c-bg);
}
.upload-area:hover { border-color: var(--c-primary); }
.placeholder { display: flex; flex-direction: column; gap: 10px; color: var(--c-ink-500); font-size: 18px; }
.preview-img { max-width: 100%; max-height: 240px; border-radius: var(--r-md); }
.interp-text { font-size: 16px; color: var(--c-ink-700); line-height: 2; white-space: pre-wrap; }
.ind-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ind-item { display: flex; justify-content: space-between; padding: 10px 14px; background: var(--c-bg); border-radius: var(--r-md); font-size: 15px; }
.ind-key { color: var(--c-ink-500); }
.ind-val { font-weight: 800; color: var(--c-primary); }
</style>
