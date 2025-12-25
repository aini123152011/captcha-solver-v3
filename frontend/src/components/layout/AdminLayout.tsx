import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Users, History, DollarSign, ArrowLeft, Settings } from 'lucide-react'

const navItems = [
  { to: '/admin/users', label: 'Users', icon: Users },
  { to: '/admin/tasks', label: 'Tasks', icon: History },
  { to: '/admin/finance', label: 'Finance', icon: DollarSign },
]

export function AdminLayout() {
  const location = useLocation()
  const user = useAuthStore((s) => s.user)

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card">
        <div className="p-6">
          <h1 className="text-xl font-bold">Admin Panel</h1>
          <p className="text-sm text-muted-foreground">{user?.email}</p>
        </div>
        <Separator />
        <div className="p-4">
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
        <div className="p-4">
          <Link to="/portal/dashboard">
            <Button variant="ghost" className="w-full justify-start">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Portal
            </Button>
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 bg-muted/30">
        <Outlet />
      </main>
    </div>
  )
}
