"""
认证模块：JWT 令牌创建和验证，支持 IP 白名单免认证。
"""
import ipaddress
import jwt
from fastapi import Header, HTTPException, Request
from backend.config import settings
from backend.common.logger import logger

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


def _ip_in_whitelist(ip_str: str, whitelist: str) -> bool:
    """检查客户端 IP 是否匹配白名单（支持逗号分隔的 IP 或 CIDR 网段）"""
    try:
        client_ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    for entry in whitelist.split(","):
        entry = entry.strip()
        if not entry:
            continue
        try:
            if "/" in entry:
                if client_ip in ipaddress.ip_network(entry, strict=False):
                    return True
            elif client_ip == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False


async def verify_token(request: Request, authorization: str = Header(None)):
    """FastAPI 依赖：先检查白名单，再验证 JWT 令牌"""
    # 白名单 IP 免认证
    if settings.auth_whitelist_ips and request.client:
        client_ip = request.client.host
        if _ip_in_whitelist(client_ip, settings.auth_whitelist_ips):
            logger.info(f"IP白名单绕过认证成功 client_ip={client_ip}")
            return
    # JWT 令牌验证
    client_ip = request.client.host if request.client else None
    if not authorization:
        if client_ip:
            logger.warning(f"认证失败：未提供认证凭据 client_ip={client_ip}")
        else:
            logger.warning("认证失败：未提供认证凭据")
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        if client_ip:
            logger.warning(f"认证失败：认证格式错误 client_ip={client_ip}")
        else:
            logger.warning("认证失败：认证格式错误")
        raise HTTPException(status_code=401, detail="认证格式错误，需要 Bearer token")
    try:
        jwt.decode(token, settings.admin_password, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        if client_ip:
            logger.warning(f"认证失败：令牌已过期 client_ip={client_ip}")
        else:
            logger.warning("认证失败：令牌已过期")
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        if client_ip:
            logger.warning(f"认证失败：令牌无效 client_ip={client_ip}")
        else:
            logger.warning("认证失败：令牌无效")
        raise HTTPException(status_code=401, detail="令牌无效，请重新登录")
