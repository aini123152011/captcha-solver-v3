# Captcha Solver v3.0

reCAPTCHA v2 自动识别服务 - 2captcha 兼容 API

## 快速开始

### Docker 部署 (推荐)

```bash
# 克隆项目
git clone https://github.com/aini123152011/captcha-solver-v3.git
cd captcha-solver-v3

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 SECRET_KEY 和 API_KEY_PEPPER

# 启动服务
docker compose up -d

# 数据库迁移
docker compose exec api alembic upgrade head
```

### 本地开发

#### 1. 环境准备

**macOS:**
```bash
brew install postgresql redis ffmpeg
brew services start postgresql
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql redis-server ffmpeg
sudo systemctl start postgresql redis
```

#### 2. 安装项目

```bash
# 克隆项目
git clone https://github.com/aini123152011/captcha-solver-v3.git
cd captcha-solver-v3

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 安装 Playwright 浏览器
playwright install chromium
playwright install-deps  # Linux 需要
```

#### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/captcha_solver
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-at-least-32-characters
API_KEY_PEPPER=your-pepper-key-at-least-32-characters
BROWSER_HEADLESS=true  # 设为 false 可看到浏览器执行过程
```

#### 4. 初始化数据库

```bash
# 创建数据库
createdb captcha_solver

# 运行迁移
alembic upgrade head
```

#### 5. 启动服务

需要启动 3 个服务 (建议使用 3 个终端)：

**终端 1 - 后端 API:**
```bash
source .venv/bin/activate
uvicorn captcha_solver.api.main:app --reload --port 8000
```

**终端 2 - Worker (处理验证码):**
```bash
source .venv/bin/activate
python -m arq captcha_solver.worker.main.WorkerSettings
```

**终端 3 - 前端 (可选):**
```bash
cd frontend
npm install
npm run dev
```

#### 6. 访问服务

| 服务 | 地址 |
|------|------|
| 后端 API 文档 | http://localhost:8000/docs |
| 前端界面 | http://localhost:3000 |
| Admin 后台 | http://localhost:8000/admin |

## API 使用

### 用户注册与认证

```bash
# 注册用户
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# 登录获取 JWT Token
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPass123"

# 生成 API Key (需要 JWT Token)
curl -X POST http://localhost:8000/users/me/regenerate-api-key \
  -H "Authorization: Bearer <your-jwt-token>"
```

### 2captcha 兼容 API

```bash
# 创建任务
curl -X POST http://localhost:8000/api/createTask \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "YOUR_API_KEY",
    "task": {
      "type": "RecaptchaV2Task",
      "websiteURL": "https://example.com",
      "websiteKey": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
    }
  }'

# 获取结果 (轮询直到 status 为 ready)
curl -X POST http://localhost:8000/api/getTaskResult \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "YOUR_API_KEY",
    "taskId": "TASK_ID"
  }'

# 获取余额
curl -X POST http://localhost:8000/api/getBalance \
  -H "Content-Type: application/json" \
  -d '{"clientKey": "YOUR_API_KEY"}'
```

### 支持的任务类型

| 类型 | 说明 |
|------|------|
| `RecaptchaV2Task` | reCAPTCHA v2 标准版 |
| `RecaptchaV2TaskProxyless` | reCAPTCHA v2 无代理版 |
| `RecaptchaV2TaskInvisible` | reCAPTCHA v2 隐形版 |

## 项目结构

```
src/captcha_solver/
├── domain/          # 领域层 (实体、值对象、接口)
├── application/     # 应用层 (服务、用例)
├── infrastructure/  # 基础设施层 (数据库、缓存、队列)
├── api/             # API 层 (路由、中间件)
├── worker/          # Worker 层 (任务消费)
└── config/          # 配置

frontend/            # React 前端
├── src/
│   ├── api/         # API 客户端
│   ├── components/  # UI 组件
│   ├── pages/       # 页面
│   └── stores/      # 状态管理
```

## 技术栈

**后端:**
- Python 3.12+
- FastAPI + FastAPI-Users
- PostgreSQL + SQLAlchemy 2.0
- Redis + Arq (任务队列)
- Playwright (浏览器自动化)
- Whisper (语音识别)

**前端:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Zustand (状态管理)

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接串 | - |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 密钥 (≥32字符) | - |
| `API_KEY_PEPPER` | API Key 加密盐 (≥32字符) | - |
| `BROWSER_HEADLESS` | 无头浏览器模式 | `true` |
| `BROWSER_POOL_SIZE` | 浏览器池大小 | `5` |
| `PRICE_PER_1000` | 每 1000 次价格 | `2.99` |

## License

MIT
