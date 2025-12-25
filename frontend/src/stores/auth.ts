import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import { authApi } from '@/api/auth'

interface AuthState {
  token: string | null
  user: User | null
  isLoading: boolean
  error: string | null
  isAuthenticated: () => boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  setUser: (user: User) => void
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: false,
      error: null,

      isAuthenticated: () => !!get().token && !!get().user,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login(email, password)
          set({ token: response.access_token })
          await get().fetchUser()
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Login failed'
          set({ error: message, isLoading: false })
          throw error
        }
      },

      register: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          await authApi.register(email, password)
          await get().login(email, password)
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Registration failed'
          set({ error: message, isLoading: false })
          throw error
        }
      },

      logout: () => {
        set({ token: null, user: null, error: null })
      },

      fetchUser: async () => {
        try {
          const user = await authApi.getMe()
          set({ user, isLoading: false })
        } catch {
          set({ isLoading: false })
          get().logout()
        }
      },

      setUser: (user: User) => {
        set({ user })
      },

      initialize: async () => {
        const { token } = get()
        if (token && !get().user) {
          set({ isLoading: true })
          await get().fetchUser()
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          state.initialize()
        }
      },
    }
  )
)
