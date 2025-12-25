import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { formatCurrency } from '@/lib/utils'
import { LayoutDashboard, Wallet, History, Key, LogOut, Settings } from 'lucide-react'

const navItems = [
  { to: '/portal/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/portal/wallet', label: 'Wallet', icon: Wallet },
  { to: '/portal/tasks', label: 'Tasks', icon: History },
  { to: '/portal/api-keys', label: 'API Keys', icon: Key },
]

export function PortalLayout() {
  const location = useLocation()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card">
        <div className="p-6">
          <h1 className="text-xl font-bold">Captcha Solver</h1>
          <p className="text-sm text-muted-foreground">{user?.email}</p>
        </div>
        <Separator />
        <div className="p-4">
          <div className="rounded-lg bg-muted p-4 mb-4">
            <p className="text-sm text-muted-foreground">Balance</p>
            <p className="text-2xl font-bold">{formatCurrency(user?.balance ?? 0)}</p>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link key={item.to} to={item.to}>
                <Button
                  variant={location.pathname === item.to ? 'secondary' : 'ghost'}
                  className="w-full justify-start"
                >
                  <item.icon className="mr-2 h-4 w-4" />
                  {item.label}
                </Button>
              </Link>
            ))}
          </nav>
        </div>
        <Separator />
        <div className="p-4 space-y-1">
          {user?.is_superuser && (
            <Link to="/admin">
              <Button variant="ghost" className="w-full justify-start">
                <Settings className="mr-2 h-4 w-4" />
                Admin Panel
              </Button>
            </Link>
          )}
          <Button variant="ghost" className="w-full justify-start text-destructive" onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 bg-muted/30">
        <Outlet />
      </main>
    </div>
  )
}
