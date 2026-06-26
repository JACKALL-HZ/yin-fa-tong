import http from './index'
import type { ApiResponse } from '@/types'

export const statsApi = {
  dashboard: () => http.get<ApiResponse>('/statistics/dashboard'),
}
