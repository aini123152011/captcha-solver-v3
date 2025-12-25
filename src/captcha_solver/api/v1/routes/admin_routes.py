"""Admin API routes."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.api.auth.users import current_superuser
from captcha_solver.domain.value_objects import TaskStatus, TransactionType
from captcha_solver.infrastructure.database.connection import get_async_session
from captcha_solver.infrastructure.database.models import TaskModel, TransactionModel, UserModel
from captcha_solver.infrastructure.database.repositories.task_repo import TaskRepository
from captcha_solver.infrastructure.database.repositories.transaction_repo import TransactionRepository
from captcha_solver.infrastructure.database.repositories.user_repo import UserRepository

router = APIRouter()


class AdminUserResponse(BaseModel):
    id: str
    email: str
    balance: float
    is_active: bool
    is_superuser: bool
    created_at: str


class AdminUserUpdateRequest(BaseModel):
    is_active: bool | None = None
    is_superuser: bool | None = None


class AdminTaskResponse(BaseModel):
    id: str
    user_id: str
    user_email: str | None = None
    type: str
    status: str
    cost: float
    token: str | None = None
    error: str | None = None
    created_at: str
    updated_at: str | None = None


class FinanceStatsResponse(BaseModel):
    total_revenue: float
    total_deposits: float
    total_refunds: float
    net_balance: float
    deposit_count: int
    refund_count: int
    today_revenue: float
    today_tasks: int
    today_success_rate: float
    week_revenue: float
    week_tasks: int
    week_new_users: int
    month_revenue: float
    month_tasks: int
    month_active_users: int


class AdminTransactionResponse(BaseModel):
    id: str
    user_id: str
    user_email: str | None = None
    type: str
    amount: float
    reference: str | None = None
    created_at: str


def _format_datetime(value) -> str | None:
    return value.isoformat() if value else None


def _to_float(value: Decimal | None) -> float:
    return float(value or Decimal("0"))


@router.get("/admin/users", response_model=list[AdminUserResponse])
async def list_users(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    _: UserModel = Depends(current_superuser),
) -> list[AdminUserResponse]:
    user_repo = UserRepository(session)
    users = await user_repo.list_all(limit=limit, offset=offset)
    return [
        AdminUserResponse(
            id=str(user.id),
            email=user.email,
            balance=float(user.balance),
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=_format_datetime(user.created_at),
        )
        for user in users
    ]


@router.patch("/admin/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    _: UserModel = Depends(current_superuser),
) -> AdminUserResponse:
    if payload.is_active is None and payload.is_superuser is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user id",
        ) from exc

    user_repo = UserRepository(session)
    updated = await user_repo.update_flags(
        user_id=user_uuid,
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await session.commit()
    return AdminUserResponse(
        id=str(updated.id),
        email=updated.email,
        balance=float(updated.balance),
        is_active=updated.is_active,
        is_superuser=updated.is_superuser,
        created_at=_format_datetime(updated.created_at),
    )


@router.get("/admin/tasks", response_model=list[AdminTaskResponse])
async def list_tasks(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias="status"),
    session: AsyncSession = Depends(get_async_session),
    _: UserModel = Depends(current_superuser),
) -> list[AdminTaskResponse]:
    task_status = None
    if status_filter:
        try:
            task_status = TaskStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status",
            ) from exc

    task_repo = TaskRepository(session)
    tasks = await task_repo.list_all(limit=limit, offset=offset, status=task_status)

    user_repo = UserRepository(session)
    user_ids = {task.user_id for task in tasks}
    users = await user_repo.list_by_ids(list(user_ids))
    user_email_map = {user.id: user.email for user in users}

    responses: list[AdminTaskResponse] = []
    for task in tasks:
        error = None
        if task.error_code and task.error_desc:
            error = f"{task.error_code}: {task.error_desc}"
        elif task.error_code:
            error = task.error_code
        elif task.error_desc:
            error = task.error_desc

        updated_at = task.completed_at or task.started_at
        responses.append(
            AdminTaskResponse(
                id=str(task.id),
                user_id=str(task.user_id),
                user_email=user_email_map.get(task.user_id),
                type=task.type.value,
                status=task.status.value,
                cost=float(task.cost),
                token=task.token,
                error=error,
                created_at=_format_datetime(task.created_at),
                updated_at=_format_datetime(updated_at),
            )
        )
    return responses


@router.get("/admin/finance/stats", response_model=FinanceStatsResponse)
async def get_finance_stats(
    session: AsyncSession = Depends(get_async_session),
    _: UserModel = Depends(current_superuser),
) -> FinanceStatsResponse:
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    revenue_expr = func.coalesce(
        func.sum(
            case(
                (TransactionModel.type == TransactionType.DEDUCT, -TransactionModel.amount),
                else_=Decimal("0"),
            )
        ),
        Decimal("0"),
    )
    deposit_expr = func.coalesce(
        func.sum(
            case(
                (TransactionModel.type == TransactionType.DEPOSIT, TransactionModel.amount),
                else_=Decimal("0"),
            )
        ),
        Decimal("0"),
    )
    refund_expr = func.coalesce(
        func.sum(
            case(
                (TransactionModel.type == TransactionType.REFUND, TransactionModel.amount),
                else_=Decimal("0"),
            )
        ),
        Decimal("0"),
    )

    total_revenue = (await session.execute(select(revenue_expr))).scalar_one()
    total_deposits = (await session.execute(select(deposit_expr))).scalar_one()
    total_refunds = (await session.execute(select(refund_expr))).scalar_one()

    deposit_count = (
        await session.execute(
            select(func.count()).where(TransactionModel.type == TransactionType.DEPOSIT)
        )
    ).scalar_one()
    refund_count = (
        await session.execute(
            select(func.count()).where(TransactionModel.type == TransactionType.REFUND)
        )
    ).scalar_one()

    net_balance = (
        await session.execute(
            select(func.coalesce(func.sum(UserModel.balance), Decimal("0")))
        )
    ).scalar_one()

    today_revenue = (
        await session.execute(
            select(revenue_expr).where(TransactionModel.created_at >= today_start)
        )
    ).scalar_one()
    week_revenue = (
        await session.execute(
            select(revenue_expr).where(TransactionModel.created_at >= week_start)
        )
    ).scalar_one()
    month_revenue = (
        await session.execute(
            select(revenue_expr).where(TransactionModel.created_at >= month_start)
        )
    ).scalar_one()

    today_tasks = (
        await session.execute(
            select(func.count()).where(TaskModel.created_at >= today_start)
        )
    ).scalar_one()
    today_success_tasks = (
        await session.execute(
            select(func.count()).where(
                TaskModel.created_at >= today_start,
                TaskModel.status == TaskStatus.READY,
            )
        )
    ).scalar_one()
    today_success_rate = 0.0
    if today_tasks:
        today_success_rate = round((today_success_tasks / today_tasks) * 100, 2)

    week_tasks = (
        await session.execute(
            select(func.count()).where(TaskModel.created_at >= week_start)
        )
    ).scalar_one()
    week_new_users = (
        await session.execute(
            select(func.count()).where(UserModel.created_at >= week_start)
        )
    ).scalar_one()

    month_tasks = (
        await session.execute(
            select(func.count()).where(TaskModel.created_at >= month_start)
        )
    ).scalar_one()
    month_active_users = (
        await session.execute(
            select(func.count(func.distinct(TaskModel.user_id))).where(
                TaskModel.created_at >= month_start
            )
        )
    ).scalar_one()

    return FinanceStatsResponse(
        total_revenue=_to_float(total_revenue),
        total_deposits=_to_float(total_deposits),
        total_refunds=_to_float(total_refunds),
        net_balance=_to_float(net_balance),
        deposit_count=deposit_count,
        refund_count=refund_count,
        today_revenue=_to_float(today_revenue),
        today_tasks=today_tasks,
        today_success_rate=today_success_rate,
        week_revenue=_to_float(week_revenue),
        week_tasks=week_tasks,
        week_new_users=week_new_users,
        month_revenue=_to_float(month_revenue),
        month_tasks=month_tasks,
        month_active_users=month_active_users,
    )


@router.get("/admin/finance/transactions", response_model=list[AdminTransactionResponse])
async def list_finance_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    _: UserModel = Depends(current_superuser),
) -> list[AdminTransactionResponse]:
    tx_repo = TransactionRepository(session)
    transactions = await tx_repo.list_recent(limit=limit, offset=offset)

    user_repo = UserRepository(session)
    user_ids = {tx.user_id for tx in transactions}
    users = await user_repo.list_by_ids(list(user_ids))
    user_email_map = {user.id: user.email for user in users}

    return [
        AdminTransactionResponse(
            id=str(tx.id),
            user_id=str(tx.user_id),
            user_email=user_email_map.get(tx.user_id),
            type=tx.type.value,
            amount=float(tx.amount),
            reference=tx.reference_id,
            created_at=_format_datetime(tx.created_at),
        )
        for tx in transactions
    ]
