"""领域接口 - AI Provider"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class AIProviderType(str, Enum):
    """AI 提供商类型"""

    SAM3 = "sam3"
    OPENAI = "openai"
    CLAUDE = "claude"


@dataclass
class ImageAnalysisResult:
    """图像分析结果"""

    success: bool
    target_cells: list[tuple[int, int]]  # (row, col) 列表
    confidence: float = 0.0
    error: str | None = None


class IAIProvider(Protocol):
    """AI 提供商接口"""

    @property
    def provider_type(self) -> AIProviderType:
        """提供商类型"""
        ...

    @property
    def is_available(self) -> bool:
        """是否可用"""
        ...

    async def analyze_captcha(
        self,
        image_data: bytes,
        target_description: str,
        grid_size: tuple[int, int] = (3, 3),
    ) -> ImageAnalysisResult:
        """分析验证码图像"""
        ...


class IAIProviderManager(Protocol):
    """AI 提供商管理器接口"""

    def get_available_providers(self) -> list[IAIProvider]:
        """获取可用提供商列表"""
        ...

    async def analyze_captcha(
        self,
        image_data: bytes,
        target_description: str,
        grid_size: tuple[int, int] = (3, 3),
        preferred_provider: AIProviderType | None = None,
    ) -> ImageAnalysisResult:
        """分析验证码（自动选择提供商）"""
        ...
