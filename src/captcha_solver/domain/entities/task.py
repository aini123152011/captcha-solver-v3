"""实体 - Task 聚合根"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from ..exceptions import InvalidStateTransitionError
from ..value_objects import TaskStatus, TaskType


@dataclass
class Task:
    """任务聚合根"""

    id: UUID
    user_id: UUID
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    website_url: str | None = None
    website_key: str = ""
    website_domain: str | None = None
    is_enterprise: bool = False
    token: str | None = None
    cost: Decimal = Decimal("0")
    error_code: str | None = None
    error_desc: str | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        user_id: UUID,
        task_type: TaskType,
        website_key: str,
        website_url: str | None = None,
        website_domain: str | None = None,
        is_enterprise: bool = False,
    ) -> "Task":
        """创建新任务"""
        return cls(
            id=uuid4(),
            user_id=user_id,
            type=task_type,
            website_key=website_key,
            website_url=website_url,
            website_domain=website_domain,
            is_enterprise=is_enterprise,
        )

    def transition_to(self, new_status: TaskStatus) -> None:
        """状态转换"""
        if not self.status.can_transition_to(new_status):
            raise InvalidStateTransitionError(self.status.value, new_status.value)
        self.status = new_status

    def start_processing(self) -> None:
        """开始处理"""
        self.transition_to(TaskStatus.PROCESSING)
        self.started_at = datetime.utcnow()

    def complete(self, token: str, cost: Decimal) -> None:
        """完成任务"""
        self.transition_to(TaskStatus.READY)
        self.token = token
        self.cost = cost
        self.completed_at = datetime.utcnow()

    def fail(self, error_code: str, error_desc: str | None = None) -> None:
        """标记失败"""
        self.transition_to(TaskStatus.FAILED)
        self.error_code = error_code
        self.error_desc = error_desc
        self.completed_at = datetime.utcnow()

    def increment_retry(self) -> None:
        """增加重试计数"""
        self.retry_count += 1

    def is_sitekey_mode(self) -> bool:
        """是否为 Sitekey 模式"""
        return bool(self.website_domain and self.website_key)

    def get_domain(self) -> str | None:
        """获取域名（优先 website_domain，否则从 website_url 解析）"""
        if self.website_domain:
            return self.website_domain
        if self.website_url:
            from urllib.parse import urlparse
            parsed = urlparse(self.website_url)
            return f"{parsed.scheme}://{parsed.netloc}"
        return None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return False
        return self.id == other.id
