"""
认证模块：JWT 令牌创建和验证。
"""
import jwt
from fastapi import Header, HTTPException, Request
from backend.config import settings

_ALGORITHM = "HS256"
_TOKEN_EXPIRE_SECONDS = 7 * 24 * 3600  # 7 天


def create_token() -> str:
    """创建 JWT 令牌，有效期 7 天"""
    import time
    now = int(time.time())
    payload = {
        "sub": "admin",
        "iat": now,
        "exp": now + _TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, settings.admin_password, algorithm=_ALGORITHM)


async def verify_token(authorization: str = Header(None)):
    """FastAPI 依赖：从 Authorization Header 中验证 JWT 令牌"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="认证格式错误，需要 Bearer token")
    try:
        jwt.decode(token, settings.admin_password, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="令牌无效，请重新登录")
