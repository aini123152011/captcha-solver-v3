"""应用配置 - Pydantic Settings"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置 - 从环境变量加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "Captcha Solver"
    app_version: str = "3.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # 安全配置
    secret_key: str = Field(default="change-me-in-production", min_length=32)
    api_key_pepper: str = Field(default="change-me-in-production", min_length=32)
    api_key_pepper_previous: str | None = None  # 用于轮换

    # 数据库配置
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/captcha_solver"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10

    # 浏览器配置
    browser_pool_size: int = 5
    browser_headless: bool = True
    browser_proxy: str | None = None
    browser_proxies: str | None = None  # 逗号分隔

    @computed_field
    @property
    def proxy_list(self) -> list[str] | None:
        if self.browser_proxies:
            return [p.strip() for p in self.browser_proxies.split(",") if p.strip()]
        return None

    # AI 配置
    sam3_enabled: bool = True
    sam3_verify_ssl: bool = True
    sam3_proxy: str | None = None
    openai_api_key: str | None = None
    claude_api_key: str | None = None

    # 定价配置
    price_per_1000: float = 2.99

    @computed_field
    @property
    def price_per_task(self) -> float:
        return self.price_per_1000 / 1000

    # 任务配置
    task_timeout: int = 120
    task_max_retries: int = 3

    # 速率限制
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # JWT 配置
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # 邮件配置
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@example.com"

    # Stripe 配置
    stripe_api_key: str | None = None
    stripe_webhook_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
