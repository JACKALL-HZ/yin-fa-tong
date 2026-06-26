import http from './index'
import type { ApiResponse, ReserveCreate, ReserveOrder } from '@/types'

export const reserveApi = {
  create: (data: ReserveCreate) => http.post<ApiResponse<ReserveOrder>>('/reserves', data),
  listMy: (params?: any) => http.get<ApiResponse<ReserveOrder[]>>('/reserves', { params }),
  getById: (id: number) => http.get<ApiResponse<ReserveOrder>>(`/reserves/${id}`),
  pay: (id: number) => http.post<ApiResponse>(`/reserves/${id}/pay`),
  cancel: (id: number) => http.post<ApiResponse>(`/reserves/${id}/cancel`),
  listAll: (params?: any) => http.get<ApiResponse<ReserveOrder[]>>('/reserves/admin/all', { params }),
}
