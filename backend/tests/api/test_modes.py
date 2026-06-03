"""modes路由的API端点测试"""
import pytest
pytestmark = pytest.mark.docker
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from backend.main import app


class TestModesAPI:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_metadata(self):
        metadata = Mock()
        metadata.key = b"/joblens/config/modes/test-mode/info"
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
        with patch('backend.routers.modes.get_etcd_client', return_value=mock_etcd_client) as mock_get:
            yield mock_get

    # ─── 辅助函数测试 ───

    def test_validate_mode_name_valid(self):
        from backend.routers.modes import validate_mode_name
        assert validate_mode_name("test-mode") is True
        assert validate_mode_name("mode123") is True
        assert validate_mode_name("a") is True

    def test_validate_mode_name_invalid(self):
        from backend.routers.modes import validate_mode_name
        assert validate_mode_name("") is False
        assert validate_mode_name("a" * 51) is False
        assert validate_mode_name("test mode") is False
        assert validate_mode_name("test_mode") is False
        assert validate_mode_name("test.mode") is False

    def test_validate_yaml_valid(self):
        from backend.routers.modes import validate_yaml
        assert validate_yaml("key: value") is True
        assert validate_yaml("") is True
        assert validate_yaml("list:\n  - item1\n  - item2") is True

    def test_validate_yaml_invalid(self):
        from backend.routers.modes import validate_yaml
        with pytest.raises(ValueError, match="YAML"):
            validate_yaml("key: value: broken")

    def test_is_mode_exist_exists(self, mock_etcd_client):
        from backend.routers.modes import is_mode_exist
        mock_etcd_client.get.return_value = (b'{"name":"test"}', Mock())
        assert is_mode_exist(mock_etcd_client, "test-mode") is True

    def test_is_mode_exist_not_found(self, mock_etcd_client):
        from backend.routers.modes import is_mode_exist
        mock_etcd_client.get.return_value = (None, None)
        assert is_mode_exist(mock_etcd_client, "ghost-mode") is False

    def test_get_mode_config_path(self):
        from backend.routers.modes import get_mode_config_path
        path = get_mode_config_path("test-mode")
        assert "test-mode" in path
        assert path.endswith("config.yaml")

    def test_get_mode_info_path(self):
        from backend.routers.modes import get_mode_info_path
        path = get_mode_info_path("test-mode")
        assert "test-mode" in path
        assert path.endswith("/info")

    # ─── GET / - 获取模式列表 ───

    def test_get_modes_success(self, client, mock_etcd_client, patch_etcd):
        from backend.models.mode import ModeInfo
        mode = ModeInfo(name="test-mode", description="测试模式")
        mock_metadata = Mock()
        mock_metadata.key = b"/joblens/config/modes/test-mode/info"
        mock_etcd_client.get_prefix.return_value = [
            (mode.model_dump_json().encode(), mock_metadata)
        ]
        response = client.get("/api/modes/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["modes"][0]["name"] == "test-mode"

    def test_get_modes_empty(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/modes/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["modes"] == []

    def test_get_modes_error(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get_prefix.side_effect = Exception("ETCD不可达")
        response = client.get("/api/modes/")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    # ─── POST / - 创建模式 ───

    def test_create_mode_success(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.post("/api/modes/", json={
            "name": "new-mode",
            "description": "新模式"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-mode"
        assert data["description"] == "新模式"
        assert mock_etcd_client.put.call_count >= 2

    def test_create_mode_invalid_name(self, client, mock_etcd_client, patch_etcd):
        response = client.post("/api/modes/", json={
            "name": "invalid mode!",
            "description": "bad"
        })
        assert response.status_code == 400

    def test_create_mode_duplicate(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (b'{"name":"existing"}', Mock())
        response = client.post("/api/modes/", json={
            "name": "existing",
            "description": "已存在"
        })
        assert response.status_code == 409

    def test_create_mode_default(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.post("/api/modes/", json={
            "name": "default-mode",
            "default": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["default"] is True

    # ─── GET /{mode_name} - 获取模式详情 ───

    def test_get_mode_success(self, client, mock_etcd_client, patch_etcd):
        from datetime import datetime
        mode_dict = {
            "name": "test-mode",
            "description": "测试",
            "default": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (json.dumps(mode_dict).encode(), Mock()),
            (b"config content", Mock())
        ]
        response = client.get("/api/modes/test-mode")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-mode"
        assert data["config_count"] == 1

    def test_get_mode_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.get("/api/modes/ghost")
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]

    # ─── PUT /{mode_name} - 更新模式 ───

    def test_update_mode_success(self, client, mock_etcd_client, patch_etcd):
        mode_dict = {
            "name": "test-mode",
            "description": "旧描述",
            "default": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_etcd_client.get.return_value = (json.dumps(mode_dict).encode(), Mock())
        response = client.put("/api/modes/test-mode", json={
            "description": "新描述"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "新描述"

    def test_update_mode_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.put("/api/modes/ghost", json={"description": "x"})
        assert response.status_code == 404

    # ─── DELETE /{mode_name} - 删除模式 ───

    def test_delete_mode_success(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-mode"}', Mock()),
            None
        ]
        mock_etcd_client.get_prefix.return_value = []
        response = client.delete("/api/modes/test-mode")
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]

    def test_delete_mode_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.delete("/api/modes/ghost")
        assert response.status_code == 404

    def test_delete_mode_in_use(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-mode"}', Mock()),
            None
        ]
        svc_metadata = Mock()
        svc_metadata.key = b"/joblens/services/svc-1/mode"
        mock_etcd_client.get_prefix.return_value = [
            (b"test-mode", svc_metadata)
        ]
        response = client.delete("/api/modes/test-mode")
        assert response.status_code == 400
        assert "正在被" in response.json()["detail"]

    # ─── GET /{mode_name}/config - 获取配置 ───

    def test_get_mode_config_success(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (b"key: value\n", Mock())
        response = client.get("/api/modes/test-mode/config")
        assert response.status_code == 200
        assert response.json()["config"] == "key: value\n"

    def test_get_mode_config_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.get("/api/modes/ghost/config")
        assert response.status_code == 404

    def test_get_mode_config_with_metadata(self, client, mock_etcd_client, mock_metadata):
        mock_etcd_client.get.return_value = (b"key: value", mock_metadata)
        with patch('backend.routers.modes.get_etcd_client', return_value=mock_etcd_client):
            response = client.get("/api/modes/test-mode/config?include_metadata=true")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert data["metadata"]["version"] == 1

    # ─── PUT /{mode_name}/config - 更新配置 ───

    def test_update_mode_config_success(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-mode"}', Mock()),
            (b"old config", Mock()),
        ]
        response = client.put("/api/modes/test-mode/config", json={
            "raw_config": "new: config\n"
        })
        assert response.status_code == 200
        assert "已更新" in response.json()["message"]

    def test_update_mode_config_invalid_yaml(self, client, mock_etcd_client, patch_etcd):
        response = client.put("/api/modes/test-mode/config", json={
            "raw_config": "invalid: yaml: broken"
        })
        assert response.status_code == 400

    def test_update_mode_config_mode_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock(return_value=(None, None))
        response = client.put("/api/modes/ghost/config", json={
            "raw_config": "key: value\n"
        })
        assert response.status_code == 404

    # ─── GET /default - 获取默认模式 ───
    # 注意: /default 路由定义在 /{mode_name} 之后，所以会先匹配 /{mode_name}
    # 以下是直接测试 get_default_mode 函数的单元测试

    def test_get_default_mode_function(self, mock_etcd_client):
        from backend.routers.modes import get_default_mode
        mock_etcd_client.get.return_value = (b"default-mode", Mock())
        result = get_default_mode(mock_etcd_client)
        assert result == "default-mode"

    def test_get_default_mode_function_not_found(self, mock_etcd_client):
        from backend.routers.modes import get_default_mode
        mock_etcd_client.get.return_value = (None, None)
        result = get_default_mode(mock_etcd_client)
        assert result is None

    # ─── GET /{mode_name}/versions - 版本历史 ───

    def test_get_versions_success(self, client, mock_etcd_client, patch_etcd):
        mock_metadata = Mock()
        mock_metadata.mod_revision = 5
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-mode"}', Mock()),
            (b"current config", mock_metadata),
        ]
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/modes/test-mode/versions")
        assert response.status_code == 200
        data = response.json()
        assert data["current_version"] == "v5"

    def test_get_versions_mode_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.get("/api/modes/ghost/versions")
        assert response.status_code == 404

    # ─── POST /{mode_name}/rollback/{version} - 回滚 ───

    def test_rollback_success(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-mode"}', Mock()),
            (b'{"config":"old config"}', Mock()),
            (b"current config", Mock()),
        ]
        response = client.post("/api/modes/test-mode/rollback/v1")
        assert response.status_code == 200
        assert "已回滚" in response.json()["message"]

    def test_rollback_version_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-mode"}', Mock()),
            (None, None),
        ]
        response = client.post("/api/modes/test-mode/rollback/v999")
        assert response.status_code == 404

    # ─── GET /{mode_name}/version/{version} - 特定版本 ───

    def test_get_specific_version_current(self, client, mock_etcd_client, patch_etcd):
        mock_metadata = Mock()
        mock_metadata.mod_revision = 3
        mock_metadata.create_revision = 1
        mock_metadata.lease_id = 0
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-mode"}', Mock()),
            (b"current config", mock_metadata),
        ]
        response = client.get("/api/modes/test-mode/version/current")
        assert response.status_code == 200
        assert response.json()["config"] == "current config"

    def test_get_specific_version_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get = Mock(return_value=(None, None))
        response = client.get("/api/modes/ghost/version/current")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
