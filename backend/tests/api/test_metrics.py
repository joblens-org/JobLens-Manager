"""metrics路由的API端点测试"""
import pytest
pytestmark = pytest.mark.docker
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from backend.main import app


class TestMetricsAPI:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_services(self):
        from backend.routers import metrics as metrics_module

        original_registry = metrics_module.registry_service
        original_collector = metrics_module.collector_service

        registry_mock = AsyncMock()
        collector_mock = AsyncMock()
        metrics_module.registry_service = registry_mock
        metrics_module.collector_service = collector_mock

        yield {
            "registry": registry_mock,
            "collector": collector_mock
        }

        metrics_module.registry_service = original_registry
        metrics_module.collector_service = original_collector

    @pytest.fixture
    def sample_service(self):
        from backend.models.service import ServiceInfo
        return ServiceInfo(
            service_id="svc-123",
            name="test-service",
            host="localhost",
            port=8080,
            base_url="http://localhost:8080",
            version="1.0.0",
            status="healthy",
            registered_at=datetime.now().isoformat(),
            last_heartbeat=datetime.now().isoformat()
        )

    @pytest.fixture
    def sample_collector_perf(self):
        from backend.models.metrics import CollectorPerf
        return CollectorPerf(
            name="collector-1",
            call_cnt=100,
            err_cnt=0,
            max_us=500.0,
            mean_us=50.0,
            min_us=1.0,
            variance=25.0
        )

    @pytest.fixture
    def sample_writer_perf(self):
        from backend.models.metrics import WriterPerf
        return WriterPerf(
            name="writer-1",
            call_cnt=1000,
            err_cnt=0,
            max_us=100.0,
            mean_us=10.0,
            min_us=0.5,
            variance=5.0
        )

    # ─── GET /services/{service_id}/collectors - 采集器性能 ───

    @pytest.mark.asyncio
    def test_get_collector_perf_success(self, client, mock_services, sample_service, sample_collector_perf):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_collector_perf.return_value = [sample_collector_perf]
        response = client.get("/api/metrics/services/svc-123/collectors")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "collector-1"

    @pytest.mark.asyncio
    def test_get_collector_perf_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.get("/api/metrics/services/ghost/collectors")
        assert response.status_code == 404

    # ─── GET /services/{service_id}/writers - Writer性能 ───

    @pytest.mark.asyncio
    def test_get_writer_perf_success(self, client, mock_services, sample_service, sample_writer_perf):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_writer_perf.return_value = [sample_writer_perf]
        response = client.get("/api/metrics/services/svc-123/writers")
        assert response.status_code == 200
        assert response.json()[0]["name"] == "writer-1"

    @pytest.mark.asyncio
    def test_get_writer_perf_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.get("/api/metrics/services/ghost/writers")
        assert response.status_code == 404

    # ─── GET /services/{service_id}/writers/{writer_name} - Writer详情 ───

    @pytest.mark.asyncio
    def test_get_writer_info_success(self, client, mock_services, sample_service):
        from backend.models.metrics import WriterInfo
        mock_services["registry"].get_service.return_value = sample_service
        writer_info = WriterInfo(
            name="writer-1",
            type="file",
            config={"path": "/tmp/test"},
            status="running",
            metrics_written=5000
        )
        mock_services["collector"].get_writer_info.return_value = writer_info
        response = client.get("/api/metrics/services/svc-123/writers/writer-1")
        assert response.status_code == 200
        assert response.json()["name"] == "writer-1"

    @pytest.mark.asyncio
    def test_get_writer_info_not_found(self, client, mock_services, sample_service):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_writer_info.return_value = None
        response = client.get("/api/metrics/services/svc-123/writers/ghost")
        assert response.status_code == 404

    @pytest.mark.asyncio
    def test_get_writer_info_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.get("/api/metrics/services/ghost/writers/writer-1")
        assert response.status_code == 404

    # ─── GET /services/{service_id}/all - 全部指标 ───

    @pytest.mark.asyncio
    def test_get_all_metrics_success(self, client, mock_services, sample_service, sample_collector_perf, sample_writer_perf):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_collector_perf.return_value = [sample_collector_perf]
        mock_services["collector"].get_writer_perf.return_value = [sample_writer_perf]
        response = client.get("/api/metrics/services/svc-123/all")
        assert response.status_code == 200
        data = response.json()
        assert data["service_id"] == "svc-123"
        assert len(data["collectors"]) == 1
        assert len(data["writers"]) == 1

    @pytest.mark.asyncio
    def test_get_all_metrics_partial_failure(self, client, mock_services, sample_service, sample_collector_perf):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_collector_perf.return_value = [sample_collector_perf]
        mock_services["collector"].get_writer_perf.side_effect = Exception("Writer不可达")
        response = client.get("/api/metrics/services/svc-123/all")
        assert response.status_code == 200
        data = response.json()
        assert len(data["collectors"]) == 1
        assert len(data["writers"]) == 0

    # ─── GET /services/{service_id}/prometheus - Prometheus指标 ───

    @pytest.mark.asyncio
    def test_get_prometheus_metrics_success(self, client, mock_services, sample_service):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_prometheus_metrics.return_value = "# HELP test\n# TYPE test gauge\ntest 1"
        response = client.get("/api/metrics/services/svc-123/prometheus")
        assert response.status_code == 200
        assert "HELP" in response.json()["content"]

    @pytest.mark.asyncio
    def test_get_prometheus_metrics_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.get("/api/metrics/services/ghost/prometheus")
        assert response.status_code == 404

    # ─── GET /registry - 注册中心指标 ───

    @pytest.mark.asyncio
    def test_get_registry_metrics_success(self, client, mock_services):
        from backend.models.service import RegistryHealth, RegistryStats
        mock_services["registry"].get_registry_health.return_value = RegistryHealth(status="healthy", details={"version": "3.5.0"})
        mock_services["registry"].get_registry_stats.return_value = RegistryStats(
            total_services=10, healthy_services=8, unhealthy_services=2,
            status_distribution={}, heartbeat_interval=30.0,
            service_timeout=60.0, timestamp=datetime.now()
        )
        response = client.get("/api/metrics/registry")
        assert response.status_code == 200
        data = response.json()
        assert data["registry_health"]["status"] == "healthy"
        assert data["registry_stats"]["total_services"] == 10

    @pytest.mark.asyncio
    def test_get_registry_metrics_error(self, client, mock_services):
        mock_services["registry"].get_registry_health.side_effect = Exception("注册中心错误")
        response = client.get("/api/metrics/registry")
        assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
