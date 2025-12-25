"""API 请求/响应 Schema"""

from datetime import datetime
from typing import Any, Literal, Union, Annotated
import re

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


# ===== 任务参数 Schema =====


class RecaptchaV2TaskParams(BaseModel):
    """reCAPTCHA v2 任务参数"""

    type: Literal["RecaptchaV2Task", "RecaptchaV2TaskInvisible", "RecaptchaV2TaskProxyless"]
    websiteURL: HttpUrl
    websiteKey: str = Field(..., min_length=20, max_length=60)
    websiteDomain: str | None = None
    isEnterprise: bool = False

    @field_validator("websiteKey")
    @classmethod
    def validate_sitekey(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_-]+$", v):
            raise ValueError("Invalid sitekey format")
        return v


class RecaptchaV3TaskParams(BaseModel):
    """reCAPTCHA v3 任务参数"""

    type: Literal["RecaptchaV3Task"]
    websiteURL: HttpUrl
    websiteKey: str = Field(..., min_length=20, max_length=60)
    pageAction: str | None = None
    minScore: float = Field(default=0.3, ge=0.1, le=0.9)

    @field_validator("websiteKey")
    @classmethod
    def validate_sitekey(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_-]+$", v):
            raise ValueError("Invalid sitekey format")
        return v


# Union type for all task params
TaskParams = Union[RecaptchaV2TaskParams, RecaptchaV3TaskParams]


class CreateTaskRequest(BaseModel):
    """创建任务请求"""

    clientKey: str = Field(..., description="API Key", min_length=32)
    task: dict = Field(..., description="任务参数")

    def get_validated_task(self) -> TaskParams:
        """获取验证后的任务参数"""
        task_type = self.task.get("type")
        if task_type in ("RecaptchaV2Task", "RecaptchaV2TaskInvisible", "RecaptchaV2TaskProxyless"):
            return RecaptchaV2TaskParams(**self.task)
        elif task_type == "RecaptchaV3Task":
            return RecaptchaV3TaskParams(**self.task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")


class CreateTaskResponse(BaseModel):
    """创建任务响应"""

    errorId: int = 0
    errorCode: str | None = None
    errorDescription: str | None = None
    taskId: str | None = None


class GetTaskResultRequest(BaseModel):
    """获取任务结果请求"""

    clientKey: str = Field(..., description="API Key")
    taskId: str = Field(..., description="任务 ID")


class GetTaskResultResponse(BaseModel):
    """获取任务结果响应"""

    errorId: int = 0
    errorCode: str | None = None
    errorDescription: str | None = None
    status: str | None = None  # "processing" | "ready"
    solution: dict | None = None
    cost: float | None = None
    createTime: int | None = None
    endTime: int | None = None


# ===== 余额相关 Schema =====


class GetBalanceRequest(BaseModel):
    """获取余额请求"""

    clientKey: str = Field(..., description="API Key")


class GetBalanceResponse(BaseModel):
    """获取余额响应"""

    errorId: int = 0
    errorCode: str | None = None
    errorDescription: str | None = None
    balance: float | None = None


# ===== 报告错误 Schema =====


class ReportIncorrectRequest(BaseModel):
    """报告错误请求"""

    clientKey: str = Field(..., description="API Key")
    taskId: str = Field(..., description="任务 ID")


class ReportIncorrectResponse(BaseModel):
    """报告错误响应"""

    errorId: int = 0
    errorCode: str | None = None
    errorDescription: str | None = None
    status: str | None = None


# ===== 错误码 =====


class ErrorCodes:
    """错误码常量"""

    SUCCESS = 0
    MISSING_PARAM = 1
    INVALID_API_KEY = 2
    INVALID_TASK_TYPE = 3
    ZERO_BALANCE = 10
    NO_SUCH_TASK = 12
    TASK_UNSOLVABLE = 21
    RATE_LIMIT = 22
    INTERNAL_ERROR = 99


ERROR_MESSAGES = {
    ErrorCodes.MISSING_PARAM: ("ERROR_MISSING_PARAM", "缺少必要参数"),
    ErrorCodes.INVALID_API_KEY: ("ERROR_KEY_DOES_NOT_EXIST", "API Key 无效"),
    ErrorCodes.INVALID_TASK_TYPE: ("ERROR_INVALID_TASK_TYPE", "不支持的任务类型"),
    ErrorCodes.ZERO_BALANCE: ("ERROR_ZERO_BALANCE", "余额不足"),
    ErrorCodes.NO_SUCH_TASK: ("ERROR_NO_SUCH_CAPTCHA_ID", "任务不存在"),
    ErrorCodes.TASK_UNSOLVABLE: ("ERROR_CAPTCHA_UNSOLVABLE", "验证码无法识别"),
    ErrorCodes.RATE_LIMIT: ("ERROR_RATE_LIMIT", "请求频率超限"),
    ErrorCodes.INTERNAL_ERROR: ("ERROR_INTERNAL", "内部错误"),
}


def make_error_response(error_id: int, **extra: Any) -> dict:
    """生成错误响应"""
    if error_id == 0:
        return {"errorId": 0, **extra}

    code, desc = ERROR_MESSAGES.get(error_id, ("ERROR_UNKNOWN", "未知错误"))
    return {
        "errorId": error_id,
        "errorCode": code,
        "errorDescription": desc,
        **extra,
    }
