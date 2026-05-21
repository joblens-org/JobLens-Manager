"""configs路由的API端点测试"""
import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from backend.main import app


class TestConfigsAPI:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_etcd_client(self):
        client = Mock()
        client.get.return_value = (b'{"name":"test-mode"}', Mock())
        client.put = Mock()
        client.get_prefix = Mock(return_value=[])
        return client

    @pytest.fixture
    def patch_all(self, mock_etcd_client):
        """同时patch get_etcd_client + get_mode_path + get_mode_dirpath，消除额外的get调用"""
        with patch('backend.routers.configs.get_etcd_client', return_value=mock_etcd_client):
            with patch('backend.routers.configs.get_mode_path', return_value="/modes/test-mode/config.yaml"):
                with patch('backend.routers.configs.get_mode_dirpath', return_value="/modes/test-mode/config"):
                    yield

    # ─── 辅助函数测试 ───

    def test_validate_yaml_valid(self):
        from backend.routers.configs import validate_yaml
        assert validate_yaml("key: value") is True
        assert validate_yaml("") is True

    def test_validate_yaml_invalid(self):
        from backend.routers.configs import validate_yaml
        with pytest.raises(ValueError, match="YAML"):
            validate_yaml("[invalid")

    def test_ensure_mode_exists_success(self, mock_etcd_client):
        from backend.routers.configs import ensure_mode_exists
        with patch('backend.routers.configs.get_etcd_client', return_value=mock_etcd_client):
            ensure_mode_exists("test-mode")

    def test_ensure_mode_exists_not_found(self, mock_etcd_client):
        from backend.routers.configs import ensure_mode_exists
        from fastapi import HTTPException
        mock_etcd_client.get.return_value = (None, None)
        with pytest.raises(HTTPException) as exc:
            ensure_mode_exists("ghost")
        assert exc.value.status_code == 404

    # ─── GET /{mode} - 获取配置 ───

    def test_get_config_success(self, client, mock_etcd_client, patch_all):
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (b"key: value\n", Mock()),
        ])
        response = client.get("/api/configs/test-mode")
        assert response.status_code == 200
        assert response.json()["config"] == "key: value\n"

    def test_get_config_not_found_mode(self, client, mock_etcd_client, patch_all):
        mock_etcd_client.get.return_value = (None, None)
        response = client.get("/api/configs/ghost-mode")
        assert response.status_code == 404

    def test_get_config_not_found_config(self, client, mock_etcd_client, patch_all):
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (None, None),
        ])
        response = client.get("/api/configs/test-mode")
        assert response.status_code == 404
        assert "配置不存在" in response.json()["detail"]

    def test_get_config_with_metadata(self, client, mock_etcd_client, patch_all):
        mock_metadata = Mock()
        mock_metadata.version = 3
        mock_metadata.create_revision = 1
        mock_metadata.mod_revision = 3
        mock_metadata.lease_id = 0
        mock_metadata.key = b"/modes/test-mode/config/config.yaml"
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (b"key: value", mock_metadata),
        ])
        response = client.get("/api/configs/test-mode?include_metadata=true")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert data["metadata"]["version"] == 3

    # ─── PUT /{mode} - 更新配置 ───

    def _make_metadata(self, version=1):
        m = Mock()
        m.version = version
        m.mod_revision = version
        m.create_revision = 1
        m.lease_id = 0
        return m

    def test_update_config_success(self, client, mock_etcd_client, patch_all):
        old_meta = self._make_metadata(2)
        new_meta = self._make_metadata(3)
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', old_meta),
            (b"old config", old_meta),
            (None, None),
            (b"new config", new_meta),
        ])
        response = client.put("/api/configs/test-mode", json={"raw_config": "new: config\n"})
        assert response.status_code == 200
        assert "更新成功" in response.json()["message"]

    def test_update_config_invalid_yaml(self, client, mock_etcd_client, patch_all):
        mock_etcd_client.get = Mock(return_value=(b'{"name":"test-mode"}', Mock()))
        response = client.put("/api/configs/test-mode", json={"raw_config": "invalid: yaml: broken"})
        assert response.status_code == 400

    def test_update_config_mode_not_found(self, client, mock_etcd_client, patch_all):
        mock_etcd_client.get = Mock(return_value=(None, None))
        response = client.put("/api/configs/ghost", json={"raw_config": "key: value\n"})
        assert response.status_code == 404

    def test_update_config_with_description(self, client, mock_etcd_client, patch_all):
        old_meta = self._make_metadata(2)
        new_meta = self._make_metadata(3)
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', old_meta),
            (b"old config", old_meta),
            (None, None),
            (b"new config", new_meta),
        ])
        response = client.put("/api/configs/test-mode", json={
            "raw_config": "key: value\n", "description": "更新说明"
        })
        assert response.status_code == 200

    # ─── GET /{mode}/versions - 版本历史 ───

    def test_get_versions_success(self, client, mock_etcd_client, patch_all):
        current_metadata = Mock()
        current_metadata.version = 5
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (b"current config", current_metadata),
        ])
        response = client.get("/api/configs/test-mode/versions")
        assert response.status_code == 200
        assert response.json()["current_version"] == 5

    def test_get_versions_config_not_found(self, client, mock_etcd_client, patch_all):
        mock_metadata = self._make_metadata(5)
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (None, mock_metadata),
        ])
        response = client.get("/api/configs/test-mode/versions")
        assert response.status_code == 404

    # ─── GET /{mode}/version/{version} - 特定版本 ───

    def test_get_specific_version_current(self, client, mock_etcd_client, patch_all):
        mock_metadata = Mock()
        mock_metadata.mod_revision = 3
        mock_metadata.create_revision = 1
        mock_metadata.lease_id = 0
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (b"current config", mock_metadata),
        ])
        response = client.get("/api/configs/test-mode/version/current")
        assert response.status_code == 200
        assert response.json()["config"] == "current config"

    def test_get_specific_version_history(self, client, mock_etcd_client, patch_all):
        mock_metadata = Mock()
        mock_metadata.mod_revision = 1
        mock_metadata.create_revision = 1
        mock_metadata.lease_id = 0
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (b"old config", mock_metadata),
        ])
        response = client.get("/api/configs/test-mode/version/v1")
        assert response.status_code == 200

    def test_get_specific_version_not_found(self, client, mock_etcd_client, patch_all):
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (None, None),
        ])
        response = client.get("/api/configs/test-mode/version/v999")
        assert response.status_code == 404

    # ─── POST /{mode}/rollback/{version} - 回滚 ───

    def test_rollback_success(self, client, mock_etcd_client, patch_all):
        meta = self._make_metadata(3)
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (b"target config", meta),
            (b"current config", meta),
        ])
        response = client.post("/api/configs/test-mode/rollback/v1")
        assert response.status_code == 200
        assert "回滚成功" in response.json()["message"]

    def test_rollback_version_not_found(self, client, mock_etcd_client, patch_all):
        mock_etcd_client.get = Mock(side_effect=[
            (b'{"name":"test-mode"}', Mock()),
            (None, None),
        ])
        response = client.post("/api/configs/test-mode/rollback/v999")
        assert response.status_code == 404

    # ─── GET /modes - 所有模式信息 ───
    # 注意: /modes 路由定义在 /{mode} 之后，因此 GET /api/configs/modes 会匹配 /{mode}
    # 这里直接测试 get_all_modes 函数的辅助逻辑


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
