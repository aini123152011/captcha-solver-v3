"""用户仓储实现"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.domain.entities.user import User
from ..models import UserModel


class UserRepository:
    """用户仓储"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """通过 ID 获取用户"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        """通过邮箱获取用户"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_hashed_api_key(self, hashed_key: str) -> User | None:
        """通过哈希 API Key 获取用户"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.hashed_api_key == hashed_key)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, user: User) -> User:
        """保存用户 (不 commit，由调用方控制事务)"""
        model = self._to_model(user)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        """获取用户列表"""
        result = await self.session.execute(
            select(UserModel)
            .order_by(UserModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def list_by_ids(self, user_ids: list[UUID]) -> list[User]:
        """通过 ID 列表获取用户"""
        if not user_ids:
            return []
        result = await self.session.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update_flags(
        self,
        user_id: UUID,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> User | None:
        """更新用户状态"""
        values: dict = {}
        if is_active is not None:
            values["is_active"] = is_active
        if is_superuser is not None:
            values["is_superuser"] = is_superuser
        if not values:
            return await self.get_by_id(user_id)

        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**values)
            .returning(UserModel)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_api_key(
        self,
        user_id: UUID,
        hashed_api_key: str,
        api_key_prefix: str,
    ) -> User | None:
        """更新用户 API Key"""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                hashed_api_key=hashed_api_key,
                api_key_prefix=api_key_prefix,
            )
            .returning(UserModel)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_balance_atomic(
        self, user_id: UUID, amount: Decimal
    ) -> Decimal | None:
        """
        原子更新余额

        使用 UPDATE ... SET balance = balance + amount WHERE balance + amount >= 0
        返回更新后余额，余额不足返回 None
        """
        if amount < 0:
            # 扣费：检查余额是否足够
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .where(UserModel.balance >= abs(amount))
                .values(balance=UserModel.balance + amount)
                .returning(UserModel.balance)
            )
        else:
            # 增加余额
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(balance=UserModel.balance + amount)
                .returning(UserModel.balance)
            )

        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            # 余额不足或用户不存在
            return None

        # 不 commit，由调用方控制事务
        return row[0]

    def _to_entity(self, model: UserModel) -> User:
        """模型转实体"""
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            hashed_api_key=model.hashed_api_key,
            api_key_prefix=model.api_key_prefix,
            balance=model.balance,
            is_active=model.is_active,
            is_superuser=model.is_superuser,
            is_verified=model.is_verified,
            created_at=model.created_at,
            last_login_at=model.last_login_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """实体转模型"""
        return UserModel(
            id=entity.id,
            email=entity.email,
            hashed_password=entity.hashed_password,
            hashed_api_key=entity.hashed_api_key,
            api_key_prefix=entity.api_key_prefix,
            balance=entity.balance,
            is_active=entity.is_active,
            is_superuser=entity.is_superuser,
            is_verified=entity.is_verified,
            created_at=entity.created_at,
            last_login_at=entity.last_login_at,
        )
