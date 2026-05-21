"""Cluster模型的单元测试"""
import pytest
from datetime import datetime
from backend.models.cluster import (
    ClusterInfo,
    ClusterConfig,
    ClusterConfigUpdate,
    ClusterDetail,
    ClusterScheme,
    ClusterExtraSchema,
    ClusterListResponse,
    ClusterSchemeResponse,
)


class TestClusterInfo:
    """ClusterInfo 模型测试"""

    def test_create_cluster_info_basic(self):
        info = ClusterInfo(
            cluster_name="condor-prod",
            cluster_type="condor",
            tags=["tag-schedd-1", "tag-schedd-2"],
        )
        assert info.cluster_name == "condor-prod"
        assert info.cluster_type == "condor"
        assert info.tags == ["tag-schedd-1", "tag-schedd-2"]

    def test_create_cluster_info_single_tag(self):
        """单 tag 场景（如 slurm）"""
        info = ClusterInfo(
            cluster_name="slurm-cluster",
            cluster_type="slurm",
            tags=["tag-slurm-1"],
        )
        assert len(info.tags) == 1
        assert info.tags[0] == "tag-slurm-1"

    def test_create_cluster_info_empty_tags(self):
        info = ClusterInfo(cluster_name="empty-cluster", cluster_type="unknown")
        assert info.tags == []

    def test_cluster_info_serialization(self):
        info = ClusterInfo(
            cluster_name="test",
            cluster_type="condor",
            tags=["t1", "t2"],
        )
        data = info.model_dump()
        assert data["cluster_name"] == "test"
        assert data["cluster_type"] == "condor"
        assert data["tags"] == ["t1", "t2"]


class TestClusterConfig:
    """ClusterConfig 模型测试"""

    def test_create_cluster_config_defaults(self):
        config = ClusterConfig()
        assert config.alias == ""
        assert config.description == ""
        assert config.enabled is True
        assert config.extra == {}
        assert config.updated_at is None

    def test_create_cluster_config_full(self):
        now = datetime.now()
        config = ClusterConfig(
            alias="我的集群",
            description="测试集群",
            enabled=False,
            extra={"location": "北京", "env": "prod"},
            updated_at=now,
        )
        assert config.alias == "我的集群"
        assert config.description == "测试集群"
        assert config.enabled is False
        assert config.extra == {"location": "北京", "env": "prod"}
        assert config.updated_at == now

    def test_cluster_config_extra_dict_mutable(self):
        """extra 字段应该是可变的 dict"""
        config = ClusterConfig()
        config.extra["key"] = "value"
        assert config.extra["key"] == "value"

    def test_cluster_config_serialization(self):
        config = ClusterConfig(alias="test")
        data = config.model_dump()
        assert data["alias"] == "test"
        assert data["enabled"] is True
        assert data["extra"] == {}


class TestClusterConfigUpdate:
    """ClusterConfigUpdate 模型测试"""

    def test_create_full_update(self):
        update = ClusterConfigUpdate(
            alias="新别名",
            description="新描述",
            enabled=False,
            extra={"new_key": "new_value"},
        )
        assert update.alias == "新别名"
        assert update.description == "新描述"
        assert update.enabled is False
        assert update.extra == {"new_key": "new_value"}

    def test_create_partial_update(self):
        """部分字段更新：只改别名"""
        update = ClusterConfigUpdate(alias="新别名")
        assert update.alias == "新别名"
        assert update.description is None
        assert update.enabled is None
        assert update.extra is None

    def test_create_empty_update(self):
        update = ClusterConfigUpdate()
        assert update.alias is None
        assert update.description is None
        assert update.enabled is None
        assert update.extra is None

    def test_model_dump_exclude_unset(self):
        """测试 exclude_unset 仅导出已设置的字段"""
        update = ClusterConfigUpdate(alias="新别名")
        dumped = update.model_dump(exclude_unset=True)
        assert "alias" in dumped
        assert "description" not in dumped
        assert "enabled" not in dumped
        assert "extra" not in dumped


