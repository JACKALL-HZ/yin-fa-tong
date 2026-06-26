import http from './index'
import type { ApiResponse, GuideResponse } from '@/types'

export const guideApi = {
  diagnose: (symptom_text: string) =>
    http.post<ApiResponse<GuideResponse>>('/guide/diagnose', { symptom_text }),
  voiceSearch: (voice_text: string) =>
    http.post<ApiResponse>('/guide/voice-search', null, { params: { voice_text } }),
}
