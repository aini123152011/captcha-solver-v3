import apiClient from './client'
import type { Task, GetBalanceResponse } from '@/types'

export const tasksApi = {
  list: async (params?: { limit?: number; offset?: number; status?: string }): Promise<Task[]> => {
    const { data } = await apiClient.get<Task[]>('/api/v1/tasks', { params })
    return data
  },

  getById: async (taskId: string): Promise<Task> => {
    const { data } = await apiClient.get<Task>(`/api/v1/tasks/${taskId}`)
    return data
  },

  getBalance: async (apiKey: string): Promise<GetBalanceResponse> => {
    const { data } = await apiClient.post<GetBalanceResponse>('/api/getBalance', { clientKey: apiKey })
    return data
  },
}
