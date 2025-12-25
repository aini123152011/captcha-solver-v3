import apiClient from './client'

export interface Transaction {
  id: number
  user_id: string
  type: string
  amount: number
  balance_after: number
  task_id: string | null
  reference: string | null
  description: string | null
  created_at: string
}

export const billingApi = {
  getTransactions: async (params?: { limit?: number; offset?: number }): Promise<Transaction[]> => {
    const { data } = await apiClient.get<Transaction[]>('/api/v1/transactions', { params })
    return data
  },

  createDeposit: async (amount: number): Promise<{ checkout_url: string }> => {
    const { data } = await apiClient.post<{ checkout_url: string }>('/api/v1/deposit', { amount })
    return data
  },
}
