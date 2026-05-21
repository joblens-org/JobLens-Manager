"""
集群管理相关 Pydantic 模型

设计要点：
- 一个集群名称(cluster_name)可映射多个 tag（如 Condor 多 schedd 场景）
- 每个 tag 对应唯一的 jobid 空间
- 集群配置属性绑定在 cluster_name 级别，所有 tag 共享
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClusterInfo(BaseModel):
    """注册中心自动发现的集群原始信息（从 ETCD 读取）"""
    cluster_name: str = Field(..., description="集群名称")
    cluster_type: str = Field(..., description="集群类型（如 condor/slurm 等）")
    tags: list[str] = Field(default_factory=list, description="集群标签列表，每个标签对应唯一 jobid 空间")

    class Config:
        json_schema_extra = {
            "example": {
                "cluster_name": "my-condor-cluster",
                "cluster_type": "condor",
                "tags": ["tag-schedd-1", "tag-schedd-2"]
            }
        }


class ClusterConfig(BaseModel):
    """集群额外配置属性（由本系统维护）"""
    alias: str = Field("", description="集群别名，供其他模块调用")
    description: str = Field("", description="集群描述说明")
    enabled: bool = Field(True, description="是否启用")
    extra: dict = Field(default_factory=dict, description="JSON 自由扩展字段，供后续属性扩展使用")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "alias": "生产 Condor 集群",
                "description": "北京机房的 Condor 调度器集群",
                "enabled": True,
                "extra": {"location": "北京", "scheduler_version": "23.0"}
            }
        }


class ClusterConfigUpdate(BaseModel):
    """集群配置更新请求"""
    alias: Optional[str] = Field(None, description="集群别名")
    description: Optional[str] = Field(None, description="集群描述")
    enabled: Optional[bool] = Field(None, description="是否启用")
    extra: Optional[dict] = Field(None, description="扩展配置 JSON")


class ClusterExtraSchema(BaseModel):
    """
    extra 字段中 5 个必填项的 schema 定义
    
    仅用于校验和字段识别，不改变 extra 的存储结构。
    后续新增必填字段只需在 required_field_names() 中添加。
    """
    es_url: str = Field("", description="ElasticSearch 地址")
    es_username: str = Field("", description="ES 用户名")
    es_password: str = Field("", description="ES 密码")
    index_pattern: str = Field("", description="ES 索引模式")
    timezone: str = Field("Asia/Shanghai", description="时区")
    default_node_port: int = Field(0, description="默认节点端口")
    script_path: str = Field("", description="脚本路径")

    @staticmethod
    def required_field_names() -> list[str]:
        """返回 5 个必填字段名列表"""
        return [
            "es_url", "es_username", "es_password",
            "default_node_port", "script_path",
        ]

    @staticmethod
    def get_missing_fields(extra: dict) -> list[str]:
        """检查 extra 中缺失或为空值/零值的必填字段"""
        missing = []
        for field in ClusterExtraSchema.required_field_names():
            value = extra.get(field)
            if value is None or value == "" or value == 0:
                missing.append(field)
        return missing

    @staticmethod
    def defaults() -> dict:
        """返回所有必填字段的默认值"""
        return {
            "es_url": "",
            "es_username": "",
            "es_password": "",
            "default_node_port": 0,
            "script_path": "",
        }


class ClusterDetail(BaseModel):
    """集群完整信息（自动发现 + 手动配置合并）"""
    cluster_name: str
    cluster_type: str
    tags: list[str] = Field(default_factory=list)
    alias: str = ""
    description: str = ""
    enabled: bool = True
    extra: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list, description="未配置的必填字段列表")
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "cluster_name": "my-condor-cluster",
                "cluster_type": "condor",
                "tags": ["tag-schedd-1", "tag-schedd-2"],
                "alias": "生产 Condor 集群",
                "description": "北京机房 Condor 集群",
                "enabled": True,
                "extra": {},
                "updated_at": "2024-01-01T00:00:00"
            }
        }


class ClusterScheme(BaseModel):
    """外部可视化查询用的集群 scheme（精简版）"""
    cluster_name: str
    cluster_type: str
    tags: list[str] = Field(default_factory=list)
    alias: str = ""
    enabled: bool = True
    extra: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list, description="未配置的必填字段列表")

    class Config:
        json_schema_extra = {
            "example": {
                "cluster_name": "my-condor-cluster",
                "cluster_type": "condor",
                "tags": ["tag-schedd-1"],
                "alias": "生产集群",
                "enabled": True,
                "extra": {}
            }
        }


class ClusterListResponse(BaseModel):
    """集群列表响应"""
    clusters: list[ClusterDetail]
    total: int = Field(..., description="集群总数")


class ClusterSchemeResponse(BaseModel):
    """集群 scheme 列表响应"""
    clusters: list[ClusterScheme]
    total: int = Field(..., description="集群总数")
