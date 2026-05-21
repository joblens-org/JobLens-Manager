"""RegistryService的服务层测试"""
import pytest
import httpx
import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from backend.services.registry_service import RegistryService
from backend.models import ServiceInfo, RegistryStats, RegistryHealth


class TestRegistryService:
    """RegistryService测试类"""
    
    @pytest.fixture
    def service(self):
        """RegistryService实例"""
        return RegistryService()
    
    @pytest.fixture
    def mock_client(self, service):
        """Mock HTTP客户端"""
        mock_client = AsyncMock()
        service.client = mock_client
        service.base_url = "http://test-registry:8080"
        # Mock ETCD 客户端，返回空属性以免覆盖服务自带的 mode/role_id
        etcd_mock = Mock()
        etcd_mock.get.return_value = (None, None)
        etcd_mock.get_prefix.return_value = []
        service.etcd_client = etcd_mock
        return mock_client
    
    @pytest.fixture
    def sample_service_data(self):
        """示例服务数据"""
        return {
            "id": "test-service-123",
            "host": "localhost",
            "port": 8080,
            "name": "test-service",
            "version": "1.0.0",
            "base_url": "http://localhost:8080",
            "status": "healthy",
            "registered_at": "2024-01-01T00:00:00Z",
            "last_heartbeat": "2024-01-01T00:10:00Z",
            "mode": "production",
            "role_id": "role-123",
            "metadata": {"environment": "test"}
        }
    
    @pytest.mark.asyncio
    async def test_get_services(self, service, mock_client):
        """测试获取服务列表"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "service-1",
                "host": "host1",
                "port": 8080,
                "name": "service1",
                "version": "1.0.0",
                "base_url": "http://host1:8080",
                "status": "healthy",
                "registered_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "service-2",
                "host": "host2",
                "port": 8081,
                "name": "service2",
                "version": "1.0.0",
                "base_url": "http://host2:8081",
                "status": "unhealthy",
                "registered_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_client.get.return_value = mock_response
        
        # 执行测试
        services = await service.get_services()
        
        # 验证
        assert len(services) == 2
        assert services[0].service_id == "service-1"
        assert services[1].service_id == "service-2"
        mock_client.get.assert_called_once_with(
            "http://test-registry:8080/services",
            params={"healthy_only": "false"}
        )
    
    @pytest.mark.asyncio
    async def test_get_services_healthy_only(self, service, mock_client):
        """测试仅获取健康服务"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "service-1",
                "host": "host1",
                "port": 8080,
                "name": "service1",
                "version": "1.0.0",
                "base_url": "http://host1:8080",
                "status": "healthy",
                "registered_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_client.get.return_value = mock_response
        
        # 执行测试
        services = await service.get_services(healthy_only=True)
        
        # 验证
        assert len(services) == 1
        assert services[0].service_id == "service-1"
        mock_client.get.assert_called_once_with(
            "http://test-registry:8080/services",
            params={"healthy_only": "true"}
        )
    
    @pytest.mark.asyncio
    async def test_get_service_found(self, service, mock_client, sample_service_data):
        """测试获取存在的服务"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_service_data
        mock_client.get.return_value = mock_response
        
        # 执行测试
        service_info = await service.get_service("test-service-123")
        
        # 验证
        assert service_info is not None
        assert service_info.service_id == "test-service-123"
        assert service_info.name == "test-service"
        assert service_info.mode == "production"
        assert service_info.role_id == "role-123"
        mock_client.get.assert_called_once_with(
            "http://test-registry:8080/services/test-service-123"
        )
    
    @pytest.mark.asyncio
    async def test_get_service_not_found(self, service, mock_client):
        """测试获取不存在的服务"""
        # 准备mock响应（404）
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        
        # 执行测试
        service_info = await service.get_service("non-existent")
        
        # 验证
        assert service_info is None
        mock_client.get.assert_called_once_with(
            "http://test-registry:8080/services/non-existent"
        )
    
    @pytest.mark.asyncio
    async def test_get_service_http_error(self, service, mock_client):
        """测试获取服务时发生HTTP错误"""
        # 准备mock响应（500错误）
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")
        mock_client.get.return_value = mock_response
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Server error"):
            await service.get_service("service-123")
    
    @pytest.mark.asyncio
    async def test_unregister_service_success(self, service, mock_client):
        """测试成功注销服务"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.delete.return_value = mock_response
        
        # 执行测试
        result = await service.unregister_service("service-123")
        
        # 验证
        assert result is True
        mock_client.delete.assert_called_once_with(
            "http://test-registry:8080/unregister/service-123"
        )
    
    @pytest.mark.asyncio
    async def test_unregister_service_not_found(self, service, mock_client):
        """测试注销不存在的服务"""
        # 准备mock响应（404）
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.delete.return_value = mock_response
        
        # 执行测试
        result = await service.unregister_service("non-existent")
        
        # 验证
        assert result is False
        mock_client.delete.assert_called_once_with(
            "http://test-registry:8080/unregister/non-existent"
        )
    
    @pytest.mark.asyncio
    async def test_unregister_service_http_error(self, service, mock_client):
        """测试注销服务时发生HTTP错误"""
        # 准备mock响应（500错误）
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")
        mock_client.delete.return_value = mock_response
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Server error"):
            await service.unregister_service("service-123")
    
    @pytest.mark.asyncio
    async def test_get_registry_health(self, service, mock_client):
        """测试获取注册中心健康状态"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "details": {"version": "1.0.0", "uptime": "10 days"}
        }
        mock_client.get.return_value = mock_response
        
        # 执行测试
        health = await service.get_registry_health()
        
        # 验证
        assert isinstance(health, RegistryHealth)
        assert health.status == "healthy"
        assert health.details["version"] == "1.0.0"
        mock_client.get.assert_called_once_with("http://test-registry:8080/health")
    
    @pytest.mark.asyncio
    async def test_get_registry_stats(self, service, mock_client):
        """测试获取注册中心统计信息"""
        # 准备mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_services": 100,
            "status_distribution": {"healthy": 80, "unhealthy": 20},
            "heartbeat_interval": 30.0,
            "service_timeout": 60.0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        mock_client.get.return_value = mock_response
        
        # 执行测试
        stats = await service.get_registry_stats()
        
        # 验证
        assert isinstance(stats, RegistryStats)
        assert stats.total_services == 100
        assert stats.status_distribution["healthy"] == 80
        assert stats.healthy_services == 80
        assert stats.unhealthy_services == 20
        assert stats.heartbeat_interval == 30.0
        assert stats.service_timeout == 60.0
        mock_client.get.assert_called_once_with("http://test-registry:8080/stats")
    
    @pytest.mark.asyncio
    async def test_close(self, service, mock_client):
        """测试关闭客户端连接"""
        # 执行测试
        await service.close()
        
        # 验证
        mock_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_timeout_handling(self, service, mock_client):
        """测试HTTP超时处理"""
        # 模拟超时异常
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
        
        # 执行测试并验证异常
        with pytest.raises(httpx.TimeoutException):
            await service.get_services()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])