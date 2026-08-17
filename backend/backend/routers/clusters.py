"""
集群管理 API 路由

职责：
- 从注册中心 ETCD 读取自动发现的集群数据
- 提供集群额外属性（别名/描述/启用/扩展）的 CRUD
- 提供外部可视化前端查询集群 scheme 的接口
"""
import json
from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.models import (
    ClusterDetail,
    ClusterConfig,
    ClusterConfigUpdate,
    ClusterExtraSchema,
    ClusterListResponse,
    ClusterScheme,
    ClusterSchemeResponse,
)
from backend.config import settings
from backend.common.logger import logger
from backend.common.etcd_client import get_etcd_client

router = APIRouter(tags=["clusters"])


def _get_cluster_instance_prefix() -> str:
    """获取注册中心集群实例路径前缀"""
    return settings.etcd_clusters_instance_prefix.replace("//", "/")


def _get_cluster_config_key(cluster_name: str) -> str:
    """获取本系统管理的集群配置 ETCD 键"""
    return f"{settings.etcd_config_prefix}clusters/{cluster_name}".replace("//", "/")


def _read_cluster_config(client, cluster_name: str) -> ClusterConfig:
    """从 ETCD 读取集群配置，不存在时返回默认值"""
    key = _get_cluster_config_key(cluster_name)
    value, _ = client.get(key)
    if value is None:
        return ClusterConfig()
    try:
        data = json.loads(value)
        return ClusterConfig(**data)
    except Exception:
        logger.warning(f"集群配置解析失败，使用默认值: cluster_name={cluster_name}")
        return ClusterConfig()


def _read_all_cluster_instances(client) -> list[dict]:
    """从 ETCD 读取注册中心自动发现的所有集群实例"""
    prefix = _get_cluster_instance_prefix()
    clusters = []
    try:
        for value, metadata in client.get_prefix(prefix):
            try:
                data = json.loads(value)
                clusters.append(data)
            except Exception:
                key_str = metadata.key.decode() if metadata.key else "unknown"
                logger.warning(f"集群实例数据解析失败，跳过: key={key_str}")
                continue
    except Exception as e:
        logger.error(f"读取集群实例列表失败: {str(e)}")
    return clusters


def _merge_cluster_detail(instance_data: dict, config: ClusterConfig) -> ClusterDetail:
    """合并注册中心数据与本地配置为完整视图"""
    return ClusterDetail(
        cluster_name=instance_data.get("cluster_name", ""),
        cluster_type=instance_data.get("cluster_type", ""),
        tags=instance_data.get("tags", []),
        alias=config.alias,
        description=config.description,
        enabled=config.enabled,
        extra=config.extra,
        missing_fields=ClusterExtraSchema.get_missing_fields(config.extra),
        updated_at=config.updated_at,
    )


def _merge_cluster_scheme(instance_data: dict, config: ClusterConfig) -> ClusterScheme:
    """合并为外部可视化用的精简视图"""
    return ClusterScheme(
        cluster_name=instance_data.get("cluster_name", ""),
        cluster_type=instance_data.get("cluster_type", ""),
        tags=instance_data.get("tags", []),
        alias=config.alias,
        enabled=config.enabled,
        extra=config.extra,
        missing_fields=ClusterExtraSchema.get_missing_fields(config.extra),
    )


@router.get("", response_model=ClusterListResponse, summary="获取所有集群列表")
async def get_clusters():
    """获取所有集群列表（合并自动发现数据 + 手动配置）"""
    logger.info("获取集群列表")
    try:
        client = get_etcd_client()
        instances = _read_all_cluster_instances(client)

        clusters = []
        for instance in instances:
            cluster_name = instance.get("cluster_name", "")
            if not cluster_name:
                continue
            config = _read_cluster_config(client, cluster_name)
            detail = _merge_cluster_detail(instance, config)
            clusters.append(detail)

        logger.info(f"获取集群列表成功: 总数={len(clusters)}")
        return ClusterListResponse(clusters=clusters, total=len(clusters))
    except Exception as e:
        logger.error(f"获取集群列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取集群列表失败: {str(e)}")


@router.get("/scheme", response_model=ClusterSchemeResponse, summary="获取集群 scheme（外部可视化用）")
async def get_clusters_scheme():
    """
    获取所有集群的 scheme 信息，供外部可视化前端使用。
    返回精简视图：cluster_name / cluster_type / tags / alias / enabled / extra
    """
    logger.info("获取集群 scheme")
    try:
        client = get_etcd_client()
        instances = _read_all_cluster_instances(client)

        clusters = []
        for instance in instances:
            cluster_name = instance.get("cluster_name", "")
            if not cluster_name:
                continue
            config = _read_cluster_config(client, cluster_name)
            scheme = _merge_cluster_scheme(instance, config)
            clusters.append(scheme)

        logger.info(f"获取集群 scheme 成功: 总数={len(clusters)}")
        return ClusterSchemeResponse(clusters=clusters, total=len(clusters))
    except Exception as e:
        logger.error(f"获取集群 scheme 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取集群 scheme 失败: {str(e)}")


@router.get("/{cluster_name}", response_model=ClusterDetail, summary="获取单个集群详情")
async def get_cluster(cluster_name: str):
    """获取单个集群的完整详情"""
    logger.info(f"获取集群详情: cluster_name={cluster_name}")
    try:
        client = get_etcd_client()

        # 从注册中心数据中查找该集群
        instances = _read_all_cluster_instances(client)
        instance_data = None
        for inst in instances:
            if inst.get("cluster_name") == cluster_name:
                instance_data = inst
                break

        if instance_data is None:
            raise HTTPException(status_code=404, detail=f"集群 '{cluster_name}' 不存在")

        config = _read_cluster_config(client, cluster_name)
        detail = _merge_cluster_detail(instance_data, config)

        logger.info(f"获取集群详情成功: cluster_name={cluster_name}")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取集群详情失败: cluster_name={cluster_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取集群详情失败: {str(e)}")


@router.put("/{cluster_name}/config", summary="更新集群配置属性")
async def update_cluster_config(cluster_name: str, config_update: ClusterConfigUpdate):
    """
    更新集群的额外配置属性（别名、描述、启用状态、扩展字段）。
    仅更新请求中提供的字段，未提供的字段保持不变。
    """
    logger.info(f"更新集群配置: cluster_name={cluster_name}, update={config_update.model_dump(exclude_unset=True)}")
    try:
        client = get_etcd_client()

        # 验证集群在注册中心数据中存在
        instances = _read_all_cluster_instances(client)
        instance_exists = any(
            inst.get("cluster_name") == cluster_name for inst in instances
        )
        if not instance_exists:
            raise HTTPException(status_code=404, detail=f"集群 '{cluster_name}' 不存在")

        # 读取现有配置
        existing_config = _read_cluster_config(client, cluster_name)

        # 只更新提供的字段
        update_dict = config_update.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(existing_config, key, value)

        existing_config.updated_at = datetime.now()

        # 写入 ETCD
        key = _get_cluster_config_key(cluster_name)
        client.put(key, existing_config.model_dump_json())

        logger.info(f"集群配置更新成功: cluster_name={cluster_name}")
        return {"message": f"集群 '{cluster_name}' 配置已更新", "cluster_name": cluster_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新集群配置失败: cluster_name={cluster_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"更新集群配置失败: {str(e)}")
