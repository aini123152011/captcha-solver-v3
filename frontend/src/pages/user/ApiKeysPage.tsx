import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Key, Copy, RefreshCw, Eye, EyeOff, Check } from 'lucide-react'

export function ApiKeysPage() {
  const user = useAuthStore((s) => s.user)
  const fetchUser = useAuthStore((s) => s.fetchUser)
  const [showKey, setShowKey] = useState(false)
  const [copied, setCopied] = useState(false)

  const regenerateMutation = useMutation({
    mutationFn: () => authApi.regenerateApiKey(),
    onSuccess: () => {
      fetchUser()
    },
  })

  const handleCopy = async () => {
    if (user?.api_key) {
      await navigator.clipboard.writeText(user.api_key)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleRegenerate = () => {
    if (confirm('Are you sure you want to regenerate your API key? Your existing key will stop working immediately.')) {
      regenerateMutation.mutate()
    }
  }

  const maskedKey = user?.api_key ? user.api_key.slice(0, 8) + '•'.repeat(24) + user.api_key.slice(-4) : ''

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">API Keys</h1>
        <p className="text-muted-foreground">Manage your API authentication credentials</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Your API Key
          </CardTitle>
          <CardDescription>
            Use this key to authenticate API requests. Keep it secure and never share it publicly.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  type={showKey ? 'text' : 'password'}
                  value={showKey ? (user?.api_key || '') : maskedKey}
                  readOnly
                  className="font-mono pr-20"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1/2 -translate-y-1/2"
                  onClick={() => setShowKey(!showKey)}
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <Button variant="outline" onClick={handleCopy} disabled={!user?.api_key}>
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t">
            <div>
              <p className="font-medium">Regenerate API Key</p>
              <p className="text-sm text-muted-foreground">
                Generate a new key. The current key will be invalidated immediately.
              </p>
            </div>
            <Button
              variant="destructive"
              onClick={handleRegenerate}
              disabled={regenerateMutation.isPending}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${regenerateMutation.isPending ? 'animate-spin' : ''}`} />
              Regenerate
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* API Usage Guide */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Start Guide</CardTitle>
          <CardDescription>How to use the API</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">1. Create a Task</h4>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
{`curl -X POST https://api.example.com/createTask \\
  -H "Content-Type: application/json" \\
  -d '{
    "clientKey": "${user?.api_key?.slice(0, 8) || 'YOUR_API_KEY'}...",
    "task": {
      "type": "RecaptchaV2TaskProxyless",
      "websiteURL": "https://example.com",
      "websiteKey": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
    }
  }'`}
            </pre>
          </div>

          <div>
            <h4 className="font-medium mb-2">2. Get Task Result</h4>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
{`curl -X POST https://api.example.com/getTaskResult \\
  -H "Content-Type: application/json" \\
  -d '{
    "clientKey": "${user?.api_key?.slice(0, 8) || 'YOUR_API_KEY'}...",
    "taskId": "task-uuid-here"
  }'`}
            </pre>
          </div>

          <div>
            <h4 className="font-medium mb-2">3. Check Balance</h4>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
{`curl -X POST https://api.example.com/getBalance \\
  -H "Content-Type: application/json" \\
  -d '{
    "clientKey": "${user?.api_key?.slice(0, 8) || 'YOUR_API_KEY'}..."
  }'`}
            </pre>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
