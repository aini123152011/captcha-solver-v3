import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/api/admin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency } from '@/lib/utils'
import { DollarSign, TrendingUp, TrendingDown, CreditCard, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function AdminFinancePage() {
  const { data: stats, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['admin', 'finance'],
    queryFn: () => adminApi.getFinanceStats(),
  })

  const { data: recentTransactions = [] } = useQuery({
    queryKey: ['admin', 'transactions'],
    queryFn: () => adminApi.getRecentTransactions(),
  })

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Financial Dashboard</h1>
          <p className="text-muted-foreground">Revenue, deposits, and financial metrics</p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : formatCurrency(stats?.total_revenue ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">From task completions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Deposits</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {isLoading ? '...' : formatCurrency(stats?.total_deposits ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">{stats?.deposit_count ?? 0} transactions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Refunds</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {isLoading ? '...' : formatCurrency(stats?.total_refunds ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">{stats?.refund_count ?? 0} refunds issued</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Net Balance</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : formatCurrency(stats?.net_balance ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">Current system liability</p>
          </CardContent>
        </Card>
      </div>

      {/* Period Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Today</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Revenue</span>
              <span className="font-medium">{formatCurrency(stats?.today_revenue ?? 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tasks</span>
              <span className="font-medium">{stats?.today_tasks ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Success Rate</span>
              <span className="font-medium">{stats?.today_success_rate ?? 0}%</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">This Week</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Revenue</span>
              <span className="font-medium">{formatCurrency(stats?.week_revenue ?? 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tasks</span>
              <span className="font-medium">{stats?.week_tasks ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">New Users</span>
              <span className="font-medium">{stats?.week_new_users ?? 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">This Month</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Revenue</span>
              <span className="font-medium">{formatCurrency(stats?.month_revenue ?? 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tasks</span>
              <span className="font-medium">{stats?.month_tasks ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Active Users</span>
              <span className="font-medium">{stats?.month_active_users ?? 0}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          {recentTransactions.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No transactions</p>
          ) : (
            <div className="space-y-4">
              {recentTransactions.slice(0, 10).map((tx: any) => (
                <div key={tx.id} className="flex items-center justify-between border-b pb-4 last:border-0">
                  <div>
                    <p className="font-medium capitalize">{tx.type}</p>
                    <p className="text-sm text-muted-foreground">{tx.user_email}</p>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium ${tx.amount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {tx.amount > 0 ? '+' : ''}{formatCurrency(tx.amount)}
                    </p>
                    <p className="text-xs text-muted-foreground">{tx.reference}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
