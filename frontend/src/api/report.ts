import http from './index'
import type { ApiResponse, ReportItem, ReportDetail } from '@/types'

export const reportApi = {
  upload: (form: FormData) =>
    http.post<ApiResponse>('/reports/upload', form),
  list: () => http.get<ApiResponse<ReportItem[]>>('/reports'),
  getById: (id: number) => http.get<ApiResponse<ReportDetail>>('/reports/' + id),
  delete: (id: number) => http.delete<ApiResponse>(`/reports/${id}`),
}
