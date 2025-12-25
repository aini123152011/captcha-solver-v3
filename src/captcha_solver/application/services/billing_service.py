"""计费服务 - 处理余额和交易"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.domain.entities.transaction import Transaction
from captcha_solver.domain.exceptions import InsufficientBalanceError, RefundAlreadyProcessedError
from captcha_solver.infrastructure.database.repositories.transaction_repo import TransactionRepository
from captcha_solver.infrastructure.database.repositories.user_repo import UserRepository


class BillingService:
    """计费服务"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.tx_repo = TransactionRepository(session)

    async def deduct_balance(
        self,
        user_id: UUID,
        amount: Decimal,
        task_id: str,
        description: str | None = None,
        auto_commit: bool = False,
    ) -> Decimal:
        """
        扣除余额

        使用原子操作，返回扣除后余额
        auto_commit=False 时不提交，由调用方控制事务
        """
        # 原子扣费
        new_balance = await self.user_repo.update_balance_atomic(
            user_id, -abs(amount)
        )

        if new_balance is None:
            raise InsufficientBalanceError(float(amount), 0.0)

        # 记录交易
        transaction = Transaction.create_deduct(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            task_id=task_id,
            description=description or f"Task {task_id[:8]}...",
        )
        await self.tx_repo.save(transaction)

        if auto_commit:
            await self.session.commit()

        return new_balance

    async def refund(
        self,
        user_id: UUID,
        amount: Decimal,
        task_id: str,
        description: str | None = None,
    ) -> Decimal:
        """
        退款 (幂等操作)

        顺序：先插入交易记录（触发唯一约束检查），再更新余额
        整体在一个事务中完成
        """
        # 创建退款交易记录
        # 注意：此时 balance_after 是临时值，稍后更新
        transaction = Transaction.create_refund(
            user_id=user_id,
            amount=amount,
            balance_after=Decimal("0"),  # 临时值
            task_id=task_id,
            description=description or f"Refund for task {task_id[:8]}...",
        )

        # 先尝试插入交易记录 (触发唯一约束检查)
        # 如果已存在，flush 会抛出 IntegrityError
        inserted = await self.tx_repo.save_idempotent(transaction)
        if not inserted:
            raise RefundAlreadyProcessedError(task_id)

        # 交易记录插入成功，更新余额
        new_balance = await self.user_repo.update_balance_atomic(
            user_id, abs(amount)
        )

        if new_balance is None:
            await self.session.rollback()
            raise ValueError(f"User not found: {user_id}")

        # 提交整个事务
        await self.session.commit()

        return new_balance

    async def deposit(
        self,
        user_id: UUID,
        amount: Decimal,
        payment_id: str,
        description: str | None = None,
    ) -> Decimal:
        """充值"""
        # 原子加款
        new_balance = await self.user_repo.update_balance_atomic(
            user_id, abs(amount)
        )

        if new_balance is None:
            raise ValueError(f"User not found: {user_id}")

        # 记录交易
        transaction = Transaction.create_deposit(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            payment_id=payment_id,
            description=description or f"Deposit from payment {payment_id[:8]}...",
        )
        await self.tx_repo.save(transaction)

        # 提交事务
        await self.session.commit()

        return new_balance

    async def get_balance(self, user_id: UUID) -> Decimal:
        """获取余额"""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        return user.balance
