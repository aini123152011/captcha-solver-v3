"""数据库连接配置"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from captcha_solver.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入 - 获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_db_and_tables() -> None:
    """创建数据库表（仅用于开发/测试）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
