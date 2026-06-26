import http from './index'
import type { ApiResponse, QueueStatus } from '@/types'

export interface QueuePosition {
  queue_code: string
  my_number: number
  current_number: number
  before_you: number
  estimated_minutes: number
}

export const queueApi = {
  status: (scheduleId: number) => http.get<ApiResponse<QueueStatus>>(`/queue/status/${scheduleId}`),
  myPosition: (queueCode: string) => http.get<ApiResponse<QueuePosition>>(`/queue/my-position/${queueCode}`),
}
