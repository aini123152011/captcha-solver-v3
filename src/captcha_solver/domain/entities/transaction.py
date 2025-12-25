"""实体 - Transaction"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from ..value_objects import TransactionType


@dataclass
class Transaction:
    """交易记录实体"""

    id: UUID
    user_id: UUID
    type: TransactionType
    amount: Decimal
    balance_after: Decimal
    reference_id: str  # 幂等键（如 task_id）
    reference_type: str  # 引用类型（如 "TASK"）
    description: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create_deduct(
        cls,
        user_id: UUID,
        amount: Decimal,
        balance_after: Decimal,
        task_id: str,
        description: str | None = None,
    ) -> "Transaction":
        """创建扣费交易"""
        return cls(
            id=uuid4(),
            user_id=user_id,
            type=TransactionType.DEDUCT,
            amount=-abs(amount),  # 扣费为负数
            balance_after=balance_after,
            reference_id=task_id,
            reference_type="TASK",
            description=description,
        )

    @classmethod
    def create_refund(
        cls,
        user_id: UUID,
        amount: Decimal,
        balance_after: Decimal,
        task_id: str,
        description: str | None = None,
    ) -> "Transaction":
        """创建退款交易"""
        return cls(
            id=uuid4(),
            user_id=user_id,
            type=TransactionType.REFUND,
            amount=abs(amount),  # 退款为正数
            balance_after=balance_after,
            reference_id=task_id,
            reference_type="TASK_REFUND",
            description=description,
        )

    @classmethod
    def create_deposit(
        cls,
        user_id: UUID,
        amount: Decimal,
        balance_after: Decimal,
        payment_id: str,
        description: str | None = None,
    ) -> "Transaction":
        """创建充值交易"""
        return cls(
            id=uuid4(),
            user_id=user_id,
            type=TransactionType.DEPOSIT,
            amount=abs(amount),
            balance_after=balance_after,
            reference_id=payment_id,
            reference_type="PAYMENT",
            description=description,
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id
