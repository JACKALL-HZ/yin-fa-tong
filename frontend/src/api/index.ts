import axios, { AxiosError, type AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000,  // 60s，适配 Dify AI 长链路调用
})

// 请求拦截器：注入 Token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：统一错误处理
http.interceptors.response.use(
  (res: AxiosResponse<ApiResponse>) => {
    const body = res.data
    if (body.code !== 200 && body.code !== 0) {
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message))
    }
    return res
  },
  (err: AxiosError<ApiResponse>) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(err)
    }
    const msg = err.response?.data?.message || err.message || '网络异常'
    ElMessage.error(msg)
    return Promise.reject(err)
  },
)

export default http
