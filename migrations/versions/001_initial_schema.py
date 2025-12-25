"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("hashed_api_key", sa.String(64), unique=True, nullable=True, index=True),
        sa.Column("api_key_prefix", sa.String(16), nullable=True),
        sa.Column("balance", sa.Numeric(12, 4), nullable=False, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )

    # Tasks table
    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("type", sa.Enum("RecaptchaV2Task", "RecaptchaV2TaskInvisible", "RecaptchaV3Task", "HCaptchaTask", name="tasktype"), nullable=False),
        sa.Column("status", sa.Enum("pending", "processing", "ready", "failed", name="taskstatus"), nullable=False, default="pending", index=True),
        sa.Column("website_url", sa.String(2048), nullable=True),
        sa.Column("website_key", sa.String(100), nullable=False),
        sa.Column("website_domain", sa.String(255), nullable=True),
        sa.Column("is_enterprise", sa.Boolean(), nullable=False, default=False),
        sa.Column("token", sa.Text(), nullable=True),
        sa.Column("cost", sa.Numeric(12, 4), nullable=False, default=0),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_desc", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # Transactions table
    op.create_table(
        "transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("type", sa.Enum("deposit", "deduct", "refund", "bonus", name="transactiontype"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 4), nullable=False),
        sa.Column("balance_after", sa.Numeric(12, 4), nullable=False),
        sa.Column("reference_id", sa.String(64), nullable=False),
        sa.Column("reference_type", sa.String(32), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )
    op.create_unique_constraint("uq_transactions_ref", "transactions", ["reference_id", "reference_type"])

    # Dead letter tasks table
    op.create_table(
        "dead_letter_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("original_task_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("failed_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False, default=False),
    )


def downgrade() -> None:
    op.drop_table("dead_letter_tasks")
    op.drop_table("transactions")
    op.drop_table("tasks")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS tasktype")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS transactiontype")
