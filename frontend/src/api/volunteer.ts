import http from './index'
import type { ApiResponse, Volunteer } from '@/types'

export const volunteerApi = {
  list: () => http.get<ApiResponse<Volunteer[]>>('/volunteers'),
  getById: (id: number) => http.get<ApiResponse<Volunteer>>(`/volunteers/${id}`),
  create: (data: Partial<Volunteer>) => http.post<ApiResponse<Volunteer>>('/volunteers', data),
  update: (id: number, data: Partial<Volunteer>) => http.put<ApiResponse<Volunteer>>(`/volunteers/${id}`, data),
  delete: (id: number) => http.delete<ApiResponse>(`/volunteers/${id}`),
}
