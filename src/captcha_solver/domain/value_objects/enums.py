"""值对象 - 任务类型和状态"""

from enum import Enum


class TaskType(str, Enum):
    """任务类型"""

    RECAPTCHA_V2 = "RecaptchaV2Task"
    RECAPTCHA_V2_INVISIBLE = "RecaptchaV2TaskInvisible"
    RECAPTCHA_V3 = "RecaptchaV3Task"
    HCAPTCHA = "HCaptchaTask"

    @classmethod
    def from_string(cls, value: str) -> "TaskType":
        """从字符串解析任务类型 (支持 2captcha 标准名称)"""
        # 移除 Proxyless 后缀进行匹配
        normalized = value.replace("Proxyless", "").replace("proxyless", "")
        for member in cls:
            if member.value == normalized or member.value == value:
                return member
        raise ValueError(f"Unknown task type: {value}")

    def is_invisible(self) -> bool:
        return "Invisible" in self.value


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

    def is_terminal(self) -> bool:
        """是否为终态"""
        return self in (TaskStatus.READY, TaskStatus.FAILED)

    def can_transition_to(self, target: "TaskStatus") -> bool:
        """检查状态转换是否合法"""
        allowed_transitions = {
            TaskStatus.PENDING: {TaskStatus.PROCESSING, TaskStatus.FAILED},
            TaskStatus.PROCESSING: {TaskStatus.READY, TaskStatus.FAILED},
            TaskStatus.READY: set(),  # 终态
            TaskStatus.FAILED: set(),  # 终态
        }
        return target in allowed_transitions.get(self, set())


class TransactionType(str, Enum):
    """交易类型"""

    DEPOSIT = "deposit"
    DEDUCT = "deduct"
    REFUND = "refund"
    BONUS = "bonus"


class PaymentStatus(str, Enum):
    """支付状态"""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
