/** 格式化日期 */
export function formatDate(d: string | Date, fmt = 'YYYY-MM-DD'): string {
  const date = typeof d === 'string' ? new Date(d) : d
  const o: Record<string, string> = {
    YYYY: String(date.getFullYear()),
    MM: String(date.getMonth() + 1).padStart(2, '0'),
    DD: String(date.getDate()).padStart(2, '0'),
    HH: String(date.getHours()).padStart(2, '0'),
    mm: String(date.getMinutes()).padStart(2, '0'),
    ss: String(date.getSeconds()).padStart(2, '0'),
  }
  return fmt.replace(/YYYY|MM|DD|HH|mm|ss/g, (k) => o[k] || k)
}

/** 挂号订单状态文本 */
export function orderStatusText(s: number): string {
  const map: Record<number, string> = { 1: '待支付', 2: '已预约', 3: '已就诊', 4: '已取消' }
  return map[s] || '未知'
}

/** 时段文案 */
export function timePeriodText(p: number): string {
  const map: Record<number, string> = { 1: '上午', 2: '下午', 3: '夜间' }
  return map[p] || '全天'
}

/** 陪诊状态 */
export function accompanyStatusText(s: number): string {
  const map: Record<number, string> = { 1: '待审核', 2: '待服务', 3: '服务中', 4: '已完成', 5: '已取消' }
  return map[s] || '未知'
}
