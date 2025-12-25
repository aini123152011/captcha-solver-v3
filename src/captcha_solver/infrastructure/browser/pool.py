"""浏览器池 - 每任务独立上下文"""

import asyncio
import random
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from captcha_solver.config import settings

_browser_pool: "BrowserPoolV2 | None" = None
_pool_lock = asyncio.Lock()


class BrowserPoolV2:
    """浏览器池 V2 - 每任务独立上下文，避免污染"""

    def __init__(
        self,
        pool_size: int = 5,
        headless: bool = True,
        proxy_list: list[str] | None = None,
    ):
        self._pool_size = pool_size
        self._headless = headless
        self._proxy_list = proxy_list or []
        self._playwright = None
        self._browser: Browser | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """初始化浏览器"""
        if self._initialized:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        self._semaphore = asyncio.Semaphore(self._pool_size)
        self._initialized = True
        logger.info(f"Browser pool initialized (size={self._pool_size})")

    async def close(self) -> None:
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._initialized = False
        logger.info("Browser pool closed")

    def _get_random_proxy(self) -> dict | None:
        """随机获取代理"""
        if not self._proxy_list:
            return None
        proxy_url = random.choice(self._proxy_list)
        return {"server": proxy_url}

    @asynccontextmanager
    async def new_context(self) -> AsyncGenerator[BrowserContext, None]:
        """获取新上下文（隔离环境）"""
        if not self._initialized or not self._browser:
            raise RuntimeError("Browser pool not initialized")

        async with self._semaphore:
            proxy = self._get_random_proxy()
            context = await self._browser.new_context(
                proxy=proxy,
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
                bypass_csp=True,
            )
            try:
                yield context
            finally:
                await context.close()

    @asynccontextmanager
    async def new_page(self) -> AsyncGenerator[Page, None]:
        """获取新页面（简化接口）"""
        async with self.new_context() as context:
            page = await context.new_page()
            try:
                yield page
            finally:
                await page.close()


async def get_browser_pool() -> BrowserPoolV2:
    """获取浏览器池单例"""
    global _browser_pool
    async with _pool_lock:
        if _browser_pool is None:
            _browser_pool = BrowserPoolV2(
                pool_size=settings.browser_pool_size,
                headless=settings.browser_headless,
                proxy_list=settings.proxy_list,
            )
            await _browser_pool.initialize()
        return _browser_pool


async def close_browser_pool() -> None:
    """关闭浏览器池"""
    global _browser_pool
    async with _pool_lock:
        if _browser_pool:
            await _browser_pool.close()
            _browser_pool = None
