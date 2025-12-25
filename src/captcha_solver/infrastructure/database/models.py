"""SQLAlchemy ORM 模型"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, Boolean, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from captcha_solver.domain.value_objects import PaymentStatus, TaskStatus, TaskType, TransactionType
from .connection import Base


def _enum_values(enum_cls):
    """返回枚举值列表，用于 SQLAlchemy Enum 的 values_callable 参数"""
    return [member.value for member in enum_cls]


class UserModel(Base):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # API Key (哈希存储)
    hashed_api_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    api_key_prefix: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # 余额 (使用 Numeric 精确存储)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"), nullable=False)

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    tasks: Mapped[list["TaskModel"]] = relationship(back_populates="user", lazy="dynamic")
    transactions: Mapped[list["TransactionModel"]] = relationship(back_populates="user", lazy="dynamic")


class TaskModel(Base):
    """任务表"""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)

    # 任务信息
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, values_callable=_enum_values, name="tasktype"),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, values_callable=_enum_values, name="taskstatus"),
        default=TaskStatus.PENDING,
        index=True,
        nullable=False,
    )

    # 网站信息
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    website_key: Mapped[str] = mapped_column(String(100), nullable=False)
    website_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_enterprise: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 结果
    token: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"), nullable=False)

    # 错误信息
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_desc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    user: Mapped["UserModel"] = relationship(back_populates="tasks")


class TransactionModel(Base):
    """交易表"""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)

    # 交易信息
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, values_callable=_enum_values, name="transactiontype"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    # 幂等键 (用于防止重复交易)
    reference_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(32), nullable=False)

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    user: Mapped["UserModel"] = relationship(back_populates="transactions")

    # 唯一约束：同一 reference_id + reference_type 只能有一条记录 (幂等)
    __table_args__ = (
        UniqueConstraint("reference_id", "reference_type", name="uq_transactions_ref"),
    )


class DeadLetterTaskModel(Base):
    """死信任务表 (用于存储失败的任务)"""

    __tablename__ = "dead_letter_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
