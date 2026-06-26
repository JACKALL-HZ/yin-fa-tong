import http from './index'
import type { ApiResponse, Department } from '@/types'

export const deptApi = {
  list: (params?: any) => http.get<ApiResponse<Department[]>>('/departments', { params }),
  getByHospital: (hospitalId: number) => http.get<ApiResponse<Department[]>>(`/departments/by-hospital/${hospitalId}`),
  create: (data: Partial<Department>) => http.post<ApiResponse<Department>>('/departments', data),
  update: (id: number, data: Partial<Department>) => http.put<ApiResponse<Department>>(`/departments/${id}`, data),
  delete: (id: number) => http.delete<ApiResponse>(`/departments/${id}`),
}
