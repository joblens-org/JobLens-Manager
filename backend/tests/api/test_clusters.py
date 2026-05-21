"""clusters路由的API端点测试"""
import json
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from backend.main import app


class TestClustersAPI:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_etcd_client(self):
        client = Mock()
        client.get = Mock(return_value=(None, None))
        client.put = Mock()
        client.get_prefix = Mock(return_value=[])
        return client

    @pytest.fixture
    def patch_etcd(self, mock_etcd_client):
        with patch(
            "backend.routers.clusters.get_etcd_client",
            return_value=mock_etcd_client,
        ) as mock_get:
            yield mock_get

    @pytest.fixture
    def sample_instances(self):
        """模拟注册中心自动发现的集群数据"""
        return [
            {
                "cluster_name": "condor-prod-1",
                "cluster_type": "condor",
                "tags": ["tag-schedd-1", "tag-schedd-2"],
            },
            {
                "cluster_name": "slurm-prod-1",
                "cluster_type": "slurm",
                "tags": ["tag-slurm-1"],
            },
        ]

    @pytest.fixture
    def sample_config(self):
        """模拟已保存的集群配置"""
        return {
            "alias": "生产集群",
            "description": "北京机房",
            "enabled": True,
            "extra": {"location": "北京", "es_url": "http://es:9200"},
            "updated_at": "2024-01-01T00:00:00",
        }

    def _mock_instance_prefix(self, mock_etcd_client, instances):
        """模拟 etcd get_prefix 返回集群实例数据"""
        results = []
        for instance in instances:
            mock_metadata = Mock()
            mock_metadata.key = f"/joblens_registry/clusters/instance/{instance['cluster_name']}".encode()
            results.append((json.dumps(instance).encode(), mock_metadata))
        mock_etcd_client.get_prefix.return_value = results

    # ─── GET /api/clusters ───

    def test_get_clusters_empty(self, client, patch_etcd, mock_etcd_client):
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/clusters")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["clusters"] == []

    def test_get_clusters_with_data(self, client, patch_etcd, mock_etcd_client, sample_instances, sample_config):
        self._mock_instance_prefix(mock_etcd_client, sample_instances)
        # 为第一个集群模拟已保存的配置
        mock_etcd_client.get.side_effect = lambda key: (
            (json.dumps(sample_config).encode(), Mock()) if "condor-prod-1" in key else (None, None)
        ) if isinstance(key, str) else (None, None)

        response = client.get("/api/clusters")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["clusters"]) == 2

        # 验证集群数据
        c1 = data["clusters"][0]
        assert c1["cluster_name"] == "condor-prod-1"
        assert c1["cluster_type"] == "condor"
        assert c1["tags"] == ["tag-schedd-1", "tag-schedd-2"]
        assert c1["alias"] == "生产集群"
        assert c1["description"] == "北京机房"
        # extra 中只有 es_url 被填了，其余 4 个必填字段应出现在 missing_fields
        assert "es_url" not in c1["missing_fields"]
        assert len(c1["missing_fields"]) == 4

        # 第二个集群无配置，应使用默认值
        c2 = data["clusters"][1]
        assert c2["cluster_name"] == "slurm-prod-1"
        assert c2["alias"] == ""
        assert c2["enabled"] is True
        assert c2["extra"] == {}
        assert len(c2["missing_fields"]) == 5

    def test_get_clusters_merge_default_config(self, client, patch_etcd, mock_etcd_client, sample_instances):
        """集群无已保存配置时，合并时应使用默认值"""
        self._mock_instance_prefix(mock_etcd_client, sample_instances)
        mock_etcd_client.get.return_value = (None, None)

        response = client.get("/api/clusters")
        assert response.status_code == 200
        data = response.json()
        assert len(data["clusters"]) == 2
        for c in data["clusters"]:
            assert c["alias"] == ""
            assert c["description"] == ""
            assert c["enabled"] is True
            assert c["extra"] == {}
            assert len(c["missing_fields"]) == 5

    # ─── GET /api/clusters/scheme ───

    def test_get_clusters_scheme(self, client, patch_etcd, mock_etcd_client, sample_instances, sample_config):
        self._mock_instance_prefix(mock_etcd_client, sample_instances)
        mock_etcd_client.get.side_effect = lambda key: (
            (json.dumps(sample_config).encode(), Mock()) if "condor-prod-1" in key else (None, None)
        ) if isinstance(key, str) else (None, None)

        response = client.get("/api/clusters/scheme")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        scheme = data["clusters"][0]
        # scheme 不应包含 description 字段
        assert "description" not in scheme
        assert scheme["cluster_name"] == "condor-prod-1"
        assert scheme["alias"] == "生产集群"
        assert scheme["enabled"] is True
        # scheme 应包含 missing_fields
        assert "missing_fields" in scheme
        assert "es_url" not in scheme["missing_fields"]

    def test_get_clusters_scheme_empty(self, client, patch_etcd, mock_etcd_client):
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/clusters/scheme")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    # ─── GET /api/clusters/{cluster_name} ───

    def test_get_cluster_success(self, client, patch_etcd, mock_etcd_client, sample_instances, sample_config):
        self._mock_instance_prefix(mock_etcd_client, sample_instances)
        mock_etcd_client.get.return_value = (json.dumps(sample_config).encode(), Mock())

        response = client.get("/api/clusters/condor-prod-1")
        assert response.status_code == 200
        data = response.json()
        assert data["cluster_name"] == "condor-prod-1"
        assert data["alias"] == "生产集群"
        assert data["tags"] == ["tag-schedd-1", "tag-schedd-2"]

    def test_get_cluster_not_found(self, client, patch_etcd, mock_etcd_client):
        mock_etcd_client.get_prefix.return_value = []
        response = client.get("/api/clusters/non-existent")
        assert response.status_code == 404

    # ─── PUT /api/clusters/{cluster_name}/config ───

    def test_update_cluster_config_success(self, client, patch_etcd, mock_etcd_client, sample_instances):
        self._mock_instance_prefix(mock_etcd_client, sample_instances)
        # 现有配置不存在
        mock_etcd_client.get.return_value = (None, None)

        update_data = {
            "alias": "新别名",
            "description": "新描述",
            "enabled": False,
            "extra": {"key": "value"},
        }
        response = client.put("/api/clusters/condor-prod-1/config", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] is not None
        assert data["cluster_name"] == "condor-prod-1"

        # 验证 put 被调用
        mock_etcd_client.put.assert_called_once()
        call_args = mock_etcd_client.put.call_args
        assert "condor-prod-1" in call_args[0][0]

        # 验证写入的 JSON 包含所有更新字段
        written_data = json.loads(call_args[0][1])
        assert written_data["alias"] == "新别名"
        assert written_data["description"] == "新描述"
        assert written_data["enabled"] is False
        assert written_data["extra"] == {"key": "value"}

    def test_update_cluster_config_partial(self, client, patch_etcd, mock_etcd_client, sample_instances):
        """部分更新：只改 alias，其他字段保持不变"""
        self._mock_instance_prefix(mock_etcd_client, sample_instances)

        existing_config = {
            "alias": "旧别名",
            "description": "旧描述",
            "enabled": True,
            "extra": {"old": "data"},
        }
        mock_etcd_client.get.return_value = (json.dumps(existing_config).encode(), Mock())

        response = client.put(
            "/api/clusters/condor-prod-1/config",
            json={"alias": "新别名"},
        )
        assert response.status_code == 200

        # 验证写入的数据：alias 更新了，其他保持不变
        call_args = mock_etcd_client.put.call_args
        written_data = json.loads(call_args[0][1])
        assert written_data["alias"] == "新别名"
        assert written_data["description"] == "旧描述"
        assert written_data["enabled"] is True
        assert written_data["extra"] == {"old": "data"}

    def test_update_cluster_config_cluster_not_found(self, client, patch_etcd, mock_etcd_client):
        mock_etcd_client.get_prefix.return_value = []

        response = client.put(
            "/api/clusters/non-existent/config",
            json={"alias": "test"},
        )
        assert response.status_code == 404

    # ─── 路径函数测试 ───

    def test_cluster_instance_prefix(self):
        from backend.routers.clusters import _get_cluster_instance_prefix
        prefix = _get_cluster_instance_prefix()
        assert "clusters/instance/" in prefix

    def test_cluster_config_key(self):
        from backend.routers.clusters import _get_cluster_config_key
        key = _get_cluster_config_key("my-cluster")
        assert "clusters/my-cluster" in key
        assert "//" not in key

    def test_read_cluster_config_default(self, mock_etcd_client):
        from backend.routers.clusters import _read_cluster_config
        mock_etcd_client.get.return_value = (None, None)
        config = _read_cluster_config(mock_etcd_client, "test")
        assert config.alias == ""
        assert config.enabled is True

    def test_merge_cluster_detail(self):
        from backend.routers.clusters import _merge_cluster_detail
        from backend.models.cluster import ClusterConfig

        instance = {
            "cluster_name": "test",
            "cluster_type": "condor",
            "tags": ["t1", "t2"],
        }
        config = ClusterConfig(alias="别名", enabled=True, extra={"k": "v"})
        detail = _merge_cluster_detail(instance, config)
        assert detail.cluster_name == "test"
        assert detail.cluster_type == "condor"
        assert detail.tags == ["t1", "t2"]
        assert detail.alias == "别名"
        assert detail.enabled is True
        assert detail.extra == {"k": "v"}

    def test_merge_cluster_scheme(self):
        from backend.routers.clusters import _merge_cluster_scheme
        from backend.models.cluster import ClusterConfig

        instance = {"cluster_name": "test", "cluster_type": "slurm", "tags": ["t1"]}
        config = ClusterConfig(alias="scheme-别名", enabled=False)
        scheme = _merge_cluster_scheme(instance, config)
        assert scheme.cluster_name == "test"
        assert scheme.alias == "scheme-别名"
        assert scheme.enabled is False
