"""Worker 主入口"""

from typing import Any

from arq import cron
from arq.connections import RedisSettings
from loguru import logger

from captcha_solver.config import settings
from captcha_solver.infrastructure.browser.pool import BrowserPoolV2, close_browser_pool, get_browser_pool
from .handlers.solve_task import solve_captcha_task


def get_redis_settings() -> RedisSettings:
    """解析 Redis URL"""
    url = settings.redis_url

    if url.startswith("redis://"):
        url = url[8:]

    host = "localhost"
    port = 6379
    database = 0

    if "/" in url:
        url, db_str = url.rsplit("/", 1)
        database = int(db_str) if db_str else 0

    if ":" in url:
        host, port_str = url.rsplit(":", 1)
        port = int(port_str)
    else:
        host = url

    return RedisSettings(
        host=host,
        port=port,
        database=database,
        conn_timeout=30,
        conn_retries=5,
        conn_retry_delay=1,
    )


async def startup(ctx: dict[str, Any]) -> None:
    """Worker 启动"""
    logger.info("Worker starting...")

    # 初始化浏览器池
    pool = await get_browser_pool()
    ctx["browser_pool"] = pool

    logger.info(f"Browser pool initialized (size={settings.browser_pool_size})")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker 关闭"""
    logger.info("Worker shutting down...")

    await close_browser_pool()

    logger.info("Worker stopped")


class WorkerSettings:
    """arq Worker 设置"""

    functions = [solve_captcha_task]

    on_startup = startup
    on_shutdown = shutdown

    redis_settings = get_redis_settings()

    # Worker 配置
    max_jobs = 5
    job_timeout = 300
    keep_result = 3600
    poll_delay = 0.5
    max_tries = 3


def run():
    """运行 Worker"""
    import asyncio
    from arq import run_worker

    asyncio.run(run_worker(WorkerSettings))


if __name__ == "__main__":
    run()
