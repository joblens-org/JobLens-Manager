"""深度健康检查 /api/health/deep 的端点测试。"""

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


class _Resp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.content = b"{}"
        self._payload = payload

    def json(self):
        return self._payload


class _Client:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url):
        return self._response


def _etcd_ok():
    return SimpleNamespace(
        status=lambda: SimpleNamespace(
            version="3.5.26",
            db_size=1024,
            leader=SimpleNamespace(id=7),
            raft_index=42,
            raft_term=3,
        )
    )


def _etcd_broken():
    def boom():
        raise ConnectionError("etcd unreachable")

    return SimpleNamespace(status=boom)


def _patch(etcd_client, registry_response):
    return (
        patch("backend.routers.health.get_etcd_client", return_value=etcd_client),
        patch(
            "backend.routers.health.httpx.AsyncClient",
            lambda *args, **kwargs: _Client(registry_response),
        ),
    )


def _request():
    with TestClient(app) as client:
        return client.get("/api/health/deep")


def test_deep_health_ok():
    registry = _Resp(
        200, {"status": "healthy", "details": {"registered_services": 10, "healthy_services": 9}}
    )
    etcd_patch, registry_patch = _patch(_etcd_ok(), registry)
    with etcd_patch, registry_patch:
        response = _request()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["etcd"]["status"] == "ok"
    assert body["checks"]["etcd"]["raft_index"] == 42
    assert body["checks"]["registry"]["status"] == "ok"
    assert body["checks"]["registry"]["registered_services"] == 10


def test_deep_health_etcd_failure_is_degraded():
    registry = _Resp(200, {"status": "healthy", "details": {}})
    etcd_patch, registry_patch = _patch(_etcd_broken(), registry)
    with etcd_patch, registry_patch:
        response = _request()

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["etcd"]["status"] == "error"
    assert body["checks"]["registry"]["status"] == "ok"


def test_deep_health_registry_http_error_is_degraded():
    registry = _Resp(500, {"status": "error"})
    etcd_patch, registry_patch = _patch(_etcd_ok(), registry)
    with etcd_patch, registry_patch:
        response = _request()

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["registry"]["status"] == "error"
    assert body["checks"]["registry"]["http_status"] == 500


def test_deep_health_registry_unhealthy_payload_is_degraded():
    registry = _Resp(200, {"status": "unhealthy", "details": {}})
    etcd_patch, registry_patch = _patch(_etcd_ok(), registry)
    with etcd_patch, registry_patch:
        response = _request()

    assert response.status_code == 503
    assert response.json()["checks"]["registry"]["status"] == "error"
