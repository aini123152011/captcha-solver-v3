// User types
export interface User {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  api_key: string | null
  balance: number
  referral_code: string | null
  created_at: string
  last_login_at: string | null
}

// Task types
export type TaskType = 'RecaptchaV2Task' | 'RecaptchaV2TaskInvisible' | 'RecaptchaV3Task' | 'HCaptchaTask'
export type TaskStatus = 'pending' | 'processing' | 'ready' | 'failed'

export interface Task {
  id: string
  user_id: string
  type: TaskType
  status: TaskStatus
  website_url: string | null
  website_key: string
  website_domain: string | null
  is_enterprise: boolean
  token: string | null
  cost: number
  error_code: string | null
  error_desc: string | null
  retry_count: number
  created_at: string
  started_at: string | null
  completed_at: string | null
}

// Transaction types
export type TransactionType = 'deposit' | 'deduct' | 'refund' | 'bonus'

export interface Transaction {
  id: number
  user_id: string
  type: TransactionType
  amount: number
  balance_after: number
  task_id: string | null
  description: string | null
  created_at: string
}

// API Response types
export interface ApiError {
  errorId: number
  errorCode: string
  errorDescription: string
}

export interface CreateTaskResponse {
  errorId: number
  errorCode?: string
  errorDescription?: string
  taskId?: string
}

export interface GetTaskResultResponse {
  errorId: number
  errorCode?: string
  errorDescription?: string
  status?: 'processing' | 'ready'
  solution?: { gRecaptchaResponse: string }
  cost?: number
  createTime?: number
  endTime?: number
}

export interface GetBalanceResponse {
  errorId: number
  errorCode?: string
  errorDescription?: string
  balance?: number
}

// Auth types
export interface LoginRequest {
  username: string // email
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

// Stats types
export interface DashboardStats {
  balance: number
  totalTasks: number
  successRate: number
  recentTasks: Task[]
  usageByDay: { date: string; count: number }[]
}
