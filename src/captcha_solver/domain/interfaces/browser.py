"""领域接口 - Browser"""

from dataclasses import dataclass
from typing import AsyncContextManager, Protocol

from playwright.async_api import Page


@dataclass
class SolveResult:
    """求解结果"""

    success: bool
    token: str | None = None
    error_code: str | None = None
    error_desc: str | None = None
    retry_count: int = 0


class IBrowserPool(Protocol):
    """浏览器池接口"""

    async def initialize(self) -> None:
        """初始化浏览器池"""
        ...

    async def close(self) -> None:
        """关闭浏览器池"""
        ...

    def new_page(self) -> AsyncContextManager[Page]:
        """获取新页面（Context Manager）"""
        ...


class ICaptchaSolver(Protocol):
    """验证码求解器接口"""

    async def solve(
        self,
        page: Page,
        website_url: str | None = None,
        website_key: str | None = None,
        website_domain: str | None = None,
        is_enterprise: bool = False,
    ) -> SolveResult:
        """求解验证码"""
        ...
