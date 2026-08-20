import http from './index'
import type { ApiResponse, GuideResponse } from '@/types'

export const guideApi = {
  diagnose: (symptom_text: string) =>
    http.post<ApiResponse<GuideResponse>>('/guide/diagnose', { symptom_text }),
  voiceSearch: (voice_text: string) =>
    http.post<ApiResponse>('/guide/voice-search', null, { params: { voice_text } }),

  /**
   * SSE 流式导诊（POST /guide/diagnose/stream）
   * EventSource 不支持 POST，用 fetch + ReadableStream 解析 SSE。
   * onEvent(event, data) 回调：start / node_end / final / error
   */
  streamDiagnose: async (
    symptom_text: string,
    onEvent: (event: string, data: any) => void,
  ): Promise<void> => {
    const token = localStorage.getItem('token')
    const resp = await fetch('/api/guide/diagnose/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ symptom_text }),
    })
    if (!resp.ok || !resp.body) throw new Error(`SSE 连接失败 ${resp.status}`)

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      // SSE 事件以空行分隔
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        let event = 'message'
        let data = ''
        for (const line of part.split('\n')) {
          if (line.startsWith('event:')) event = line.slice(6).trim()
          else if (line.startsWith('data:')) data += line.slice(5).trim()
        }
        if (!data) continue
        try {
          onEvent(event, JSON.parse(data))
        } catch {
          onEvent(event, data)
        }
      }
    }
  },
}
