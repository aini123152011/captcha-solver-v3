"""实体 - User 聚合根"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from ..value_objects import Money


@dataclass
class User:
    """用户聚合根"""

    id: UUID
    email: str
    hashed_password: str
    hashed_api_key: str | None = None
    api_key_prefix: str | None = None  # 用于显示，如 "sk_...abc"
    balance: Decimal = Decimal("0")
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: datetime | None = None

    @classmethod
    def create(
        cls,
        email: str,
        hashed_password: str,
        hashed_api_key: str | None = None,
        api_key_prefix: str | None = None,
    ) -> "User":
        """创建新用户"""
        return cls(
            id=uuid4(),
            email=email,
            hashed_password=hashed_password,
            hashed_api_key=hashed_api_key,
            api_key_prefix=api_key_prefix,
        )

    def can_afford(self, amount: Decimal) -> bool:
        """检查是否有足够余额"""
        return self.balance >= amount

    def get_balance_as_money(self) -> Money:
        """获取余额 Money 对象"""
        return Money(self.balance)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id
