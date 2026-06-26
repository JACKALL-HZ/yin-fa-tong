import { ref } from 'vue'
import type { AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'

/**
 * 通用异步请求封装
 * 用法: const { data, loading, error, run } = useRequest(() => someApi())
 */
export function useRequest<T>(
  fn: () => Promise<AxiosResponse<ApiResponse<T>>>,
) {
  const loading = ref(false)
  const data = ref<T>()
  const error = ref<string>()

  async function run() {
    loading.value = true
    error.value = undefined
    try {
      const res = await fn()
      data.value = res.data.data
      return data.value
    } catch (e: any) {
      error.value = e?.message || '请求失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, data, error, run }
}
