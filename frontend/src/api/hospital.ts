import http from './index'
import type { ApiResponse, Hospital } from '@/types'

export const hospitalApi = {
  list: (params?: any) => http.get<ApiResponse<Hospital[]>>('/hospitals', { params }),
  getById: (id: number) => http.get<ApiResponse<Hospital>>(`/hospitals/${id}`),
  create: (data: Partial<Hospital>) => http.post<ApiResponse<Hospital>>('/hospitals', data),
  update: (id: number, data: Partial<Hospital>) => http.put<ApiResponse<Hospital>>(`/hospitals/${id}`, data),
  delete: (id: number) => http.delete<ApiResponse>(`/hospitals/${id}`),
}
