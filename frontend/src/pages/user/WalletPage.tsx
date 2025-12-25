import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth'
import { billingApi, Transaction } from '@/api/billing'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Wallet, ArrowUpRight, ArrowDownRight } from 'lucide-react'

export function WalletPage() {
  const user = useAuthStore((s) => s.user)
  const fetchUser = useAuthStore((s) => s.fetchUser)
  const queryClient = useQueryClient()
  const [amount, setAmount] = useState('')

  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => billingApi.getTransactions(),
  })

  const depositMutation = useMutation({
    mutationFn: (amount: number) => billingApi.createDeposit(amount),
    onSuccess: (data) => {
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      }
    },
  })

  const handleDeposit = (e: React.FormEvent) => {
    e.preventDefault()
    const value = parseFloat(amount)
    if (value >= 1) {
      depositMutation.mutate(value)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Wallet</h1>
        <p className="text-muted-foreground">Manage your balance and transactions</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Balance Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-5 w-5" />
              Current Balance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{formatCurrency(user?.balance ?? 0)}</p>
          </CardContent>
        </Card>

        {/* Deposit Card */}
        <Card>
          <CardHeader>
            <CardTitle>Add Funds</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleDeposit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Amount (USD)</Label>
                <Input
                  id="amount"
                  type="number"
                  min="1"
                  step="0.01"
                  placeholder="10.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                {[5, 10, 25, 50].map((preset) => (
                  <Button
                    key={preset}
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setAmount(preset.toString())}
                  >
                    ${preset}
                  </Button>
                ))}
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={depositMutation.isPending || !amount || parseFloat(amount) < 1}
              >
                {depositMutation.isPending ? 'Processing...' : 'Deposit with Stripe'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center py-8 text-muted-foreground">Loading...</p>
          ) : transactions.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No transactions yet</p>
          ) : (
            <div className="space-y-4">
              {transactions.map((tx: Transaction) => (
                <div key={tx.id} className="flex items-center justify-between border-b pb-4 last:border-0">
                  <div className="flex items-center gap-4">
                    {tx.amount > 0 ? (
                      <ArrowDownRight className="h-5 w-5 text-green-500" />
                    ) : (
                      <ArrowUpRight className="h-5 w-5 text-red-500" />
                    )}
                    <div>
                      <p className="font-medium capitalize">{tx.type}</p>
                      <p className="text-sm text-muted-foreground">{tx.description || tx.reference}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium ${tx.amount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {tx.amount > 0 ? '+' : ''}{formatCurrency(tx.amount)}
                    </p>
                    <p className="text-sm text-muted-foreground">{formatDate(tx.created_at)}</p>
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
