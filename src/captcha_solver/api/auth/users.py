"""FastAPI Users 配置"""

import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.config import settings
from captcha_solver.infrastructure.database.connection import get_async_session
from captcha_solver.infrastructure.database.models import UserModel
from captcha_solver.application.services.auth_service import generate_api_key, hash_api_key, get_api_key_prefix


class UserManager(UUIDIDMixin, BaseUserManager[UserModel, uuid.UUID]):
    """用户管理器"""

    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def on_after_register(self, user: UserModel, request: Optional[Request] = None):
        """注册后回调 - 生成 API Key"""
        # 生成 API Key
        api_key = generate_api_key()
        user.hashed_api_key = hash_api_key(api_key)
        user.api_key_prefix = get_api_key_prefix(api_key)

        # 保存到数据库
        session = self.user_db.session
        await session.commit()

        print(f"User {user.id} registered. API Key: {api_key}")

    async def on_after_forgot_password(
        self, user: UserModel, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} forgot password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: UserModel, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Token: {token}")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """获取用户数据库适配器"""
    yield SQLAlchemyUserDatabase(session, UserModel)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """获取用户管理器"""
    yield UserManager(user_db)


# JWT 策略
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=3600 * 24)  # 24 小时


# Bearer Token 传输
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# 认证后端
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPIUsers 实例
fastapi_users = FastAPIUsers[UserModel, uuid.UUID](get_user_manager, [auth_backend])

# 当前用户依赖
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
