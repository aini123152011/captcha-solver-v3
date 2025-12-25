# syntax=docker/dockerfile:1

# ============================================
# Base 镜像
# ============================================
FROM python:3.12-slim AS base

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装 Playwright 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


# ============================================
# Backend 镜像
# ============================================
FROM base AS backend-base

# 复制项目文件
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# 安装 Python 依赖
RUN pip install --no-cache-dir .

# 安装 Playwright 浏览器
RUN playwright install chromium

# 创建数据目录
RUN mkdir -p /app/data

# 环境变量
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1


# ============================================
# API 镜像
# ============================================
FROM backend-base AS api

EXPOSE 8000

CMD ["uvicorn", "captcha_solver.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ============================================
# Worker 镜像
# ============================================
FROM backend-base AS worker

CMD ["python", "-m", "arq", "captcha_solver.worker.main.WorkerSettings"]
