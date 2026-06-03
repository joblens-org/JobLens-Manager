"""
认证路由：管理员密码登录。
"""
import secrets
from fastapi import APIRouter, HTTPException
from backend.models.auth import LoginRequest, LoginResponse
from backend.common.auth import create_token
from backend.common.logger import logger
from backend.config import settings

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """管理员密码登录，返回 JWT 令牌"""
    if not settings.admin_password:
        raise HTTPException(status_code=500, detail="服务器未配置管理员密码")
    if not secrets.compare_digest(body.password, settings.admin_password):
        logger.warning("登录失败：密码错误")
        raise HTTPException(status_code=401, detail="密码错误")
    token = create_token()
    logger.info("管理员登录成功")
    return LoginResponse(token=token)
