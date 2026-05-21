"""rules路由的API端点测试"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from datetime import datetime
from backend.main import app


class TestRulesAPI:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_metadata(self):
        metadata = Mock()
        metadata.key = b"/joblens/config/rules/rule-123"
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
        client.delete = Mock()
        client.get_prefix = Mock(return_value=[])
        return client

    @pytest.fixture
    def patch_etcd(self, mock_etcd_client):
        with patch('backend.routers.rules.get_etcd_client', return_value=mock_etcd_client) as mock_get:
            yield mock_get

    @pytest.fixture
    def patch_rule_path(self):
        with patch('backend.routers.rules.get_rule_path') as mock_path:
            mock_path.return_value = "/joblens/config/rules/rule-123"
            yield mock_path

    @pytest.fixture
    def patch_lua_validator(self):
        mock_validator = Mock()
        mock_validator.validate_rule.return_value = {"name": "test_rule", "description": "test", "priority": 1, "condition": "function() end"}
        with patch('backend.routers.rules.get_lua_validator', return_value=mock_validator):
            yield mock_validator

    @pytest.fixture
    def sample_rule_dict(self):
        return {
            "rule_id": "rule-123",
            "role_id": "role-123",
            "name": "test-rule",
            "lua_content": "rule = {name='test', description='desc', priority=1, condition=function() end}",
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    # ─── GET / - 获取规则列表 ───

    def test_get_rules_success(self, client, mock_etcd_client, patch_etcd, sample_rule_dict):
        mock_metadata = Mock()
        mock_metadata.key = b"/joblens/config/rules/rule-123"
        mock_etcd_client.get_prefix.return_value = [
            (json.dumps(sample_rule_dict).encode(), mock_metadata)
        ]
        response = client.get("/api/rules/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["rules"][0]["name"] == "test-rule"

    def test_get_rules_empty(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/rules/")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_get_rules_pagination(self, client, mock_etcd_client, patch_etcd, sample_rule_dict):
        mock_metadata = Mock()
        mock_metadata.key = b"/joblens/config/rules/rule-1"
        all_rules = []
        for i in range(5):
            d = dict(sample_rule_dict)
            d["rule_id"] = f"rule-{i}"
            d["name"] = f"rule-{i}"
            all_rules.append((json.dumps(d).encode(), mock_metadata))
        mock_etcd_client.get_prefix.return_value = all_rules
        response = client.get("/api/rules/?page=1&page_size=2")
        assert response.status_code == 200
        assert len(response.json()["rules"]) == 2
        assert response.json()["total"] == 5

    def test_get_rules_skip_history(self, client, mock_etcd_client, patch_etcd, sample_rule_dict):
        mock_rule_meta = Mock()
        mock_rule_meta.key = b"/joblens/config/rules/rule-123"
        mock_history_meta = Mock()
        mock_history_meta.key = b"/joblens/config/rules/rule-123/history/v1"
        mock_etcd_client.get_prefix.return_value = [
            (json.dumps(sample_rule_dict).encode(), mock_rule_meta),
            (b"old data", mock_history_meta),
        ]
        response = client.get("/api/rules/")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    # ─── POST / - 创建规则 ───

    def test_create_rule_success(self, client, mock_etcd_client, patch_etcd, patch_lua_validator):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (b'{"name":"test-role","role_id":"role-123"}', Mock()),
            (b'{"name":"test-role","role_id":"role-123","rule_ids":[]}', Mock()),
        ]
        response = client.post("/api/rules/", json={
            "role_id": "role-123",
            "name": "new-rule",
            "lua_content": "rule = {name='test', description='desc', priority=1, condition=function() end}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-rule"

    def test_create_rule_role_not_found(self, client, mock_etcd_client, patch_etcd, patch_lua_validator):
        mock_etcd_client.get.return_value = (None, None)
        response = client.post("/api/rules/", json={
            "role_id": "ghost-role",
            "name": "new-rule",
            "lua_content": "rule = {name='test', description='desc', priority=1, condition=function() end}"
        })
        assert response.status_code == 404

    def test_create_rule_lua_validation_fails(self, client, mock_etcd_client, patch_etcd):
        mock_validator = Mock()
        mock_validator.validate_rule.side_effect = HTTPException(status_code=400, detail="Lua语法错误")
        with patch('backend.routers.rules.get_lua_validator', return_value=mock_validator):
            mock_etcd_client.get.return_value = (b'{"name":"test-role","role_id":"role-123"}', Mock())
            response = client.post("/api/rules/", json={
                "role_id": "role-123",
                "name": "bad-rule",
                "lua_content": "invalid lua code"
            })
            assert response.status_code == 400

    # ─── GET /{rule_id} - 获取规则详情 ───

    def test_get_rule_success(self, client, mock_etcd_client, patch_etcd, sample_rule_dict):
        mock_etcd_client.get.return_value = (json.dumps(sample_rule_dict).encode(), Mock())
        response = client.get("/api/rules/rule-123")
        assert response.status_code == 200
        assert response.json()["name"] == "test-rule"

    def test_get_rule_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.get("/api/rules/ghost")
        assert response.status_code == 404

    # ─── PUT /{rule_id} - 更新规则 ───

    def test_update_rule_success(self, client, mock_etcd_client, patch_etcd, sample_rule_dict, patch_lua_validator):
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (json.dumps(sample_rule_dict).encode(), Mock()),
            (b'{"name":"test-role","role_id":"role-123","rule_ids":["rule-123"]}', Mock()),
        ]
        response = client.put("/api/rules/rule-123", json={
            "name": "updated-rule",
            "lua_content": "rule = {name='updated', description='desc', priority=1, condition=function() end}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-rule"
        assert data["rule_id"] != "rule-123"

    def test_update_rule_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.put("/api/rules/ghost", json={"name": "new-name"})
        assert response.status_code == 404

    # ─── DELETE /{rule_id} - 删除规则 ───

    def test_delete_rule_success(self, client, mock_etcd_client, patch_etcd):
        from datetime import datetime
        rule_data = json.dumps({
            "rule_id": "rule-123",
            "role_id": "role-123",
            "name": "test-rule",
            "lua_content": "rule = {name='test', description='desc', priority=1, condition=function() end}",
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        role_data = json.dumps({
            "role_id": "role-123",
            "name": "test-role",
            "description": "test",
            "parent_role_id": None,
            "rule_ids": ["rule-123"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "default": False
        })
        mock_etcd_client.get = Mock()
        mock_etcd_client.get.side_effect = [
            (rule_data.encode(), Mock()),
            (role_data.encode(), Mock()),
        ]
        response = client.delete("/api/rules/rule-123")
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]
        assert mock_etcd_client.delete.called

    def test_delete_rule_not_found(self, client, mock_etcd_client, patch_etcd):
        mock_etcd_client.get.return_value = (None, None)
        response = client.delete("/api/rules/ghost")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
