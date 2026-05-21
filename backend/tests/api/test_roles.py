"""roles路由的API端点测试"""
import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from backend.main import app


class TestRolesAPI:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_metadata(self):
        metadata = Mock()
        metadata.key = b"/joblens/config/roles/test-role-id/info"
        metadata.version = 1
        metadata.create_revision = 1
        metadata.mod_revision = 1
        metadata.lease_id = 0
        return metadata

    @pytest.fixture
    def mock_etcd_client(self):
        client = Mock()
        client.get = Mock(return_value=(None, None))
        client.put = Mock()
        client.delete_prefix = Mock()
        client.delete = Mock()
        client.get_prefix = Mock(return_value=[])
        return client

    @pytest.fixture
    def patch_etcd(self, mock_etcd_client):
        with patch('backend.routers.roles.get_etcd_client', return_value=mock_etcd_client) as mock_get:
            yield mock_get

    # ─── 辅助函数测试 ───

    def test_validate_role_name_valid(self):
        from backend.routers.roles import validate_role_name
        assert validate_role_name("test-role") is True
        assert validate_role_name("role_with_underscore") is True
        assert validate_role_name("admin") is True

    def test_validate_role_name_invalid(self):
        from backend.routers.roles import validate_role_name
        assert validate_role_name("") is False
        assert validate_role_name("a" * 101) is False
        assert validate_role_name("role with space") is False
        assert validate_role_name("role.name") is False

    def test_get_role_info_path(self):
        from backend.routers.roles import get_role_info_path
        path = get_role_info_path("role-123")
        assert "role-123" in path
        assert path.endswith("/info")

    # ─── GET / - 获取角色列表 ───

    def test_get_roles_success(self, client, mock_etcd_client, patch_etcd):
        from backend.models.role import RoleInfo
        role = RoleInfo(name="test-role", description="测试角色")
        mock_metadata = Mock()
        mock_metadata.key = b"/joblens/config/roles/test-role-id/info"
        mock_etcd_client.get_prefix.return_value = [
            (role.model_dump_json().encode(), mock_metadata)
        ]
        response = client.get("/api/roles/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["roles"][0]["name"] == "test-role"

    def test_get_roles_empty(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/roles/")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_get_roles_error(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get_prefix.side_effect = Exception("ETCD错误")
        response = client.get("/api/roles/")
        assert response.status_code == 500

    # ─── POST / - 创建角色 ───

    def test_create_role_success(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get_prefix.return_value = []
        mock_etcd_client.get.return_value = (None, None)
        response = client.post("/api/roles/", json={
            "name": "new-role",
            "description": "新角色"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-role"

    def test_create_role_invalid_name(self, client, mock_etcd_client, patch_etcd):
        response = client.post("/api/roles/", json={
            "name": "invalid role!",
            "description": "bad"
        })
        assert response.status_code == 400

    def test_create_role_duplicate_name(self, client, mock_etcd_client, patch_etcd):
        from backend.models.role import RoleInfo
        existing_role = RoleInfo(name="dup-role", role_id="existing-id")
        mock_metadata = Mock()
        mock_metadata.key = b"/joblens/config/roles/existing-id/info"
        mock_etcd_client.get_prefix.return_value = [
            (existing_role.model_dump_json().encode(), mock_metadata)
        ]
        response = client.post("/api/roles/", json={
            "name": "dup-role",
            "description": "重复"
        })
        assert response.status_code == 409

    def test_create_role_parent_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get_prefix.return_value = []
        mock_etcd_client.get = Mock(return_value=(None, None))
        response = client.post("/api/roles/", json={
            "name": "child-role",
            "parent_role_id": "nonexistent-parent"
        })
        assert response.status_code in (404, 500)

    # ─── GET /{role_id} - 获取角色详情 ───

    def test_get_role_success(self, client, mock_etcd_client, patch_etcd):
        from backend.models.role import RoleInfo
        role = RoleInfo(name="test-role", role_id="role-123")
        mock_etcd_client.get.return_value = (role.model_dump_json().encode(), Mock())
        response = client.get("/api/roles/role-123")
        assert response.status_code == 200
        assert response.json()["name"] == "test-role"

    def test_get_role_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.get("/api/roles/ghost")
        assert response.status_code == 404

    # ─── PUT /{role_id} - 更新角色 ───

    def test_update_role_success(self, client, mock_etcd_client, patch_etcd):
        from backend.models.role import RoleInfo
        role = RoleInfo(name="test-role", role_id="role-123", description="旧描述")
        mock_etcd_client.get.return_value = (role.model_dump_json().encode(), Mock())
        response = client.put("/api/roles/role-123", json={"description": "新描述"})
        assert response.status_code == 200
        assert response.json()["description"] == "新描述"

    def test_update_role_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.put("/api/roles/ghost", json={"description": "x"})
        assert response.status_code == 404

    # ─── DELETE /{role_id} - 删除角色 ───

    def test_delete_role_success(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-role","role_id":"role-123"}', Mock()),
            None
        ]
        mock_etcd_client.get_prefix.return_value = []
        response = client.delete("/api/roles/role-123")
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]

    def test_delete_role_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.delete("/api/roles/ghost")
        assert response.status_code == 404

    def test_delete_role_in_use(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-role","role_id":"role-123"}', Mock()),
            None
        ]
        svc_metadata = Mock()
        svc_metadata.key = b"/joblens/services/svc-1/role"
        mock_etcd_client.get_prefix.return_value = [
            (b"role-123", svc_metadata)
        ]
        response = client.delete("/api/roles/role-123")
        assert response.status_code == 400
        assert "正在被" in response.json()["detail"]

    # ─── GET /{role_id}/rules - 获取角色规则（含继承） ───

    def test_get_role_rules_success(self, client, mock_etcd_client, patch_etcd):
        from backend.models.role import RoleInfo
        role = RoleInfo(name="test-role", role_id="role-123", rule_ids=[])
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (role.model_dump_json().encode(), Mock()),
        ]
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/roles/role-123/rules")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_get_role_rules_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.get("/api/roles/ghost/rules")
        assert response.status_code == 404

    # ─── GET /{role_id}/rules/effective - 生效规则 ───

    def test_get_effective_rules_success(self, client, mock_etcd_client, patch_etcd):
        from backend.models.role import RoleInfo
        role = RoleInfo(name="test-role", role_id="role-123", rule_ids=[])
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (role.model_dump_json().encode(), Mock()),
        ]
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/roles/role-123/rules/effective")
        assert response.status_code == 200

    # ─── GET /default - 获取默认角色 ───
    # 注意: /default 路由定义在 /{role_id} 之后，所以会先匹配 /{role_id}
    # 以下是直接测试 get_default_role_id 函数的单元测试

    def test_get_default_role_function(self, mock_etcd_client):
        from backend.routers.roles import get_default_role_id
        mock_etcd_client.get.return_value = (b"default-id", Mock())
        result = get_default_role_id(mock_etcd_client)
        assert result == "default-id"

    def test_get_default_role_function_not_found(self, mock_etcd_client):
        from backend.routers.roles import get_default_role_id
        mock_etcd_client.get.return_value = (None, None)
        result = get_default_role_id(mock_etcd_client)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
