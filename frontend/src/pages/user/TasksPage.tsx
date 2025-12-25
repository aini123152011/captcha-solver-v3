import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { tasksApi, Task } from '@/api/tasks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { formatCurrency, formatDate } from '@/lib/utils'
import { CheckCircle, XCircle, Clock, Search, RefreshCw } from 'lucide-react'

type StatusFilter = 'all' | 'pending' | 'processing' | 'ready' | 'failed'

export function TasksPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [search, setSearch] = useState('')

  const { data: tasks = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['tasks', statusFilter],
    queryFn: () => tasksApi.list({
      limit: 100,
      status: statusFilter === 'all' ? undefined : statusFilter,
    }),
    refetchInterval: 10000,
  })

  const filteredTasks = tasks.filter((task: Task) =>
    task.id.toLowerCase().includes(search.toLowerCase()) ||
    task.type.toLowerCase().includes(search.toLowerCase())
  )

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      ready: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100'}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tasks</h1>
          <p className="text-muted-foreground">View and manage your captcha solving tasks</p>
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
                placeholder="Search by ID or type..."
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

      {/* Task List */}
      <Card>
        <CardHeader>
          <CardTitle>Task History ({filteredTasks.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center py-8 text-muted-foreground">Loading...</p>
          ) : filteredTasks.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No tasks found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">Task ID</th>
                    <th className="text-left py-3 px-4 font-medium">Type</th>
                    <th className="text-left py-3 px-4 font-medium">Cost</th>
                    <th className="text-left py-3 px-4 font-medium">Created</th>
                    <th className="text-left py-3 px-4 font-medium">Token</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTasks.map((task: Task) => (
                    <tr key={task.id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(task.status)}
                          {getStatusBadge(task.status)}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <code className="text-sm bg-muted px-2 py-1 rounded">{task.id.slice(0, 8)}...</code>
                      </td>
                      <td className="py-3 px-4">{task.type}</td>
                      <td className="py-3 px-4">{formatCurrency(task.cost)}</td>
                      <td className="py-3 px-4">{formatDate(task.created_at)}</td>
                      <td className="py-3 px-4">
                        {task.token ? (
                          <code className="text-xs bg-muted px-2 py-1 rounded max-w-[200px] truncate block">
                            {task.token.slice(0, 30)}...
                          </code>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
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
