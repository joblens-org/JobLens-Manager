"""CollectorService的服务层测试"""
import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from backend.services.collector_service import CollectorService
from backend.models import (
    JobInfo,
    JobCount,
    CollectorPerf,
    WriterPerf,
    WriterInfo,
    JobOperation,
    CondorJobOperation
)


class TestCollectorService:
    """CollectorService测试类"""
    
    @pytest.fixture
    def service(self):
        """CollectorService实例"""
        return CollectorService()
    
    @pytest.fixture
    def mock_client(self, service):
        """Mock HTTP客户端"""
        mock_client = AsyncMock()
        service.client = mock_client
        return mock_client
    
    @pytest.fixture
    def sample_job_info(self):
        """示例作业信息"""
        return {
            "JobID": 123,
            "jobtype": "condor",
            "subtype": "batch",
            "JobPIDs": [1001, 1002],
            "CollectorNames": ["collector1", "collector2"]
        }
    
    @pytest.fixture
    def sample_collector_perf(self):
        """示例采集器性能数据"""
        return {
            "name": "test-collector",
            "call_cnt": 1000,
            "err_cnt": 5,
            "max_us": 150.0,
            "mean_us": 45.3,
            "min_us": 10.0,
            "variance": 12.5,
        }
    
    @pytest.fixture
    def sample_writer_perf(self):
        """示例写入器性能数据"""
        return {
            "name": "test-writer",
            "call_cnt": 500,
            "err_cnt": 2,
            "max_us": 200.0,
            "mean_us": 35.1,
            "min_us": 8.0,
            "variance": 9.3,
        }
    
    @pytest.fixture
    def sample_writer_info(self):
        """示例写入器信息"""
        return {
            "name": "test-writer",
            "type": "file",
            "status": "active",
            "config": {"path": "/tmp/output.log"},
            "metrics_written": 100,
        }
    
    @pytest.mark.asyncio
    async def test_get_jobs(self, service, mock_client):
        """测试获取作业列表"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jobs": [
                {
                    "JobID": 1,
                    "jobtype": "condor",
                    "subtype": "batch",
                    "JobPIDs": [1001],
                    "CollectorNames": ["collector1"]
                },
                {
                    "JobID": 2,
                    "jobtype": "common",
                    "subtype": "interactive",
                    "JobPIDs": [2001],
                    "CollectorNames": ["collector2"]
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        # 执行测试
        jobs = await service.get_jobs("localhost", 7592)
        
        # 验证
        assert len(jobs) == 2
        assert jobs[0].JobID == 1
        assert jobs[1].JobID == 2
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/jobs"
        )
    
    @pytest.mark.asyncio
    async def test_get_job_found(self, service, mock_client, sample_job_info):
        """测试获取存在的作业"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_job_info
        mock_client.get.return_value = mock_response
        
        # 执行测试
        job_info = await service.get_job("localhost", 7592, "123")
        
        # 验证
        assert job_info is not None
        assert job_info.JobID == 123
        assert job_info.jobtype == "condor"
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/jobs/123"
        )
    
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, service, mock_client):
        """测试获取不存在的作业"""
        # 准备mock响应（404）
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        
        # 执行测试
        job_info = await service.get_job("localhost", 7592, "999")
        
        # 验证
        assert job_info is None
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/jobs/999"
        )
    
    @pytest.mark.asyncio
    async def test_add_job_condor(self, service, mock_client):
        """测试添加Condor作业"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response
        
        # 执行测试
        result = await service.add_job(
            host="localhost",
            port=7592,
            job_type="job.condor",
            job_id=123,
            job_pids=[1001, 1002],
            lens=["lens1", "lens2"],
            slot="slot-1"
        )
        
        # 验证
        assert result is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:7592/joblens/condor_job"
        # 验证请求体包含slot字段
        json_data = call_args[1]['json']
        assert json_data['JobID'] == 123
        assert json_data['slot'] == "slot-1"
        assert json_data['type'] == "job.condor"
    
    @pytest.mark.asyncio
    async def test_add_job_common(self, service, mock_client):
        """测试添加普通作业"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response
        
        # 执行测试
        result = await service.add_job(
            host="localhost",
            port=7592,
            job_type="job.common",
            job_id=456,
            job_pids=[3001],
            lens=["common-lens"]
        )
        
        # 验证
        assert result is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:7592/joblens/job"
        json_data = call_args[1]['json']
        assert json_data['JobID'] == 456
        assert json_data['opt'] == "add"
        assert json_data['type'] == "job.common"
    
    @pytest.mark.asyncio
    async def test_remove_job(self, service, mock_client):
        """测试移除作业"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response
        
        # 执行测试
        result = await service.remove_job(
            host="localhost",
            port=7592,
            job_type="job.condor",
            job_id=789
        )
        
        # 验证
        assert result is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:7592/joblens/job"
        json_data = call_args[1]['json']
        assert json_data['JobID'] == 789
        assert json_data['opt'] == "remove"
        assert json_data['type'] == "job.condor"
    
    @pytest.mark.asyncio
    async def test_get_collector_perf(self, service, mock_client, sample_collector_perf):
        """测试获取采集器性能"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "collectors_perf": [sample_collector_perf]
        }
        mock_client.get.return_value = mock_response
        
        # 执行测试
        collector_perfs = await service.get_collector_perf("localhost", 7592)
        
        # 验证
        assert len(collector_perfs) == 1
        assert collector_perfs[0].name == "test-collector"
        assert collector_perfs[0].call_cnt == 1000
        assert collector_perfs[0].mean_us == 45.3
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/collectors/perf"
        )
    
    @pytest.mark.asyncio
    async def test_get_collector_perf_error_status(self, service, mock_client):
        """测试获取采集器性能时状态错误"""
        # 准备mock响应（状态不为ok）
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "message": "Internal error"
        }
        mock_client.get.return_value = mock_response
        
        # 执行测试并验证异常
        with pytest.raises(Exception):
            await service.get_collector_perf("localhost", 7592)
    
    @pytest.mark.asyncio
    async def test_get_writer_perf(self, service, mock_client, sample_writer_perf):
        """测试获取写入器性能"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "writers_perf": [sample_writer_perf]
        }
        mock_client.get.return_value = mock_response
        
        # 执行测试
        writer_perfs = await service.get_writer_perf("localhost", 7592)
        
        # 验证
        assert len(writer_perfs) == 1
        assert writer_perfs[0].name == "test-writer"
        assert writer_perfs[0].call_cnt == 500
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/writers/perf"
        )
    
    @pytest.mark.asyncio
    async def test_get_writer_info_found(self, service, mock_client, sample_writer_info):
        """测试获取存在的写入器信息"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_writer_info
        mock_client.get.return_value = mock_response
        
        # 执行测试
        writer_info = await service.get_writer_info("localhost", 7592, "test-writer")
        
        # 验证
        assert writer_info is not None
        assert writer_info.name == "test-writer"
        assert writer_info.type == "file"
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/writers/test-writer/info"
        )
    
    @pytest.mark.asyncio
    async def test_get_writer_info_not_found(self, service, mock_client):
        """测试获取不存在的写入器信息"""
        # 准备mock响应（404）
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        
        # 执行测试
        writer_info = await service.get_writer_info("localhost", 7592, "non-existent")
        
        # 验证
        assert writer_info is None
    
    @pytest.mark.asyncio
    async def test_get_job_count(self, service, mock_client):
        """测试获取作业数量"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_count": 42,
            "status": "active"
        }
        mock_client.get.return_value = mock_response
        
        # 执行测试
        job_count = await service.get_job_count("localhost", 7592)
        
        # 验证
        assert job_count.job_count == 42
        assert job_count.status == "active"
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/jobs/count"
        )
    
    @pytest.mark.asyncio
    async def test_check_health_healthy(self, service, mock_client):
        """测试检查采集器健康状态（健康）"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"healthy": True})
        mock_client.get.return_value = mock_response
        
        # 执行测试
        is_healthy = await service.check_health("localhost", 7592)
        
        # 验证
        assert is_healthy is True
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/joblens/healthy"
        )
    
    @pytest.mark.asyncio
    async def test_check_health_unhealthy(self, service, mock_client):
        """测试检查采集器健康状态（不健康）"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"healthy": False})
        mock_client.get.return_value = mock_response
        
        # 执行测试
        is_healthy = await service.check_health("localhost", 7592)
        
        # 验证
        assert is_healthy is False
    
    @pytest.mark.asyncio
    async def test_check_health_exception(self, service, mock_client):
        """测试检查采集器健康状态时发生异常"""
        # 模拟异常
        mock_client.get.side_effect = Exception("Connection failed")
        
        # 执行测试
        is_healthy = await service.check_health("localhost", 7592)
        
        # 验证
        assert is_healthy is False
    
    @pytest.mark.asyncio
    async def test_get_prometheus_metrics(self, service, mock_client):
        """测试获取Prometheus指标"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "# HELP test_metric Test metric\n# TYPE test_metric counter\ntest_metric 123"
        mock_client.get.return_value = mock_response
        
        # 执行测试
        metrics = await service.get_prometheus_metrics("localhost", 7592)
        
        # 验证
        assert "test_metric" in metrics
        mock_client.get.assert_called_once_with(
            "http://localhost:7592/metrics"
        )
    
    @pytest.mark.asyncio
    async def test_close(self, service, mock_client):
        """测试关闭客户端连接"""
        # 执行测试
        await service.close()
        
        # 验证
        mock_client.aclose.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])