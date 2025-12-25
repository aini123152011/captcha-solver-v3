import apiClient from './client'

export interface AdminUser {
  id: string
  email: string
  balance: number
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface AdminTask {
  id: string
  user_id: string
  user_email?: string
  type: string
  status: string
  cost: number
  token?: string
  error?: string
  created_at: string
  updated_at?: string
}

export interface FinanceStats {
  total_revenue: number
  total_deposits: number
  total_refunds: number
  net_balance: number
  deposit_count: number
  refund_count: number
  today_revenue: number
  today_tasks: number
  today_success_rate: number
  week_revenue: number
  week_tasks: number
  week_new_users: number
  month_revenue: number
  month_tasks: number
  month_active_users: number
}

export const adminApi = {
  async getUsers(): Promise<AdminUser[]> {
    const response = await apiClient.get('/admin/users')
    return response.data
  },

  async updateUser(userId: string, data: Partial<{ is_active: boolean; is_superuser: boolean }>): Promise<AdminUser> {
    const response = await apiClient.patch(`/admin/users/${userId}`, data)
    return response.data
  },

  async getTasks(params?: { limit?: number; status?: string }): Promise<AdminTask[]> {
    const response = await apiClient.get('/admin/tasks', { params })
    return response.data
  },

  async getFinanceStats(): Promise<FinanceStats> {
    const response = await apiClient.get('/admin/finance/stats')
    return response.data
  },

  async getRecentTransactions(): Promise<any[]> {
    const response = await apiClient.get('/admin/finance/transactions')
    return response.data
  },
}
