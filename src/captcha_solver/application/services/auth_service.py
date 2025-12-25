"""认证服务 - API Key 哈希与验证"""

import hashlib
import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.config import settings
from captcha_solver.domain.entities.user import User
from captcha_solver.domain.exceptions import InvalidApiKeyError
from captcha_solver.infrastructure.database.repositories.user_repo import UserRepository


def generate_api_key() -> str:
    """生成 API Key (64 字符十六进制)"""
    return f"sk_live_{secrets.token_hex(28)}"


def hash_api_key(api_key: str, pepper: str | None = None) -> str:
    """
    哈希 API Key

    使用 SHA256 + Pepper
    """
    if pepper is None:
        pepper = settings.api_key_pepper
    return hashlib.sha256(f"{api_key}{pepper}".encode()).hexdigest()


def get_api_key_prefix(api_key: str) -> str:
    """获取 API Key 前缀用于显示 (max 16 chars)"""
    return f"{api_key[:8]}...{api_key[-4:]}"


class AuthService:
    """认证服务"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def authenticate_by_api_key(self, api_key: str) -> User:
        """
        通过 API Key 认证

        支持 pepper 轮换：先尝试当前 pepper，失败后尝试上一个
        """
        # 尝试当前 pepper
        hashed = hash_api_key(api_key, settings.api_key_pepper)
        user = await self.user_repo.get_by_hashed_api_key(hashed)

        # 如果失败，尝试上一个 pepper（用于轮换期间）
        if user is None and settings.api_key_pepper_previous:
            hashed = hash_api_key(api_key, settings.api_key_pepper_previous)
            user = await self.user_repo.get_by_hashed_api_key(hashed)

        if user is None:
            raise InvalidApiKeyError()

        if not user.is_active:
            raise InvalidApiKeyError()

        return user

    async def regenerate_api_key(self, user_id: UUID) -> str:
        """
        重新生成 API Key

        返回新的明文 Key（仅此一次显示）
        """
        new_key = generate_api_key()
        updated = await self.user_repo.update_api_key(
            user_id=user_id,
            hashed_api_key=hash_api_key(new_key),
            api_key_prefix=get_api_key_prefix(new_key),
        )
        if updated is None:
            raise ValueError(f"User not found: {user_id}")

        return new_key

    async def create_user_with_api_key(
        self,
        email: str,
        hashed_password: str,
    ) -> tuple[User, str]:
        """
        创建用户并生成 API Key

        返回 (User, 明文 API Key)
        """
        api_key = generate_api_key()

        user = User.create(
            email=email,
            hashed_password=hashed_password,
            hashed_api_key=hash_api_key(api_key),
            api_key_prefix=get_api_key_prefix(api_key),
        )

        saved_user = await self.user_repo.save(user)
        return saved_user, api_key
