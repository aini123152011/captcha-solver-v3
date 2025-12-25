"""领域异常"""


class DomainError(Exception):
    """领域异常基类"""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(message)


class EntityNotFoundError(DomainError):
    """实体不存在"""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} not found: {entity_id}", "ENTITY_NOT_FOUND")
        self.entity_type = entity_type
        self.entity_id = entity_id


class InvalidStateTransitionError(DomainError):
    """无效状态转换"""

    def __init__(self, from_state: str, to_state: str) -> None:
        super().__init__(
            f"Invalid state transition: {from_state} -> {to_state}",
            "INVALID_STATE_TRANSITION",
        )


class InsufficientBalanceError(DomainError):
    """余额不足"""

    def __init__(self, required: float, available: float) -> None:
        super().__init__(
            f"Insufficient balance: required {required}, available {available}",
            "INSUFFICIENT_BALANCE",
        )
        self.required = required
        self.available = available


class InvalidApiKeyError(DomainError):
    """无效 API Key"""

    def __init__(self) -> None:
        super().__init__("Invalid API key", "INVALID_API_KEY")


class TaskUnsolvableError(DomainError):
    """任务无法求解"""

    def __init__(self, reason: str | None = None) -> None:
        super().__init__(reason or "Task could not be solved", "TASK_UNSOLVABLE")


class RateLimitExceededError(DomainError):
    """超出速率限制"""

    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__("Rate limit exceeded", "RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class RefundAlreadyProcessedError(DomainError):
    """退款已处理"""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Refund already processed for task: {task_id}", "REFUND_ALREADY_PROCESSED")
