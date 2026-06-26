import http from './index'
import type { ApiResponse, ElderBind, ProfileUpdate, UserInfo } from '@/types'

export interface TodoItem {
  icon: string
  text: string
  time: string
  urgent: boolean
}

export interface AlertItem {
  icon: string
  title: string
  desc: string
  time: string
}

export interface ElderReminderData {
  todos: TodoItem[]
  alerts: AlertItem[]
  health_reminders: HealthReminderItem[]
}

export interface HealthReminderItem {
  icon: string
  title: string
  desc: string
  action: string
}

export const userApi = {
  listElders: () => http.get<ApiResponse<ElderBind[]>>('/user/elders'),
  getElder: (id: number) => http.get<ApiResponse<ElderBind>>(`/user/elders/${id}`),
  createElder: (data: any) => http.post<ApiResponse<ElderBind>>('/user/elders', data),
  updateElder: (id: number, data: any) => http.put<ApiResponse<ElderBind>>(`/user/elders/${id}`, data),
  deleteElder: (id: number) => http.delete<ApiResponse>(`/user/elders/${id}`),
  getElderReminders: () => http.get<ApiResponse<ElderReminderData>>('/user/elders/reminders')
    .catch(() => ({ data: { code: 200, message: 'ok', data: { todos: [], alerts: [], health_reminders: [] } } })),
  updateProfile: (data: ProfileUpdate) => http.put<ApiResponse<UserInfo>>('/user/profile', data),
}
