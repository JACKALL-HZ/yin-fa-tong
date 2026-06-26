import http from './index'
import type { ApiResponse, Schedule } from '@/types'

export const scheduleApi = {
  list: (params?: any) => http.get<ApiResponse<Schedule[]>>('/schedules', { params }),
  getById: (id: number) => http.get<ApiResponse<Schedule>>(`/schedules/${id}`),
  create: (data: Partial<Schedule>) => http.post<ApiResponse<Schedule>>('/schedules', data),
  update: (id: number, data: Partial<Schedule>) => http.put<ApiResponse<Schedule>>(`/schedules/${id}`, data),
  delete: (id: number) => http.delete<ApiResponse>(`/schedules/${id}`),
}
