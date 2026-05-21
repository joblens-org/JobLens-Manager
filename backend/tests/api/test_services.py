"""services路由的API端点测试"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from backend.main import app


class TestServicesAPI:
    """services路由API测试类"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    def sample_service_info(self):
        """示例服务信息"""
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
    
    @pytest.fixture
    def sample_service_info_model(self, sample_service_info):
        """ServiceInfo模型实例"""
        from backend.models.service import ServiceInfo
        return ServiceInfo(**sample_service_info)
    
    @pytest.fixture
    def mock_services(self):
        """Mock的服务层"""
        # 需要直接mock registry_service 和 collector_service 实例
        from backend.routers import services
        
        with patch('backend.services.registry_service.get_etcd_client') as mock_etcd:
            
            # 保存原始实例
            original_registry = services.registry_service
            original_collector = services.collector_service
            
            # 创建Mock服务实例并替换
            registry_mock = AsyncMock()
            services.registry_service = registry_mock
            
            collector_mock = AsyncMock()
            services.collector_service = collector_mock
            
            # Mock ETCD客户端
            etcd_mock = Mock()
            etcd_mock.get.return_value = (None, None)
            
            yield {
                "registry": registry_mock,
                "collector": collector_mock
            }
            
            # 恢复原始实例
            services.registry_service = original_registry
            services.collector_service = original_collector
    
    def test_list_services_success(self, client, mock_services, sample_service_info_model):
        """测试获取服务列表成功"""
        # 准备mock数据
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        
        # 执行请求
        response = client.get("/api/services")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1
        assert data["total"] == 1
        # FastAPI 使用别名序列化，所以检查 id 而不是 service_id
        assert data["services"][0]["id"] == "test-service-123"
        assert data["services"][0]["name"] == "test-service"
        
        mock_services["registry"].get_services.assert_called_once_with(healthy_only=False)
    
    def test_list_services_healthy_only(self, client, mock_services, sample_service_info_model):
        """测试仅获取健康服务"""
        # 准备mock数据
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        
        # 执行请求
        response = client.get("/api/services?healthy_only=true")
        
        # 验证
        assert response.status_code == 200
        mock_services["registry"].get_services.assert_called_once_with(healthy_only=True)
    
    def test_list_services_with_mode_filter(self, client, mock_services, sample_service_info_model):
        """测试按模式筛选服务"""
        # 准备mock数据（属性已经由 registry_service 合并到服务中）
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        
        # 执行请求
        response = client.get("/api/services?mode=production")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1
        assert data["total"] == 1  # 匹配模式
    
    def test_list_services_with_role_filter(self, client, mock_services, sample_service_info_model):
        """测试按角色筛选服务"""
        # 准备mock数据（属性已经由 registry_service 合并到服务中）
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        
        # 执行请求
        response = client.get("/api/services?role_id=role-123")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1
        assert data["total"] == 1  # 匹配角色
    
    def test_list_services_filter_no_match(self, client, mock_services, sample_service_info_model):
        """测试筛选无匹配结果"""
        # 准备mock数据（属性已经由 registry_service 合并到服务中）
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        
        # 执行请求（模式不匹配，使用一个不同的模式）
        response = client.get("/api/services?mode=nonexistent")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 0
        assert data["total"] == 0  # 无匹配

    def test_list_services_with_search(self, client, mock_services, sample_service_info_model):
        """测试按关键词搜索服务"""
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        response = client.get("/api/services?search=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1
        assert data["total"] == 1

    def test_list_services_with_search_no_match(self, client, mock_services, sample_service_info_model):
        """测试搜索无匹配结果"""
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        response = client.get("/api/services?search=notexist")
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 0
        assert data["total"] == 0

    def test_list_services_search_case_insensitive(self, client, mock_services, sample_service_info_model):
        """测试搜索大小写不敏感"""
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        response = client.get("/api/services?search=TEST-SERVICE")
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1

    def test_list_services_search_by_host(self, client, mock_services, sample_service_info_model):
        """测试按主机地址搜索"""
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        response = client.get("/api/services?search=localhost")
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1

    def test_list_services_search_by_id(self, client, mock_services, sample_service_info_model):
        """测试按服务ID搜索"""
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        response = client.get("/api/services?search=test-service-123")
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1

    def test_list_services_search_with_empty_string(self, client, mock_services, sample_service_info_model):
        """测试空搜索字符串不过滤"""
        mock_services["registry"].get_services.return_value = [sample_service_info_model]
        response = client.get("/api/services?search=")
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1  # 空搜索不过滤
        assert data["total"] == 1
    
    def test_get_service_success(self, client, mock_services, sample_service_info_model):
        """测试获取单个服务成功"""
        # 准备mock数据
        mock_services["registry"].get_service.return_value = sample_service_info_model
        
        # 执行请求
        response = client.get("/api/services/test-service-123")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        # FastAPI 使用别名序列化，所以检查 id 而不是 service_id
        assert data["id"] == "test-service-123"
        assert data["name"] == "test-service"
        mock_services["registry"].get_service.assert_called_once_with("test-service-123")
    
    def test_get_service_not_found(self, client, mock_services):
        """测试获取不存在的服务"""
        # 准备mock数据（返回None）
        mock_services["registry"].get_service.return_value = None
        
        # 执行请求
        response = client.get("/api/services/non-existent")
        
        # 验证
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "服务不存在" in data["detail"]
    
    def test_get_service_health_success(self, client, mock_services, sample_service_info_model):
        """测试获取服务健康状态成功"""
        # 准备mock数据
        mock_services["registry"].get_service.return_value = sample_service_info_model
        mock_services["collector"].check_health.return_value = True
        
        # 执行请求
        response = client.get("/api/services/test-service-123/health")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["service_id"] == "test-service-123"
        assert data["name"] == "test-service"
        assert data["registry_healthy"] is True
        assert data["collector_healthy"] is True
        
        mock_services["registry"].get_service.assert_called_once_with("test-service-123")
        mock_services["collector"].check_health.assert_called_once_with("localhost", 8080)
    
    def test_get_service_health_not_found(self, client, mock_services):
        """测试获取不存在的服务健康状态"""
        # 准备mock数据
        mock_services["registry"].get_service.return_value = None
        
        # 执行请求
        response = client.get("/api/services/non-existent/health")
        
        # 验证
        assert response.status_code == 404
    
    def test_delete_service_success(self, client, mock_services):
        """测试删除服务成功"""
        # 准备mock数据
        mock_services["registry"].unregister_service.return_value = True
        
        # 执行请求
        response = client.delete("/api/services/test-service-123")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "服务已注销"
        assert data["service_id"] == "test-service-123"
        mock_services["registry"].unregister_service.assert_called_once_with("test-service-123")
    
    def test_delete_service_not_found(self, client, mock_services):
        """测试删除不存在的服务"""
        # 准备mock数据
        mock_services["registry"].unregister_service.return_value = False
        
        # 执行请求
        response = client.delete("/api/services/non-existent")
        
        # 验证
        assert response.status_code == 404
        mock_services["registry"].unregister_service.assert_called_once_with("non-existent")
    
    def test_get_registry_health_success(self, client, mock_services):
        """测试获取注册中心健康状态成功"""
        # 准备mock数据
        from backend.models.service import RegistryHealth
        mock_health = RegistryHealth(
            status="healthy",
            details={"version": "1.0.0", "uptime": "10 days"}
        )
        mock_services["registry"].get_registry_health.return_value = mock_health
        
        # 执行请求
        response = client.get("/api/services/registry/health")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data["details"]
        mock_services["registry"].get_registry_health.assert_called_once()
    
    def test_get_registry_stats_success(self, client, mock_services):
        """测试获取注册中心统计信息成功"""
        # 准备mock数据
        from backend.models.service import RegistryStats
        import datetime
        mock_stats = RegistryStats(
            total_services=100,
            status_distribution={"healthy": 80, "unhealthy": 20},
            healthy_services=80,
            unhealthy_services=20,
            heartbeat_interval=30.0,
            service_timeout=60.0,
            timestamp=datetime.datetime.now()
        )
        mock_services["registry"].get_registry_stats.return_value = mock_stats
        
        # 执行请求
        response = client.get("/api/services/registry/stats")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["total_services"] == 100
        assert data["healthy_services"] == 80
        assert data["unhealthy_services"] == 20
        mock_services["registry"].get_registry_stats.assert_called_once()
    
    def test_update_service_attributes_success(self, client, mock_services, sample_service_info_model):
        """测试更新服务属性成功"""
        # 准备mock数据
        mock_services["registry"].get_service.return_value = sample_service_info_model
        
        # 准备mock依赖函数
        with patch('backend.routers.services.is_mode_exist', return_value=True), \
             patch('backend.routers.services.is_role_exist', return_value=True):
            
            # 执行请求
            update_data = {
                "mode": "production",
                "role_id": "role-456"
            }
            response = client.put(
                "/api/services/test-service-123/attributes",
                json=update_data
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "服务属性已更新"
            assert data["service_id"] == "test-service-123"
            assert "attributes" in data
            assert data["attributes"]["mode"] == "production"
            assert data["attributes"]["role_id"] == "role-456"
    
    def test_update_service_attributes_not_found(self, client, mock_services):
        """测试更新不存在的服务属性"""
        # 准备mock数据
        mock_services["registry"].get_service.return_value = None
        
        # 执行请求
        response = client.put(
            "/api/services/non-existent/attributes",
            json={"mode": "production"}
        )
        
        # 验证
        assert response.status_code == 404
        mock_services["registry"].get_service.assert_called_once_with("non-existent")
    
    def test_update_service_attributes_partial(self, client, mock_services, sample_service_info_model):
        """测试部分更新服务属性"""
        # 准备mock数据
        mock_services["registry"].get_service.return_value = sample_service_info_model
        
        # 准备mock依赖函数
        with patch('backend.routers.services.is_mode_exist', return_value=True):
            # 执行请求（只更新模式）
            update_data = {"mode": "new-mode"}
            response = client.put(
                "/api/services/test-service-123/attributes",
                json=update_data
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            attributes = data["attributes"]
            assert attributes["mode"] == "new-mode"
    
    def test_list_services_registry_error(self, client, mock_services, sample_service_info_model):
        """测试注册中心服务错误"""
        # 模拟注册中心服务错误
        mock_services["registry"].get_services.side_effect = Exception("Registry service error")
        
        # 执行请求
        response = client.get("/api/services")
        
        # 验证
        assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])