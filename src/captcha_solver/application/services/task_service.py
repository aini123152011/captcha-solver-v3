"""任务服务 - 处理任务生命周期"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.config import settings
from captcha_solver.domain.entities.task import Task
from captcha_solver.domain.exceptions import EntityNotFoundError, InsufficientBalanceError
from captcha_solver.domain.value_objects import TaskStatus, TaskType
from captcha_solver.infrastructure.database.repositories.task_repo import TaskRepository
from captcha_solver.infrastructure.database.repositories.user_repo import UserRepository
from .billing_service import BillingService


class TaskService:
    """任务服务"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)
        self.user_repo = UserRepository(session)
        self.billing = BillingService(session)

    async def create_task(
        self,
        user_id: UUID,
        task_type: TaskType,
        website_key: str,
        website_url: str | None = None,
        website_domain: str | None = None,
        is_enterprise: bool = False,
    ) -> Task:
        """创建任务"""
        # 检查用户余额
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", str(user_id))

        price = Decimal(str(settings.price_per_task))
        if not user.can_afford(price):
            raise InsufficientBalanceError(float(price), float(user.balance))

        # 创建任务
        task = Task.create(
            user_id=user_id,
            task_type=task_type,
            website_key=website_key,
            website_url=website_url,
            website_domain=website_domain,
            is_enterprise=is_enterprise,
        )

        saved_task = await self.task_repo.save(task)
        await self.session.commit()
        return saved_task

    async def get_task(self, task_id: UUID, user_id: UUID) -> Task:
        """获取任务"""
        task = await self.task_repo.get_by_id_and_user(task_id, user_id)
        if task is None:
            raise EntityNotFoundError("Task", str(task_id))
        return task

    async def get_task_by_id(self, task_id: UUID) -> Task:
        """通过 ID 获取任务（内部使用）"""
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise EntityNotFoundError("Task", str(task_id))
        return task

    async def start_processing(self, task_id: UUID) -> bool:
        """开始处理任务"""
        result = await self.task_repo.update_status(task_id, TaskStatus.PROCESSING)
        await self.session.commit()
        return result

    async def complete_task(
        self,
        task_id: UUID,
        token: str,
    ) -> Task:
        """
        完成任务并扣费 - 原子操作

        扣费和状态更新在同一事务中完成
        """
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise EntityNotFoundError("Task", str(task_id))

        price = Decimal(str(settings.price_per_task))

        try:
            # 扣费 (不自动提交)
            await self.billing.deduct_balance(
                user_id=task.user_id,
                amount=price,
                task_id=str(task.id),
                auto_commit=False,
            )

            # 更新任务状态 (同一事务)
            await self.task_repo.update_status(
                task_id=task_id,
                status=TaskStatus.READY,
                token=token,
                cost=price,
            )

            # 统一提交
            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return await self.get_task_by_id(task_id)

    async def fail_task(
        self,
        task_id: UUID,
        error_code: str,
        error_desc: str | None = None,
    ) -> Task:
        """标记任务失败"""
        await self.task_repo.update_status(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_code=error_code,
            error_desc=error_desc,
        )
        await self.session.commit()
        return await self.get_task_by_id(task_id)

    async def refund_task(self, task_id: UUID, user_id: UUID) -> bool:
        """退款"""
        task = await self.get_task(task_id, user_id)

        if task.status != TaskStatus.READY:
            return False

        if task.cost <= 0:
            return False

        try:
            await self.billing.refund(
                user_id=user_id,
                amount=task.cost,
                task_id=str(task_id),
            )
            return True
        except Exception:
            return False

    async def list_user_tasks(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """获取用户任务列表"""
        return await self.task_repo.list_by_user(user_id, limit, offset, status)
