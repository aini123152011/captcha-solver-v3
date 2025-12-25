import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi, AdminTask } from '@/api/admin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Search, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react'

type StatusFilter = 'all' | 'pending' | 'processing' | 'ready' | 'failed'

export function AdminTasksPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [search, setSearch] = useState('')

  const { data: tasks = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['admin', 'tasks', statusFilter],
    queryFn: () => adminApi.getTasks({
      limit: 200,
      status: statusFilter === 'all' ? undefined : statusFilter,
    }),
    refetchInterval: 15000,
  })

  const filteredTasks = tasks.filter((task: AdminTask) =>
    task.id.toLowerCase().includes(search.toLowerCase()) ||
    task.user_email?.toLowerCase().includes(search.toLowerCase()) ||
    task.type.toLowerCase().includes(search.toLowerCase())
  )

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Task Audit</h1>
          <p className="text-muted-foreground">View and audit all system tasks</p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by ID, user email, or type..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              {(['all', 'pending', 'processing', 'ready', 'failed'] as StatusFilter[]).map((status) => (
                <Button
                  key={status}
                  variant={statusFilter === status ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter(status)}
                >
                  {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tasks Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Tasks ({filteredTasks.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center py-8 text-muted-foreground">Loading...</p>
          ) : filteredTasks.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No tasks found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-3 font-medium">Status</th>
                    <th className="text-left py-3 px-3 font-medium">Task ID</th>
                    <th className="text-left py-3 px-3 font-medium">User</th>
                    <th className="text-left py-3 px-3 font-medium">Type</th>
                    <th className="text-left py-3 px-3 font-medium">Cost</th>
                    <th className="text-left py-3 px-3 font-medium">Created</th>
                    <th className="text-left py-3 px-3 font-medium">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTasks.map((task: AdminTask) => (
                    <tr key={task.id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(task.status)}
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            task.status === 'ready' ? 'bg-green-100 text-green-800' :
                            task.status === 'failed' ? 'bg-red-100 text-red-800' :
                            task.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {task.status}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <code className="text-xs bg-muted px-1 py-0.5 rounded">{task.id.slice(0, 8)}</code>
                      </td>
                      <td className="py-3 px-3">
                        <div>
                          <p className="truncate max-w-[150px]">{task.user_email || '-'}</p>
                        </div>
                      </td>
                      <td className="py-3 px-3">{task.type}</td>
                      <td className="py-3 px-3">{formatCurrency(task.cost)}</td>
                      <td className="py-3 px-3">{formatDate(task.created_at)}</td>
                      <td className="py-3 px-3">
                        {task.error ? (
                          <span className="text-red-600 truncate max-w-[200px] block" title={task.error}>
                            {task.error.slice(0, 30)}...
                          </span>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
