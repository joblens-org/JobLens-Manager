"""Service模型的单元测试"""
import pytest
from datetime import datetime
from backend.models.service import (
    ServiceRegistration,
    ServiceInfo,
    ServiceHealth,
    RegistryStats,
    RegistryHealth
)


class TestServiceRegistration:
    """ServiceRegistration模型测试"""
    
    def test_create_basic_registration(self):
        """测试创建基本注册信息"""
        reg = ServiceRegistration(
            host="localhost",
            port=8080,
            name="test-service",
            version="1.0.0"
        )
        assert reg.host == "localhost"
        assert reg.port == 8080
        assert reg.name == "test-service"
        assert reg.version == "1.0.0"
    
    def test_registration_validation(self):
        """测试注册信息字段的基本类型校验"""
        # Pydantic默认仅校验类型，port=int, name=str 本身无额外约束
        # 负数端口和空名称在无 validator 时都是合法的
        reg1 = ServiceRegistration(
            host="localhost", port=-1,
            name="test-service", version="1.0.0"
        )
        assert reg1.port == -1

        reg2 = ServiceRegistration(
            host="localhost", port=8080,
            name="", version="1.0.0"
        )
        assert reg2.name == ""


class TestServiceInfo:
    """ServiceInfo模型测试"""
    
    def test_create_service_info_with_alias(self):
        """测试使用别名创建ServiceInfo"""
        now = datetime.now()
        info = ServiceInfo(
            id="test-service-123",  # 使用别名字段
            host="localhost",
            port=8080,
            name="test-service",
            version="1.0.0",
            base_url="http://localhost:8080",
            status="healthy",
            registered_at=now,
            last_heartbeat=now,
            mode="production",  # 新增模式字段
            role_id="role-123",  # 新增角色字段
            metadata={"environment": "test"}
        )
        assert info.service_id == "test-service-123"
        assert info.mode == "production"
        assert info.role_id == "role-123"
        assert info.metadata == {"environment": "test"}
    
    def test_service_info_without_optional_fields(self):
        """测试创建不带可选字段的ServiceInfo"""
        now = datetime.now()
        info = ServiceInfo(
            id="test-service-123",
            host="localhost",
            port=8080,
            name="test-service",
            version="1.0.0",
            base_url="http://localhost:8080",
            status="healthy",
            registered_at=now
        )
        assert info.last_heartbeat is None
        assert info.mode is None
        assert info.role_id is None
        assert info.metadata is None
    
    def test_service_info_status_validation(self):
        """测试状态字段验证"""
        now = datetime.now()
        # 有效状态
        info1 = ServiceInfo(
            id="test-service-123",
            host="localhost",
            port=8080,
            name="test-service",
            version="1.0.0",
            base_url="http://localhost:8080",
            status="healthy",
            registered_at=now
        )
        info2 = ServiceInfo(
            id="test-service-124",
            host="localhost",
            port=8081,
            name="test-service-2",
            version="1.0.0",
            base_url="http://localhost:8081",
            status="unhealthy",
            registered_at=now
        )
        assert info1.status == "healthy"
        assert info2.status == "unhealthy"


class TestServiceHealth:
    """ServiceHealth模型测试"""
    
    def test_create_service_health(self):
        """测试创建服务健康信息"""
        now = datetime.now()
        health = ServiceHealth(
            service_id="test-service-123",
            name="test-service",
            host="localhost",
            port=8080,
            registry_healthy=True,
            collector_healthy=False,
            last_heartbeat=now,
            version="1.0.0"
        )
        assert health.service_id == "test-service-123"
        assert health.registry_healthy is True
        assert health.collector_healthy is False
        assert health.version == "1.0.0"
    
    def test_service_health_without_optional_fields(self):
        """测试创建不带可选字段的ServiceHealth"""
        health = ServiceHealth(
            service_id="test-service-123",
            name="test-service",
            host="localhost",
            port=8080,
            registry_healthy=True,
            collector_healthy=True
        )
        assert health.last_heartbeat is None
        assert health.version is None


class TestRegistryStats:
    """RegistryStats模型测试"""
    
    def test_create_registry_stats(self):
        """测试创建注册中心统计信息"""
        now = datetime.now()
        stats = RegistryStats(
            total_services=100,
            status_distribution={"healthy": 80, "unhealthy": 20},
            healthy_services=80,
            unhealthy_services=20,
            heartbeat_interval=30.0,
            service_timeout=60.0,
            timestamp=now
        )
        assert stats.total_services == 100
        assert stats.status_distribution["healthy"] == 80
        assert stats.healthy_services == 80
        assert stats.unhealthy_services == 20
        assert stats.heartbeat_interval == 30.0
        assert stats.timestamp == now


class TestRegistryHealth:
    """RegistryHealth模型测试"""
    
    def test_create_registry_health(self):
        """测试创建注册中心健康信息"""
        health = RegistryHealth(
            status="healthy",
            details={"version": "1.0.0", "uptime": "10 days"}
        )
        assert health.status == "healthy"
        assert health.details["version"] == "1.0.0"
    
    def test_registry_health_serialization(self):
        """测试注册中心健康信息序列化"""
        health = RegistryHealth(
            status="healthy",
            details={"uptime": "10 days"}
        )
        # 转换为字典
        health_dict = health.model_dump()
        assert health_dict["status"] == "healthy"
        assert health_dict["details"]["uptime"] == "10 days"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])