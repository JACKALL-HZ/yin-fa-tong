import http from './index'
import type { ApiResponse, Doctor } from '@/types'

export const doctorApi = {
  list: (params?: any) => http.get<ApiResponse<Doctor[]>>('/doctors', { params }),
  getById: (id: number) => http.get<ApiResponse<Doctor>>(`/doctors/${id}`),
  create: (data: Partial<Doctor>) => http.post<ApiResponse<Doctor>>('/doctors', data),
  update: (id: number, data: Partial<Doctor>) => http.put<ApiResponse<Doctor>>(`/doctors/${id}`, data),
  delete: (id: number) => http.delete<ApiResponse>(`/doctors/${id}`),
}
