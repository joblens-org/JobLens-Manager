"""深度健康检查。

与 /health 的分工：
- /health 保持极简，供容器 healthcheck / 反代存活探测高频调用；
- /api/health/deep 真正检查依赖（etcd 与注册中心），供巡检与人工排障低频调用。

挂在受保护的 /api 路由下：外部访问需要令牌，部署机本机（127.0.0.1 / 白名单网段）免认证。
"""

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.common import get_etcd_client
from backend.common.logger import logger
from backend.config import settings

router = APIRouter()


@router.get("/deep", summary="深度健康检查（etcd + 注册中心）")
async def deep_health():
    """检查后端自身依赖是否可用。

    Returns:
        200 healthy：etcd 与注册中心均正常；
        503 degraded：至少一个依赖异常（响应体给出具体项，便于归因）。
    """
    checks = {}
    healthy = True

    # ---- etcd ----
    try:
        client = get_etcd_client()
        status = client.status()
        checks["etcd"] = {
            "status": "ok",
            "leader": getattr(status, "leader", None),
            "raft_index": getattr(status, "raftIndex", None),
            "db_size": getattr(status, "dbSize", None),
        }
    except Exception as exc:  # 连接失败 / 超时 / 证书等
        healthy = False
        checks["etcd"] = {"status": "error", "error": str(exc)[:200]}
        logger.warning(f"深度健康检查：etcd 异常: {exc}")

    # ---- 注册中心 ----
    registry_url = f"{settings.registry_url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(registry_url)
        payload = response.json() if response.content else {}
        details = payload.get("details") or {}
        ok = response.status_code == 200 and payload.get("status") == "healthy"
        if not ok:
            healthy = False
            logger.warning(f"深度健康检查：注册中心异常 HTTP {response.status_code}")
        checks["registry"] = {
            "status": "ok" if ok else "error",
            "http_status": response.status_code,
            "registered_services": details.get("registered_services"),
            "healthy_services": details.get("healthy_services"),
        }
    except Exception as exc:
        healthy = False
        checks["registry"] = {"status": "error", "error": str(exc)[:200]}
        logger.warning(f"深度健康检查：注册中心不可达: {exc}")

    body = {
        "status": "healthy" if healthy else "degraded",
        "checks": checks,
    }
    return JSONResponse(status_code=200 if healthy else 503, content=body)
