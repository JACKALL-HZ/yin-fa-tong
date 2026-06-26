import http from './index'
import type { ApiResponse, AccompanyOrder } from '@/types'

export const accompanyApi = {
  create: (data: any) => http.post<ApiResponse<AccompanyOrder>>('/accompany-orders', data),
  listMy: (params?: any) => http.get<ApiResponse<AccompanyOrder[]>>('/accompany-orders', { params }),
  review: (id: number, data: { service_score: number; service_comment?: string }) =>
    http.post<ApiResponse<AccompanyOrder>>(`/accompany-orders/${id}/review`, data),
  listAll: (params?: any) => http.get<ApiResponse<AccompanyOrder[]>>('/accompany-orders/admin/all', { params }),
  approve: (id: number) => http.post<ApiResponse<AccompanyOrder>>(`/accompany-orders/${id}/approve`),
  reject: (id: number) => http.post<ApiResponse>(`/accompany-orders/${id}/reject`),
  start: (id: number) => http.post<ApiResponse<AccompanyOrder>>(`/accompany-orders/${id}/start`),
  complete: (id: number) => http.post<ApiResponse<AccompanyOrder>>(`/accompany-orders/${id}/complete`),
}
