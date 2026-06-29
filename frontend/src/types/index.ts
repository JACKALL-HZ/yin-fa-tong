/** 统一 API 响应 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

/** 分页响应 */
export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ---- 认证 ----
export interface LoginRequest { username: string; password: string }
export interface RegisterRequest { username: string; password: string; nickname?: string; user_type?: number; admin_code?: string }
export interface AlipayLoginRequest { auth_code: string }
export interface SmsLoginRequest { phone: string; code: string }
export interface AdminLoginRequest { username: string; password: string }
export interface TokenResponse { access_token: string; token_type: string; user_id: number; nickname: string; user_type: number }
export interface UserInfo {
  id: number; username: string; nickname: string; user_type: number
  real_name?: string; gender?: number; id_card?: string; birthday?: string; phone?: string
  profile_complete?: boolean
}
export interface ProfileUpdate { real_name: string; gender: number; id_card: string; birthday: string; phone?: string }

// ---- 长辈绑定 ----
export interface ElderBind {
  id: number; child_uid: number; elder_name: string; elder_phone: string
  elder_id_card: string; gender: number; birthday: string; medical_card?: string
  age: number; is_elder: boolean
}

// ---- 医院四级 ----
export interface Hospital { id: number; name: string; address: string; phone: string; level: number }
export interface Department { id: number; hospital_id: number; dept_name: string; hospital_name?: string }
export interface Doctor { id: number; dept_id: number; doc_name: string; title: string; specialty: string; register_fee: number; hospital_name?: string; dept_name?: string }
export interface Schedule { id: number; doctor_id: number; work_date: string; time_period: string; normal_num: number; elder_priority_num: number; normal_remain: number; elder_remain: number; doctor_name?: string; dept_name?: string; hospital_name?: string; register_fee?: number }

// ---- 挂号 ----
export interface ReserveCreate { schedule_id: number; elder_bind_id?: number; source_type: string }
export interface ReserveOrder {
  id: number; user_id: number; schedule_id: number; queue_code: string
  queue_status: number; pay_status: number; order_status: number; source_type: string
  doctor_name?: string; dept_name?: string; hospital_name?: string
  work_date?: string; time_period?: string; time_period_text?: string
  register_fee?: number; elder_name?: string; elder_bind_id?: number
  schedule_date?: string  // 兼容旧字段
  pay_deadline?: string   // 支付截止时间（ISO 格式，待支付状态才有）
}

// ---- 候诊 ----
export interface QueueStatus { current_number: number; total_waiting: number; my_position?: number; estimated_minutes?: number }

// ---- 消息 ----
export interface Message { id: number; user_id: number; msg_type: number; msg_content: string; read_status: number; create_time: string }

// ---- 导诊 (Dify AI 增强版) ----
export interface MedicationSuggestion {
  drug_name: string
  indication: string
  dosage_note: string
  elderly_precaution: string
  contraindication: string
}

export interface GuideResult {
  dept_name: string
  score: number           // rule engine: weighted score
  matched_keywords: string[] // rule engine: matched symptom keywords
  confidence: number      // Dify AI: confidence 0-1
  reasoning: string       // Dify AI: recommendation reasoning
}

export interface GuideResponse {
  results: GuideResult[]
  input_text: string
  suggestion: string
  medications: MedicationSuggestion[]   // Dify: OTC drug suggestions
  elderly_precautions: string           // Dify: elderly-specific cautions
  emergency_flag: boolean               // Dify: emergency alert
  general_advice: string                // Dify: lifestyle advice
  engine: 'dify' | 'rule'              // which engine provided the result
}

// ---- 志愿者 ----
export interface Volunteer {
  id: number; vol_name: string; vol_phone: string; service_dept?: string
  avatar?: string; service_desc?: string; service_score: number; service_count: number; status: number
}

// ---- 陪诊 ----
export interface AccompanyOrder {
  id: number; user_id: number; elder_bind_id: number | null; elder_name?: string
  volunteer_id: number; vol_name?: string; accompany_date: string; order_status: number
  status_text: string; service_score?: number; service_comment?: string
}

// ---- 全局搜索 ----
export interface SearchResultItem {
  type: 'hospital' | 'department' | 'doctor' | 'symptom'
  id: number | string
  title: string
  subtitle: string
  extra?: {
    hospital_level?: string
    doctor_title?: string
    specialty?: string
    register_fee?: string
    dept_name?: string
    weight?: number
    route: string
  }
}

export interface SearchResponse {
  keyword: string
  total: number
  results: SearchResultItem[]
}

// ---- 提醒 ----
export interface Reminder {
  id: number; user_id: number; remind_type: string; remind_time: string
  remind_content: string; elder_bind_id: number | null; repeat_days: number; is_active: number
}

// ---- 报告 ----
export interface ReportItem {
  id: number; elder_bind_id: number; elder_name?: string; report_url: string
  interpretation?: string; create_time: string
}

export interface ReportDetail {
  id: number; elder_bind_id: number; report_url: string
  ocr_result?: { text?: string; indicators?: Record<string, number>; confidence?: number }
  interpretation?: string; create_time: string
}

export interface ReportUploadResult {
  id: number; elder_bind_id: number; report_url: string
  ocr_result?: { text?: string; indicators?: Record<string, number>; confidence?: number }
  interpretation?: string; create_time: string
}
