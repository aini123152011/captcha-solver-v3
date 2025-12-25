import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import { useAuthStore } from '@/stores/auth'

// Layouts
import { AuthLayout } from '@/components/layout/AuthLayout'
import { PortalLayout } from '@/components/layout/PortalLayout'
import { AdminLayout } from '@/components/layout/AdminLayout'

// Public Pages
import { LoginPage } from '@/pages/public/LoginPage'
import { RegisterPage } from '@/pages/public/RegisterPage'

// User Portal Pages
import { DashboardPage } from '@/pages/user/DashboardPage'
import { WalletPage } from '@/pages/user/WalletPage'
import { TasksPage } from '@/pages/user/TasksPage'
import { ApiKeysPage } from '@/pages/user/ApiKeysPage'

// Admin Pages
import { AdminUsersPage } from '@/pages/admin/AdminUsersPage'
import { AdminTasksPage } from '@/pages/admin/AdminTasksPage'
import { AdminFinancePage } from '@/pages/admin/AdminFinancePage'

function ProtectedRoute({ children, requireAdmin = false }: { children: React.ReactNode; requireAdmin?: boolean }) {
  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const isLoading = useAuthStore((s) => s.isLoading)

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && !user?.is_superuser) {
    return <Navigate to="/portal/dashboard" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <>
      <Routes>
        {/* Public Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* User Portal Routes */}
        <Route
          path="/portal"
          element={
            <ProtectedRoute>
              <PortalLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="wallet" element={<WalletPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="api-keys" element={<ApiKeysPage />} />
        </Route>

        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="users" replace />} />
          <Route path="users" element={<AdminUsersPage />} />
          <Route path="tasks" element={<AdminTasksPage />} />
          <Route path="finance" element={<AdminFinancePage />} />
        </Route>

        {/* Default Redirect */}
        <Route path="/" element={<Navigate to="/portal/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/portal/dashboard" replace />} />
      </Routes>
      <Toaster />
    </>
  )
}
