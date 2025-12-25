"""交易仓储实现"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.domain.entities.transaction import Transaction
from ..models import TransactionModel


class TransactionRepository:
    """交易仓储"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, transaction: Transaction) -> Transaction:
        """保存交易记录 (不 commit，由调用方控制事务)"""
        model = self._to_model(transaction)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def save_idempotent(self, transaction: Transaction) -> bool:
        """
        幂等保存交易 (不 commit，由调用方控制事务)

        使用 flush 触发唯一约束检查
        返回 True 表示新建，False 表示已存在
        """
        try:
            model = self._to_model(transaction)
            self.session.add(model)
            await self.session.flush()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False

    async def get_by_reference(
        self, reference_id: str, reference_type: str
    ) -> Transaction | None:
        """通过引用获取交易"""
        result = await self.session.execute(
            select(TransactionModel).where(
                TransactionModel.reference_id == reference_id,
                TransactionModel.reference_type == reference_type,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """获取用户交易列表"""
        result = await self.session.execute(
            select(TransactionModel)
            .where(TransactionModel.user_id == user_id)
            .order_by(TransactionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def list_recent(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """获取最近交易列表"""
        result = await self.session.execute(
            select(TransactionModel)
            .order_by(TransactionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: TransactionModel) -> Transaction:
        """模型转实体"""
        return Transaction(
            id=model.id,
            user_id=model.user_id,
            type=model.type,
            amount=model.amount,
            balance_after=model.balance_after,
            reference_id=model.reference_id,
            reference_type=model.reference_type,
            description=model.description,
            created_at=model.created_at,
        )

    def _to_model(self, entity: Transaction) -> TransactionModel:
        """实体转模型"""
        return TransactionModel(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type,
            amount=entity.amount,
            balance_after=entity.balance_after,
            reference_id=entity.reference_id,
            reference_type=entity.reference_type,
            description=entity.description,
            created_at=entity.created_at,
        )
