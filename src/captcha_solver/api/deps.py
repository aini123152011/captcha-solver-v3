"""API 依赖注入"""

from typing import Optional

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from captcha_solver.config import settings


# 全局 Redis 连接池
_arq_redis: Optional[ArqRedis] = None


def get_redis_settings() -> RedisSettings:
    """解析 Redis URL 获取设置"""
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


async def get_arq_redis() -> ArqRedis:
    """获取 arq Redis 连接"""
    global _arq_redis
    if _arq_redis is None:
        _arq_redis = await create_pool(get_redis_settings())
    return _arq_redis


async def close_arq_redis() -> None:
    """关闭 arq Redis 连接"""
    global _arq_redis
    if _arq_redis:
        await _arq_redis.close()
        _arq_redis = None
