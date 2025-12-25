"""FastAPI Users Schemas"""

import uuid
from decimal import Decimal
from typing import Optional

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    """用户读取 Schema"""
    balance: Decimal = Decimal("0")
    api_key_prefix: Optional[str] = None
    is_verified: bool = False


class UserCreate(schemas.BaseUserCreate):
    """用户创建 Schema"""
    pass


class UserUpdate(schemas.BaseUserUpdate):
    """用户更新 Schema"""
    pass
