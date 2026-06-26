import http from './index'
import type { ApiResponse, Reminder } from '@/types'

export const reminderApi = {
  list: () => http.get<ApiResponse<Reminder[]>>('/reminders'),
  create: (data: { remind_type: string; remind_time: string; remind_content: string }) =>
    http.post<ApiResponse<Reminder>>('/reminders', data),
  toggle: (id: number, is_active: number) =>
    http.patch<ApiResponse>(`/reminders/${id}/toggle`, { is_active }),
  remove: (id: number) =>
    http.delete<ApiResponse>(`/reminders/${id}`),
}
