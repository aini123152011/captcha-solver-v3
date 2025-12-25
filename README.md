# Captcha Solver v3.0

reCAPTCHA v2 自动识别服务 - 2captcha 兼容 API

## 快速开始

### Docker 部署 (推荐)

```bash
# 克隆项目
git clone <repo-url>
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

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 安装 Playwright 浏览器
playwright install chromium

# 启动服务
uvicorn captcha_solver.api.main:app --reload
```

## API 文档

服务启动后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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

# 获取结果
curl -X POST http://localhost:8000/api/getTaskResult \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "YOUR_API_KEY",
    "taskId": "TASK_ID"
  }'
```

## 项目结构

```
src/captcha_solver/
├── domain/          # 领域层 (实体、值对象、接口)
├── application/     # 应用层 (服务、用例)
├── infrastructure/  # 基础设施层 (数据库、缓存、队列)
├── api/             # API 层 (路由、中间件)
├── worker/          # Worker 层 (任务消费)
└── config/          # 配置
```

## 技术栈

- Python 3.12+
- FastAPI
- PostgreSQL + SQLAlchemy 2.0
- Redis + Arq
- Playwright
- Whisper (ASR)

## License

MIT
