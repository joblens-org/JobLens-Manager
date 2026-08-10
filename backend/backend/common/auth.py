"""
认证模块：JWT 令牌创建和验证，支持 IP 白名单免认证。
"""
import ipaddress
from typing import Annotated

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


def ip_in_whitelist(ip_str: str, whitelist: str) -> bool:
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


def resolve_client_ip(request: Request) -> str | None:
    """
    解析客户端真实 IP 地址。

    当 trust_proxy_headers 为 False 时，直接返回 request.client.host，
    忽略 X-Forwarded-For 和 X-Real-IP 头（防止客户端伪造）。

    当 trust_proxy_headers 为 True 时，优先使用 X-Forwarded-For 的第一个非空 IP，
    其次使用 X-Real-IP，最后回退到 request.client.host。
    """
    if not settings.trust_proxy_headers:
        return request.client.host if request.client else None

    # 信任代理头模式：优先 X-Forwarded-For 的第一个 IP
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        for ip in xff.split(","):
            ip = ip.strip()
            if ip:
                return ip

    # 其次使用 X-Real-IP
    xri = request.headers.get("X-Real-IP")
    if xri and xri.strip():
        return xri.strip()

    # 回退到直接连接的客户端地址
    return request.client.host if request.client else None


async def verify_token(request: Request, authorization: Annotated[str | None, Header()] = None):
    """FastAPI 依赖：先检查白名单，再验证 JWT 令牌"""
    # 白名单 IP 免认证
    client_ip = resolve_client_ip(request)
    if settings.auth_whitelist_ips and client_ip:
        if ip_in_whitelist(client_ip, settings.auth_whitelist_ips):
            logger.info(f"IP白名单绕过认证成功 client_ip={client_ip}")
            return
    # JWT 令牌验证
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
        _ = jwt.decode(token, settings.admin_password, algorithms=[_ALGORITHM])
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
