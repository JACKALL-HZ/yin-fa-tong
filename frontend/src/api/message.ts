import http from './index'
import type { ApiResponse, Message } from '@/types'

export const msgApi = {
  list: () => http.get<ApiResponse<Message[]>>('/messages'),
  read: (id: number) => http.post<ApiResponse>(`/messages/${id}/read`),
  unreadCount: () => http.get<ApiResponse<number>>('/messages/unread-count'),
}
