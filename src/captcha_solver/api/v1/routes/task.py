"""任务 API 路由"""

from uuid import UUID

from arq import ArqRedis
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.application.services.auth_service import AuthService
from captcha_solver.application.services.task_service import TaskService
from captcha_solver.config import settings
from captcha_solver.domain.exceptions import (
    DomainError,
    EntityNotFoundError,
    InsufficientBalanceError,
    InvalidApiKeyError,
    RateLimitExceededError,
)
from captcha_solver.domain.value_objects import TaskStatus, TaskType
from captcha_solver.infrastructure.cache.rate_limiter import get_rate_limiter
from captcha_solver.infrastructure.database.connection import get_async_session
from ..schemas.task import (
    CreateTaskRequest,
    CreateTaskResponse,
    ErrorCodes,
    GetBalanceRequest,
    GetBalanceResponse,
    GetTaskResultRequest,
    GetTaskResultResponse,
    ReportIncorrectRequest,
    ReportIncorrectResponse,
    make_error_response,
)
from captcha_solver.api.deps import get_arq_redis

router = APIRouter()


async def check_rate_limit(api_key: str) -> None:
    """检查速率限制"""
    rate_limiter = await get_rate_limiter()
    is_allowed, remaining, retry_after = await rate_limiter.is_allowed(
        key=api_key[:16],  # 使用 API Key 前缀作为限流键
        max_requests=settings.rate_limit_per_minute,
        window_seconds=60,
    )
    if not is_allowed:
        raise RateLimitExceededError(retry_after)


@router.post("/createTask", response_model=CreateTaskResponse)
async def create_task(
    request: CreateTaskRequest,
    session: AsyncSession = Depends(get_async_session),
    redis: ArqRedis = Depends(get_arq_redis),
) -> CreateTaskResponse:
    """创建验证码识别任务"""
    try:
        # 速率限制检查
        await check_rate_limit(request.clientKey)

        # 验证 API Key
        auth_service = AuthService(session)
        user = await auth_service.authenticate_by_api_key(request.clientKey)

        # 验证并解析任务参数
        try:
            task_params = request.get_validated_task()
        except (ValueError, ValidationError) as e:
            logger.warning(f"Invalid task params: {e}")
            return CreateTaskResponse(**make_error_response(ErrorCodes.INVALID_TASK_TYPE))

        # 解析任务类型
        task_type = TaskType.from_string(task_params.type)

        # 创建任务
        task_service = TaskService(session)
        task = await task_service.create_task(
            user_id=user.id,
            task_type=task_type,
            website_key=task_params.websiteKey,
            website_url=str(task_params.websiteURL),
            website_domain=getattr(task_params, "websiteDomain", None),
            is_enterprise=getattr(task_params, "isEnterprise", False),
        )

        # 加入任务队列
        await redis.enqueue_job("solve_captcha_task", str(task.id))
        logger.info(f"Task {task.id} enqueued")

        return CreateTaskResponse(errorId=0, taskId=str(task.id))

    except RateLimitExceededError:
        return CreateTaskResponse(**make_error_response(ErrorCodes.RATE_LIMIT))
    except InvalidApiKeyError:
        return CreateTaskResponse(**make_error_response(ErrorCodes.INVALID_API_KEY))
    except InsufficientBalanceError:
        return CreateTaskResponse(**make_error_response(ErrorCodes.ZERO_BALANCE))
    except DomainError as e:
        logger.warning(f"Domain error: {e}")
        return CreateTaskResponse(**make_error_response(ErrorCodes.INTERNAL_ERROR))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return CreateTaskResponse(**make_error_response(ErrorCodes.INTERNAL_ERROR))


@router.post("/getTaskResult", response_model=GetTaskResultResponse)
async def get_task_result(
    request: GetTaskResultRequest,
    session: AsyncSession = Depends(get_async_session),
) -> GetTaskResultResponse:
    """获取任务结果"""
    try:
        # 速率限制检查
        await check_rate_limit(request.clientKey)

        # 验证 API Key
        auth_service = AuthService(session)
        user = await auth_service.authenticate_by_api_key(request.clientKey)

        # 获取任务
        task_service = TaskService(session)
        task = await task_service.get_task(UUID(request.taskId), user.id)

        # 根据状态返回结果
        if task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING):
            return GetTaskResultResponse(errorId=0, status="processing")

        if task.status == TaskStatus.READY:
            return GetTaskResultResponse(
                errorId=0,
                status="ready",
                solution={"gRecaptchaResponse": task.token},
                cost=float(task.cost),
                createTime=int(task.created_at.timestamp()),
                endTime=int(task.completed_at.timestamp()) if task.completed_at else None,
            )

        # FAILED
        return GetTaskResultResponse(
            **make_error_response(
                ErrorCodes.TASK_UNSOLVABLE,
                errorCode=task.error_code,
                errorDescription=task.error_desc,
            )
        )

    except RateLimitExceededError:
        return GetTaskResultResponse(**make_error_response(ErrorCodes.RATE_LIMIT))
    except InvalidApiKeyError:
        return GetTaskResultResponse(**make_error_response(ErrorCodes.INVALID_API_KEY))
    except EntityNotFoundError:
        return GetTaskResultResponse(**make_error_response(ErrorCodes.NO_SUCH_TASK))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return GetTaskResultResponse(**make_error_response(ErrorCodes.INTERNAL_ERROR))


@router.post("/getBalance", response_model=GetBalanceResponse)
async def get_balance(
    request: GetBalanceRequest,
    session: AsyncSession = Depends(get_async_session),
) -> GetBalanceResponse:
    """获取余额"""
    try:
        await check_rate_limit(request.clientKey)
        auth_service = AuthService(session)
        user = await auth_service.authenticate_by_api_key(request.clientKey)
        return GetBalanceResponse(errorId=0, balance=float(user.balance))
    except RateLimitExceededError:
        return GetBalanceResponse(**make_error_response(ErrorCodes.RATE_LIMIT))
    except InvalidApiKeyError:
        return GetBalanceResponse(**make_error_response(ErrorCodes.INVALID_API_KEY))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return GetBalanceResponse(**make_error_response(ErrorCodes.INTERNAL_ERROR))


@router.post("/reportIncorrect", response_model=ReportIncorrectResponse)
async def report_incorrect(
    request: ReportIncorrectRequest,
    session: AsyncSession = Depends(get_async_session),
) -> ReportIncorrectResponse:
    """报告错误结果 (退款)"""
    try:
        await check_rate_limit(request.clientKey)
        auth_service = AuthService(session)
        user = await auth_service.authenticate_by_api_key(request.clientKey)

        task_service = TaskService(session)
        success = await task_service.refund_task(UUID(request.taskId), user.id)

        return ReportIncorrectResponse(
            errorId=0,
            status="success" if success else "already_refunded",
        )
    except RateLimitExceededError:
        return ReportIncorrectResponse(**make_error_response(ErrorCodes.RATE_LIMIT))
    except InvalidApiKeyError:
        return ReportIncorrectResponse(**make_error_response(ErrorCodes.INVALID_API_KEY))
    except EntityNotFoundError:
        return ReportIncorrectResponse(**make_error_response(ErrorCodes.NO_SUCH_TASK))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return ReportIncorrectResponse(**make_error_response(ErrorCodes.INTERNAL_ERROR))
