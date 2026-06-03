"""jobs路由的API端点测试"""
import pytest
pytestmark = pytest.mark.docker
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from backend.main import app


class TestJobsAPI:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_services(self):
        from backend.routers import jobs as jobs_module

        original_registry = jobs_module.registry_service
        original_collector = jobs_module.collector_service

        registry_mock = AsyncMock()
        collector_mock = AsyncMock()
        jobs_module.registry_service = registry_mock
        jobs_module.collector_service = collector_mock

        yield {
            "registry": registry_mock,
            "collector": collector_mock
        }

        jobs_module.registry_service = original_registry
        jobs_module.collector_service = original_collector

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
    def sample_job(self):
        from backend.models.job import JobInfo
        return JobInfo(
            JobID=1,
            jobtype="job",
            subtype="common",
            JobPIDs=[1001],
            CollectorNames=["collector-1"]
        )

    # ─── GET / - 获取所有作业 ───

    @pytest.mark.asyncio
    def test_list_all_jobs_success(self, client, mock_services, sample_service, sample_job):
        mock_services["registry"].get_services.return_value = [sample_service]
        mock_services["collector"].get_jobs.return_value = [sample_job]
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["service_id"] == "svc-123"

    @pytest.mark.asyncio
    def test_list_all_jobs_filter_by_service(self, client, mock_services, sample_service, sample_job):
        mock_services["registry"].get_services.return_value = [sample_service]
        mock_services["collector"].get_jobs.return_value = [sample_job]
        response = client.get("/api/jobs?service_ids=svc-123")
        assert response.status_code == 200

    @pytest.mark.asyncio
    def test_list_all_jobs_empty(self, client, mock_services):
        mock_services["registry"].get_services.return_value = []
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert response.json() == []

    # ─── GET /{job_id} - 获取作业详情 ───

    @pytest.mark.asyncio
    def test_get_job_success(self, client, mock_services, sample_service, sample_job):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_job.return_value = sample_job
        response = client.get("/api/jobs/1?service_id=svc-123")
        assert response.status_code == 200
        assert response.json()["JobID"] == 1

    @pytest.mark.asyncio
    def test_get_job_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.get("/api/jobs/1?service_id=ghost")
        assert response.status_code == 404

    @pytest.mark.asyncio
    def test_get_job_not_found(self, client, mock_services, sample_service):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_job.return_value = None
        response = client.get("/api/jobs/999?service_id=svc-123")
        assert response.status_code == 404

    # ─── POST / - 创建作业 ───

    @pytest.mark.asyncio
    def test_create_job_success(self, client, mock_services, sample_service, sample_job):
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_job.return_value = sample_job
        response = client.post("/api/jobs", json={
            "service_id": "svc-123",
            "job_type": "job.common",
            "job_id": 1,
            "job_pids": [1001],
            "lens": ["test_lens"]
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    def test_create_job_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.post("/api/jobs", json={
            "service_id": "ghost",
            "job_type": "job.common",
            "job_id": 1,
            "job_pids": [1001],
            "lens": ["test"]
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    def test_create_condor_job_without_slot(self, client, mock_services, sample_service):
        mock_services["registry"].get_service.return_value = sample_service
        response = client.post("/api/jobs", json={
            "service_id": "svc-123",
            "job_type": "job.condor",
            "job_id": 1,
            "job_pids": [1001],
            "lens": ["test"]
        })
        assert response.status_code == 400

    # ─── DELETE /{job_id} - 删除作业 ───

    @pytest.mark.asyncio
    def test_delete_job_success(self, client, mock_services, sample_service):
        mock_services["registry"].get_service.return_value = sample_service
        response = client.delete("/api/jobs/1?service_id=svc-123&job_type=job.common")
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]

    @pytest.mark.asyncio
    def test_delete_job_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.delete("/api/jobs/1?service_id=ghost&job_type=job.common")
        assert response.status_code == 404

    # ─── GET /{service_id}/count - 作业数量 ───

    @pytest.mark.asyncio
    def test_get_job_count_success(self, client, mock_services, sample_service):
        from backend.models.job import JobCount
        mock_services["registry"].get_service.return_value = sample_service
        mock_services["collector"].get_job_count.return_value = JobCount(job_count=5, status="healthy")
        response = client.get("/api/jobs/svc-123/count")
        assert response.status_code == 200
        assert response.json()["job_count"] == 5

    @pytest.mark.asyncio
    def test_get_job_count_service_not_found(self, client, mock_services):
        mock_services["registry"].get_service.return_value = None
        response = client.get("/api/jobs/ghost/count")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
