import http from './index'
import type { ApiResponse, SearchResponse } from '@/types'

export const searchApi = {
  search: (keyword: string, type: string = 'all', signal?: AbortSignal) =>
    http.get<ApiResponse<SearchResponse>>('/search', { params: { keyword, type }, signal }),
}
