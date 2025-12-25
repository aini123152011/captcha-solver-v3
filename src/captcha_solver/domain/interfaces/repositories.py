"""领域接口 - Repository 抽象"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from ..entities.task import Task
from ..entities.transaction import Transaction
from ..entities.user import User
from ..value_objects import TaskStatus


class IUserRepository(Protocol):
    """用户仓储接口"""

    async def get_by_id(self, user_id: UUID) -> User | None:
        """通过 ID 获取用户"""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """通过邮箱获取用户"""
        ...

    async def get_by_hashed_api_key(self, hashed_key: str) -> User | None:
        """通过哈希 API Key 获取用户"""
        ...

    async def save(self, user: User) -> User:
        """保存用户"""
        ...

    async def update_balance_atomic(
        self, user_id: UUID, amount: Decimal
    ) -> Decimal | None:
        """原子更新余额，返回更新后余额，余额不足返回 None"""
        ...


class ITaskRepository(Protocol):
    """任务仓储接口"""

    async def get_by_id(self, task_id: UUID) -> Task | None:
        """通过 ID 获取任务"""
        ...

    async def get_by_id_and_user(self, task_id: UUID, user_id: UUID) -> Task | None:
        """通过 ID 和用户 ID 获取任务"""
        ...

    async def save(self, task: Task) -> Task:
        """保存任务"""
        ...

    async def update_status(
        self,
        task_id: UUID,
        status: TaskStatus,
        token: str | None = None,
        error_code: str | None = None,
        error_desc: str | None = None,
    ) -> bool:
        """更新任务状态"""
        ...

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        """获取用户任务列表"""
        ...


class ITransactionRepository(Protocol):
    """交易仓储接口"""

    async def save(self, transaction: Transaction) -> Transaction:
        """保存交易记录"""
        ...

    async def save_idempotent(self, transaction: Transaction) -> bool:
        """幂等保存交易（返回 True 表示新建，False 表示已存在）"""
        ...

    async def get_by_reference(
        self, reference_id: str, reference_type: str
    ) -> Transaction | None:
        """通过引用获取交易"""
        ...

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """获取用户交易列表"""
        ...
