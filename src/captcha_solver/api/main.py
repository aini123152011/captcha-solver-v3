"""FastAPI 主入口"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from captcha_solver.config import settings
from captcha_solver.infrastructure.database.connection import create_db_and_tables
from captcha_solver.api.deps import close_arq_redis
from captcha_solver.api.v1.routes import task as task_routes
from captcha_solver.api.v1.routes import user_routes, admin_routes
from captcha_solver.api.auth.users import fastapi_users, auth_backend
from captcha_solver.api.auth.schemas import UserRead, UserCreate, UserUpdate


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    logger.info("Starting Captcha Solver API v3.0...")

    # 开发环境：自动创建表
    if settings.environment == "development":
        await create_db_and_tables()
        logger.info("Database tables created (development mode)")

    yield

    # 关闭
    logger.info("Shutting down...")
    await close_arq_redis()


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="Captcha Solver API",
        description="reCAPTCHA v2 自动识别服务 - 2captcha 兼容 API",
        version="3.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 2captcha 兼容 API 路由
    app.include_router(task_routes.router, prefix="/api", tags=["2captcha API"])

    # 注册 FastAPI Users 认证路由
    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="/auth/jwt",
        tags=["Auth"],
    )
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/auth",
        tags=["Auth"],
    )
    app.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/users",
        tags=["Users"],
    )

    # 用户扩展路由 (regenerate-api-key, tasks, transactions, deposit)
    app.include_router(user_routes.router, tags=["User"])

    # 管理员路由
    app.include_router(admin_routes.router, tags=["Admin"])

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "3.0.0"}

    return app


app = create_app()


def run():
    """运行应用"""
    import uvicorn
    uvicorn.run(
        "captcha_solver.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
