import http from './index'
import type { ApiResponse } from '@/types'

/** 支付模式 */
export type PayMode = 'sandbox' | 'mock'

/** 创建支付订单响应 */
export interface CreatePaymentData {
  order_id: string
  pay_url: string
  amount: number
  pay_mode: PayMode
}

/** 支付结果响应 */
export interface PaymentResultData {
  reserve_id: number
  pay_status: number
  order_status: number
  amount: number
  pay_time: string
}

export const paymentApi = {
  /** 创建支付订单（沙箱/模拟） */
  create: (reserve_id: number) =>
    http.post<ApiResponse<CreatePaymentData>>('/payment/create', { reserve_id }),

  /** 查询支付结果（轮询用，需登录） */
  getResult: (reserve_id: number) =>
    http.get<ApiResponse<PaymentResultData>>('/payment/result', { params: { reserve_id } }),

  /** 按商户订单号查询支付结果（支付宝回调用，无需登录） */
  queryByTradeNo: (out_trade_no: string) =>
    http.get<ApiResponse<PaymentResultData>>('/payment/query', { params: { out_trade_no } }),

  /** 主动同步支付宝支付状态（notify 回调未到达时的兜底） */
  syncStatus: (out_trade_no: string) =>
    http.post<ApiResponse<PaymentResultData>>('/payment/sync', null, { params: { out_trade_no } }),
}
