import apiClient from './client'
import type { AuthResponse, User } from '@/types'

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const { data } = await apiClient.post<AuthResponse>('/auth/jwt/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  register: async (email: string, password: string): Promise<User> => {
    const { data } = await apiClient.post<User>('/auth/register', { email, password })
    return data
  },

  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/users/me')
    return data
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/jwt/logout')
  },

  regenerateApiKey: async (): Promise<{ api_key: string }> => {
    const { data } = await apiClient.post<{ api_key: string }>('/users/me/regenerate-api-key')
    return data
  },
}