class TestClusterDetail:
    """ClusterDetail 模型测试"""

    def test_create_cluster_detail(self):
        detail = ClusterDetail(
            cluster_name="condor-prod",
            cluster_type="condor",
            tags=["t1", "t2"],
            alias="生产集群",
            description="测试",
            enabled=True,
            extra={},
        )
        assert detail.cluster_name == "condor-prod"
        assert detail.cluster_type == "condor"
        assert detail.tags == ["t1", "t2"]
        assert detail.alias == "生产集群"

    def test_create_cluster_detail_defaults(self):
        detail = ClusterDetail(cluster_name="test", cluster_type="slurm")
        assert detail.tags == []
        assert detail.alias == ""
        assert detail.description == ""
        assert detail.enabled is True
        assert detail.extra == {}
        assert detail.missing_fields == []


class TestClusterScheme:
    """ClusterScheme 模型测试（外部可视化用）"""

    def test_create_cluster_scheme(self):
        scheme = ClusterScheme(
            cluster_name="condor-prod",
            cluster_type="condor",
            tags=["t1"],
            alias="生产",
            enabled=True,
            extra={},
        )
        assert scheme.cluster_name == "condor-prod"
        # 确认 scheme 不包含 description/updated_at
        assert not hasattr(scheme, "description")

    def test_cluster_scheme_defaults(self):
        scheme = ClusterScheme(cluster_name="test", cluster_type="slurm")
        assert scheme.tags == []
        assert scheme.alias == ""
        assert scheme.enabled is True


class TestClusterListResponse:
    """ClusterListResponse 模型测试"""

    def test_create_list_response(self):
        clusters = [
            ClusterDetail(cluster_name="c1", cluster_type="condor"),
            ClusterDetail(cluster_name="c2", cluster_type="slurm"),
        ]
        resp = ClusterListResponse(clusters=clusters, total=10)
        assert len(resp.clusters) == 2
        assert resp.total == 10

    def test_empty_list_response(self):
        resp = ClusterListResponse(clusters=[], total=0)
        assert len(resp.clusters) == 0
        assert resp.total == 0


class TestClusterSchemeResponse:
    """ClusterSchemeResponse 模型测试"""

    def test_create_scheme_response(self):
        schemes = [
            ClusterScheme(cluster_name="c1", cluster_type="condor"),
        ]
        resp = ClusterSchemeResponse(clusters=schemes, total=1)
        assert len(resp.clusters) == 1
        assert resp.total == 1


class TestClusterExtraSchema:
    """ClusterExtraSchema 模型测试"""

    def test_required_field_names(self):
        names = ClusterExtraSchema.required_field_names()
        assert len(names) == 5
        assert "es_url" in names
        assert "es_username" in names
        assert "es_password" in names
        assert "default_node_port" in names
        assert "script_path" in names

    def test_get_missing_fields_all_missing(self):
        """空 extra 应报告所有 5 个字段缺失"""
        missing = ClusterExtraSchema.get_missing_fields({})
        assert len(missing) == 5

    def test_get_missing_fields_none_missing(self):
        """5 个必填字段都填了值应返回空列表"""
        extra = {
            "es_url": "http://es:9200",
            "es_username": "admin",
            "es_password": "secret",
            "default_node_port": 8080,
            "script_path": "/opt/scripts",
        }
        missing = ClusterExtraSchema.get_missing_fields(extra)
        assert missing == []

    def test_get_missing_fields_partial(self):
        """部分字段未填"""
        extra = {
            "es_url": "http://es:9200",
        }
        missing = ClusterExtraSchema.get_missing_fields(extra)
        assert "es_url" not in missing
        assert "es_username" in missing
        assert "es_password" in missing
        assert "default_node_port" in missing

    def test_get_missing_fields_empty_string(self):
        """空字符串视为缺失"""
        extra = {
            "es_url": "",
            "es_username": "admin",
        }
        missing = ClusterExtraSchema.get_missing_fields(extra)
        assert "es_url" in missing
        assert "es_username" not in missing

    def test_get_missing_fields_zero_port(self):
        """default_node_port 为 0 视为缺失"""
        extra = {"default_node_port": 0}
        missing = ClusterExtraSchema.get_missing_fields(extra)
        assert "default_node_port" in missing

        extra = {"default_node_port": 8080}
        missing = ClusterExtraSchema.get_missing_fields(extra)
        assert "default_node_port" not in missing

    def test_defaults(self):
        defaults = ClusterExtraSchema.defaults()
        assert defaults["es_url"] == ""
        assert defaults["default_node_port"] == 0

    def test_model_defaults(self):
        schema = ClusterExtraSchema()
        assert schema.timezone == "Asia/Shanghai"
        assert schema.es_url == ""
        assert schema.default_node_port == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
