import http from './index'
import type { ApiResponse, LoginRequest, RegisterRequest, TokenResponse, UserInfo } from '@/types'

export const authApi = {
  login: (data: LoginRequest) => http.post<ApiResponse<TokenResponse>>('/auth/login', data),
  register: (data: RegisterRequest) => http.post<ApiResponse<TokenResponse>>('/auth/register', data),
  wxLogin: (code: string) => http.post<ApiResponse<TokenResponse>>('/auth/wx-login', { code }),
  alipayLogin: (auth_code: string) => http.post<ApiResponse<TokenResponse>>('/auth/alipay-login', { auth_code }),
  getMe: () => http.get<ApiResponse<UserInfo>>('/auth/me'),
  /** 发送短信验证码 */
  sendSmsCode: (phone: string) => http.post<ApiResponse<null>>('/auth/sms/send', { phone }),
  /** 手机号验证码登录/注册 */
  smsLogin: (phone: string, code: string) =>
    http.post<ApiResponse<TokenResponse>>('/auth/sms/login', { phone, code }),
  /** 管理员登录 */
  adminLogin: (username: string, password: string) =>
    http.post<ApiResponse<TokenResponse>>('/auth/admin/login', { username, password }),
  /** 手机号+验证码注册 */
  registerWithCode: (phone: string, code: string, password: string) =>
    http.post<ApiResponse<TokenResponse>>('/auth/register/code', { phone, code, password }),
}
