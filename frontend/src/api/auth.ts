import http from './index'
import type { ApiResponse, LoginRequest, RegisterRequest, TokenResponse, UserInfo } from '@/types'

export const authApi = {
  login: (data: LoginRequest) => http.post<ApiResponse<TokenResponse>>('/auth/login', data),
  register: (data: RegisterRequest) => http.post<ApiResponse<TokenResponse>>('/auth/register', data),
  wxLogin: (code: string) => http.post<ApiResponse<TokenResponse>>('/auth/wx-login', { code }),
  alipayLogin: (auth_code: string) => http.post<ApiResponse<TokenResponse>>('/auth/alipay-login', { auth_code }),
  getMe: () => http.get<ApiResponse<UserInfo>>('/auth/me'),
}
