"""任务仓储实现"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from captcha_solver.domain.entities.task import Task
from captcha_solver.domain.value_objects import TaskStatus, TaskType
from ..models import TaskModel


class TaskRepository:
    """任务仓储"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: UUID) -> Task | None:
        """通过 ID 获取任务"""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id_and_user(self, task_id: UUID, user_id: UUID) -> Task | None:
        """通过 ID 和用户 ID 获取任务"""
        result = await self.session.execute(
            select(TaskModel).where(
                TaskModel.id == task_id,
                TaskModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, task: Task) -> Task:
        """保存任务 (不 commit，由调用方控制事务)"""
        model = self._to_model(task)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update_status(
        self,
        task_id: UUID,
        status: TaskStatus,
        token: str | None = None,
        cost: Decimal | None = None,
        error_code: str | None = None,
        error_desc: str | None = None,
    ) -> bool:
        """更新任务状态"""
        values: dict = {
            "status": status,
        }

        if status == TaskStatus.PROCESSING:
            values["started_at"] = datetime.utcnow()

        if status in (TaskStatus.READY, TaskStatus.FAILED):
            values["completed_at"] = datetime.utcnow()

        if token is not None:
            values["token"] = token

        if cost is not None:
            values["cost"] = cost

        if error_code is not None:
            values["error_code"] = error_code

        if error_desc is not None:
            values["error_desc"] = error_desc

        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(**values)
        )

        result = await self.session.execute(stmt)
        # 不 commit，由调用方控制事务
        return result.rowcount > 0

    async def increment_retry(self, task_id: UUID) -> bool:
        """增加重试计数"""
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(retry_count=TaskModel.retry_count + 1)
        )
        result = await self.session.execute(stmt)
        # 不 commit，由调用方控制事务
        return result.rowcount > 0

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """获取用户任务列表"""
        stmt = select(TaskModel).where(TaskModel.user_id == user_id)
        if status is not None:
            stmt = stmt.where(TaskModel.status == status)
        result = await self.session.execute(
            stmt.order_by(TaskModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """获取所有任务列表"""
        stmt = select(TaskModel)
        if status is not None:
            stmt = stmt.where(TaskModel.status == status)
        result = await self.session.execute(
            stmt.order_by(TaskModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: TaskModel) -> Task:
        """模型转实体"""
        return Task(
            id=model.id,
            user_id=model.user_id,
            type=model.type,
            status=model.status,
            website_url=model.website_url,
            website_key=model.website_key,
            website_domain=model.website_domain,
            is_enterprise=model.is_enterprise,
            token=model.token,
            cost=model.cost,
            error_code=model.error_code,
            error_desc=model.error_desc,
            retry_count=model.retry_count,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )

    def _to_model(self, entity: Task) -> TaskModel:
        """实体转模型"""
        return TaskModel(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type,
            status=entity.status,
            website_url=entity.website_url,
            website_key=entity.website_key,
            website_domain=entity.website_domain,
            is_enterprise=entity.is_enterprise,
            token=entity.token,
            cost=entity.cost,
            error_code=entity.error_code,
            error_desc=entity.error_desc,
            retry_count=entity.retry_count,
            created_at=entity.created_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
        )
