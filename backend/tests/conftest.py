import sys
import os
import logging
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.common.auth import verify_token


@pytest.fixture(autouse=True)
def override_auth():
    """自动跳过认证验证，使现有测试能正常运行"""
    async def _bypass_auth():
        return None
    app.dependency_overrides[verify_token] = _bypass_auth
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_client():
    """FastAPI TestClient fixture"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_httpx_client():
    """Mock的httpx异步客户端"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def mock_registry_service(mock_httpx_client):
    """Mock的RegistryService"""
    from backend.services.registry_service import RegistryService
    service = RegistryService()
    service.client = mock_httpx_client
    service.base_url = "http://mock-registry:8080"
    return service


@pytest.fixture
def mock_collector_service(mock_httpx_client):
    """Mock的CollectorService"""
    from backend.services.collector_service import CollectorService
    service = CollectorService()
    service.client = mock_httpx_client
    return service


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """覆盖配置中的环境变量，用于测试"""
    monkeypatch.setenv("ETCD_HOST", "localhost")
    monkeypatch.setenv("ETCD_PORT", "12379")
    monkeypatch.setenv("REGISTRY_URL", "http://mock-registry:8080")
    monkeypatch.setenv("COLLECTOR_TIMEOUT", "1.0")
    monkeypatch.setenv("CACHE_TTL", "5")
    monkeypatch.setenv("ADMIN_PASSWORD", "test123")


@pytest.fixture
def etcd_client(monkeypatch):
    """Mock的ETCD客户端，用于测试"""
    # 这里返回一个mock对象，实际ETCD集成测试会有专门的fixture
    mock_client = Mock()
    mock_client.get = Mock()
    mock_client.put = Mock()
    mock_client.delete = Mock()
    mock_client.delete_prefix = Mock()
    return mock_client


@pytest.fixture
def sample_service_info():
    """示例服务信息"""
    from backend.models.service import ServiceInfo
    return ServiceInfo(
        service_id="test-service-123",
        name="test-service",
        host="localhost",
        port=8080,
        version="1.0.0",
        status="healthy",
        last_heartbeat="2024-01-01T00:00:00Z"
    )


@pytest.fixture
def sample_role_info():
    """示例角色信息"""
    from backend.models.role import RoleInfo
    return RoleInfo(
        name="test-role",
        description="测试角色",
        parent_role_id=None,
        rule_ids=[]
    )


@pytest.fixture
def sample_rule_info():
    """示例规则信息"""
    from backend.models.role import RuleInfo
    return RuleInfo(
        name="test-rule",
        lua_content="function test() return true end",
        parent_rule_id=None,
        is_override=False,
        metadata={"type": "test"}
    )


# ETCD Docker容器fixture（可选，需要docker-py和Docker环境）
try:
    from fixtures.etcd_docker import EtcdDockerManager
    
    @pytest.fixture(scope="session")
    def etcd_docker():
        """会话级别的ETCD Docker容器fixture"""
        manager = EtcdDockerManager()
        manager.start()
        yield manager
        manager.cleanup_data()
        manager.stop()
    
    @pytest.fixture
    def etcd_docker_client(etcd_docker):
        """提供连接到ETCD Docker容器的客户端"""
        client = etcd_docker.get_client()
        # 清理可能存在的测试数据
        client.delete_prefix("/test/")
        client.delete_prefix("/software/config/")
        yield client
        # 测试后清理
        client.delete_prefix("/test/")
        client.delete_prefix("/software/config/")
    
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("docker-py未安装，ETCD Docker fixture不可用")
    
    @pytest.fixture(scope="session")
    def etcd_docker():
        """跳过ETCD Docker容器fixture"""
        pytest.skip("docker-py未安装，跳过ETCD Docker测试")
    
    @pytest.fixture
    def etcd_docker_client(etcd_docker):
        """跳过ETCD客户端fixture"""
        pytest.skip("docker-py未安装，跳过ETCD Docker测试")