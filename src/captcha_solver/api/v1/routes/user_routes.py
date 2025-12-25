"""User-facing API routes."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.api.auth.users import current_active_user
from captcha_solver.application.services.auth_service import AuthService
from captcha_solver.application.services.task_service import TaskService
from captcha_solver.domain.entities.task import Task
from captcha_solver.domain.entities.transaction import Transaction
from captcha_solver.domain.exceptions import EntityNotFoundError
from captcha_solver.domain.value_objects import TaskStatus
from captcha_solver.infrastructure.database.connection import get_async_session
from captcha_solver.infrastructure.database.models import UserModel
from captcha_solver.infrastructure.database.repositories.transaction_repo import TransactionRepository

router = APIRouter()


class RegenerateApiKeyResponse(BaseModel):
    api_key: str


class TaskResponse(BaseModel):
    id: str
    user_id: str
    type: str
    status: str
    website_url: str | None
    website_key: str
    website_domain: str | None
    is_enterprise: bool
    token: str | None
    cost: float
    error_code: str | None
    error_desc: str | None
    retry_count: int
    created_at: str
    started_at: str | None
    completed_at: str | None


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    amount: float
    balance_after: float
    task_id: str | None
    reference: str | None
    description: str | None
    created_at: str


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)


class DepositResponse(BaseModel):
    checkout_url: str


def _format_datetime(value) -> str | None:
    return value.isoformat() if value else None


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=str(task.id),
        user_id=str(task.user_id),
        type=task.type.value,
        status=task.status.value,
        website_url=task.website_url,
        website_key=task.website_key,
        website_domain=task.website_domain,
        is_enterprise=task.is_enterprise,
        token=task.token,
        cost=float(task.cost),
        error_code=task.error_code,
        error_desc=task.error_desc,
        retry_count=task.retry_count,
        created_at=_format_datetime(task.created_at),
        started_at=_format_datetime(task.started_at),
        completed_at=_format_datetime(task.completed_at),
    )


def _transaction_to_response(tx: Transaction) -> TransactionResponse:
    task_id = tx.reference_id if tx.reference_type in ("TASK", "TASK_REFUND") else None
    return TransactionResponse(
        id=str(tx.id),
        user_id=str(tx.user_id),
        type=tx.type.value,
        amount=float(tx.amount),
        balance_after=float(tx.balance_after),
        task_id=task_id,
        reference=tx.reference_id,
        description=tx.description,
        created_at=_format_datetime(tx.created_at),
    )


@router.post("/users/me/regenerate-api-key", response_model=RegenerateApiKeyResponse)
async def regenerate_api_key(
    session: AsyncSession = Depends(get_async_session),
    user: UserModel = Depends(current_active_user),
) -> RegenerateApiKeyResponse:
    auth_service = AuthService(session)
    new_key = await auth_service.regenerate_api_key(user.id)
    await session.commit()
    return RegenerateApiKeyResponse(api_key=new_key)


@router.get("/api/v1/tasks", response_model=list[TaskResponse])
async def list_tasks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias="status"),
    session: AsyncSession = Depends(get_async_session),
    user: UserModel = Depends(current_active_user),
) -> list[TaskResponse]:
    task_status = None
    if status_filter:
        try:
            task_status = TaskStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status",
            ) from exc

    task_service = TaskService(session)
    tasks = await task_service.list_user_tasks(
        user_id=user.id,
        limit=limit,
        offset=offset,
        status=task_status,
    )
    return [_task_to_response(task) for task in tasks]


@router.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: UserModel = Depends(current_active_user),
) -> TaskResponse:
    try:
        task_uuid = UUID(task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task id",
        ) from exc

    task_service = TaskService(session)
    try:
        task = await task_service.get_task(task_uuid, user.id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    return _task_to_response(task)


@router.get("/api/v1/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    user: UserModel = Depends(current_active_user),
) -> list[TransactionResponse]:
    tx_repo = TransactionRepository(session)
    transactions = await tx_repo.list_by_user(
        user_id=user.id,
        limit=limit,
        offset=offset,
    )
    return [_transaction_to_response(tx) for tx in transactions]


@router.post("/api/v1/deposit", response_model=DepositResponse)
async def create_deposit(
    payload: DepositRequest,
    user: UserModel = Depends(current_active_user),
) -> DepositResponse:
    checkout_url = f"https://checkout.stripe.com/pay/mock?amount={payload.amount}"
    return DepositResponse(checkout_url=checkout_url)
