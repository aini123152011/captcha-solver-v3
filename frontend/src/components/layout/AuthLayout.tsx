import { Outlet } from 'react-router-dom'

export function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/50">
      <div className="w-full max-w-md p-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold">Captcha Solver</h1>
          <p className="text-muted-foreground mt-2">reCAPTCHA v2 自动识别服务</p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
