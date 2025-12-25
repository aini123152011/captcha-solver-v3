import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth'
import { tasksApi } from '@/api/tasks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Activity, CheckCircle, XCircle, Clock } from 'lucide-react'

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks', 'recent'],
    queryFn: () => tasksApi.list({ limit: 10 }),
    refetchInterval: 30000,
  })

  const stats = {
    total: tasks.length,
    success: tasks.filter((t) => t.status === 'ready').length,
    failed: tasks.filter((t) => t.status === 'failed').length,
    pending: tasks.filter((t) => t.status === 'pending' || t.status === 'processing').length,
  }

  const successRate = stats.total > 0 ? ((stats.success / stats.total) * 100).toFixed(1) : '0'

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back, {user?.email}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Balance</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(user?.balance ?? 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pending}</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Tasks */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Tasks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tasks.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No tasks yet</p>
            ) : (
              tasks.slice(0, 5).map((task) => (
                <div key={task.id} className="flex items-center justify-between border-b pb-4 last:border-0">
                  <div className="flex items-center gap-4">
                    {task.status === 'ready' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : task.status === 'failed' ? (
                      <XCircle className="h-5 w-5 text-red-500" />
                    ) : (
                      <Clock className="h-5 w-5 text-yellow-500" />
                    )}
                    <div>
                      <p className="font-medium">{task.type}</p>
                      <p className="text-sm text-muted-foreground">{task.id.slice(0, 8)}...</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(task.cost)}</p>
                    <p className="text-sm text-muted-foreground">{formatDate(task.created_at)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
