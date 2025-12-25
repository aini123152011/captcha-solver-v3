"""速率限制器 - Redis Token Bucket"""

import time
from typing import Tuple

import redis.asyncio as redis

from captcha_solver.config import settings


class RateLimiter:
    """
    Token Bucket 速率限制器

    使用 Redis 实现分布式限流
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "ratelimit",
    ) -> None:
        self.redis = redis_client
        self.key_prefix = key_prefix

    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """
        检查请求是否被允许

        Args:
            key: 限流键（如 api_key 或 IP）
            max_requests: 窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (is_allowed, remaining, retry_after)
        """
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"{self.key_prefix}:{key}"

        # 使用 Lua 脚本保证原子性
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])

        -- 移除过期请求
        redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

        -- 获取当前请求数
        local current = redis.call('ZCARD', key)

        if current < max_requests then
            -- 添加新请求
            redis.call('ZADD', key, now, now .. '-' .. math.random())
            redis.call('EXPIRE', key, window_seconds)
            return {1, max_requests - current - 1, 0}
        else
            -- 获取最早的请求时间
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = 0
            if #oldest > 0 then
                retry_after = math.ceil(oldest[2] + window_seconds - now)
            end
            return {0, 0, retry_after}
        end
        """

        result = await self.redis.eval(
            lua_script,
            1,
            redis_key,
            str(now),
            str(window_start),
            str(max_requests),
            str(window_seconds),
        )

        is_allowed = bool(result[0])
        remaining = int(result[1])
        retry_after = int(result[2])

        return is_allowed, remaining, retry_after

    async def reset(self, key: str) -> None:
        """重置限流计数"""
        redis_key = f"{self.key_prefix}:{key}"
        await self.redis.delete(redis_key)


# 全局限流器实例
_rate_limiter: RateLimiter | None = None


async def get_rate_limiter() -> RateLimiter:
    """获取全局限流器"""
    global _rate_limiter

    if _rate_limiter is None:
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        _rate_limiter = RateLimiter(redis_client)

    return _rate_limiter
