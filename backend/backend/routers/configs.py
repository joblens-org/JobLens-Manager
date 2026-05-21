import asyncio
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.models import ConfigUpdate, VersionInfo
from backend.config import settings
from backend.common.etcd_client import get_etcd_client
import datetime
import yaml
import json

router = APIRouter()

def get_mode_path(mode: str) -> str:
    """获取模式配置的节点路径"""
    # 从 ETCD 中读取模式配置，获取其配置路径
    # 如果模式不存在，则使用默认路径 {mode}/config/config.yaml
    try:
        client = get_etcd_client()
        mode_key = f"/modes/{mode}"
        value, _ = client.get(mode_key)
        if value:
            # 解析模式信息，获取配置路径（如果模式信息中定义了）
            mode_info = json.loads(value)
            if 'config_path' in mode_info:
                return mode_info['config_path']
        # 默认路径
        return f"{mode}/config/config.yaml"
    except Exception:
        # 如果出错，也返回默认路径
        return f"{mode}/config/config.yaml"

def get_mode_dirpath(mode: str) -> str:
    """获取模式配置的目录路径"""
    # 类似 get_mode_path，但返回目录
    try:
        client = get_etcd_client()
        mode_key = f"/modes/{mode}"
        value, _ = client.get(mode_key)
        if value:
            mode_info = json.loads(value)
            if 'config_dir' in mode_info:
                return mode_info['config_dir']
        # 默认目录
        return f"{mode}/config"
    except Exception:
        return f"{mode}/config"

def validate_yaml(content: str) -> bool:
    """验证 YAML 内容是否合法
    
    Args:
        content: YAML 文本内容
        
    Returns:
        bool: 内容是否合法
        
    Raises:
        ValueError: 如果 YAML 格式不合法，抛出异常说明错误信息
    """
    try:
        yaml.safe_load(content)
        return True
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 格式错误: {str(e)}")
    except Exception as e:
        raise ValueError(f"YAML 验证失败: {str(e)}")

def ensure_mode_exists(mode: str):
    """确保模式存在，否则抛出 404 错误"""
    client = get_etcd_client()
    mode_key = f"/modes/{mode}"
    value, _ = client.get(mode_key)
    if not value:
        raise HTTPException(status_code=404, detail=f"模式 '{mode}' 不存在")

@router.get("/{mode}", summary="获取当前配置")
async def get_config(
    mode: str,
    include_metadata: bool = Query(False, description="是否包含元数据")
):
    """
    获取指定模式的当前配置（YAML 格式原文）
    """
    try:
        ensure_mode_exists(mode)
        client = get_etcd_client()
        node_path = get_mode_path(mode)
        # 获取当前值
        value, metadata = client.get(node_path)
        
        if value is None:
            raise HTTPException(status_code=404, detail=f"{mode} 模式配置不存在")
        
        # 直接返回 YAML 原文
        config_yaml = value.decode('utf-8') if isinstance(value, bytes) else value
        
        if include_metadata:
            return {
                "mode": mode,
                "config": config_yaml,
                "metadata": {
                    "version": metadata.version,
                    "create_revision": metadata.create_revision,
                    "mod_revision": metadata.mod_revision,
                    "lease_id": metadata.lease_id,
                    "key": metadata.key.decode() if metadata.key else None,
                }
            }
        else:
            return {
                "mode": mode,
                "config": config_yaml
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.put("/{mode}", summary="更新配置")
async def update_config(
    mode: str,
    config_update: ConfigUpdate
):
    """
    更新指定模式的配置（YAML 格式）
    
    - **config**: 新的配置内容（YAML 格式字符串）
    - **description**: 更新描述（可选）
    """
    try:
        ensure_mode_exists(mode)
        # 验证 YAML 格式的合法性
        try:
            validate_yaml(config_update.raw_config)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        client = get_etcd_client()
        node_path = get_mode_path(mode)
        
        # 获取当前配置以保存历史
        current_value, current_metadata = client.get(node_path)
        node_dir = get_mode_dirpath(mode)
        # 创建历史记录节点
        if current_value:
            history_path = f"{node_dir}/history/v{current_metadata.version}"
            client.put(history_path, current_value)
        desc_path = f"{node_dir}/last_update"
        update_info, _ = client.get(desc_path)
        if update_info:
            history_path = f"{node_dir}/history/update_v{current_metadata.version}"
            client.put(history_path, update_info)
            
        # 更新配置（直接存储 YAML 原文）
        client.put(node_path, config_update.raw_config)
        
        # 添加更新描述
        if config_update.description:
            desc_path = f"{node_dir}/last_update"
            desc_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "description": config_update.description,
                "user": "API"  # 实际应用中可以从认证信息中获取
            }
            client.put(desc_path, yaml.dump(desc_data, allow_unicode=True))
        
        # 获取更新后的元数据
        _, new_metadata = client.get(node_path)
        
        return {
            "mode": mode,
            "message": "配置更新成功",
            "new_version": new_metadata.version,
            "description": config_update.description,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.get("/{mode}/versions", summary="查看版本历史")
async def get_version_history(
    mode: str,
    limit: int = Query(10, ge=1, le=100, description="返回的历史版本数量")
):
    """
    获取指定模式的配置版本历史
    """
    try:
        ensure_mode_exists(mode)
        client = get_etcd_client()
        node_path = get_mode_path(mode)
        
        # 获取当前配置
        current_value, current_metadata = client.get(node_path)
        if current_value is None:
            raise HTTPException(status_code=404, detail=f"{mode} 模式配置不存在")
        
        versions = []
        
        # 添加当前版本
        versions.append({
            "version": current_metadata.version,
            "timestamp": datetime.datetime.now().isoformat(),
            "is_current": True
        })
        
        # 获取历史版本
        node_dir = get_mode_dirpath(mode)
        history_prefix = f"{node_dir}/history/"
        history_records = client.get_prefix(history_prefix)
        
        # 处理历史记录
        for value, metadata in history_records:
            try:
                # 从路径中提取版本号
                key_str = metadata.key.decode()
                version_str = key_str.replace(f"{node_dir}/history/v", "")
                version_num = int(version_str) if version_str.isdigit() else 0
                
                versions.append({
                    "version": version_num,
                    "key": key_str,
                    "is_current": False
                })
            except:
                continue
        
        # 按版本号降序排序
        versions.sort(key=lambda x: x["version"], reverse=True)
        
        # 限制返回数量
        versions = versions[:limit]
        
        return {
            "mode": mode,
            "total_versions": len(versions),
            "current_version": current_metadata.version,
            "versions": versions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本历史失败: {str(e)}")

@router.get("/{mode}/version/{version}", summary="获取特定版本配置")
async def get_specific_version(
    mode: str,
    version: str
):
    """
    获取指定模式的特定版本配置（YAML 格式原文）
    
    - **version**: 版本号或 'current'（当前版本）
    """
    try:
        ensure_mode_exists(mode)
        client = get_etcd_client()
        node_path = get_mode_path(mode)
        
        if version == "current":
            # 获取当前版本
            value, metadata = client.get(node_path)
            if value is None:
                raise HTTPException(status_code=404, detail=f"{mode} 模式配置不存在")
        else:
            # 获取历史版本
            if version.startswith("v"):
                version_key = version
            else:
                version_key = f"v{version}"
            node_dir = get_mode_dirpath(mode)
            history_path = f"{node_dir}/history/{version_key}"
            value, metadata = client.get(history_path)
            
            if value is None:
                raise HTTPException(status_code=404, detail=f"版本 {version} 不存在")
        
        # 直接返回 YAML 原文
        config_yaml = value.decode('utf-8') if isinstance(value, bytes) else value
        
        return {
            "mode": mode,
            "version": version if version == "current" else version_key,
            "config": config_yaml,
            "metadata": {
                "mod_revision": metadata.mod_revision,
                "create_revision": metadata.create_revision,
                "lease_id": metadata.lease_id,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本配置失败: {str(e)}")

@router.post("/{mode}/rollback/{version}", summary="回滚到指定版本")
async def rollback_to_version(
    mode: str,
    version: str,
    description: Optional[str] = "版本回滚"
):
    """
    将配置回滚到指定版本
    """
    try:
        ensure_mode_exists(mode)
        client = get_etcd_client()
        node_path = get_mode_path(mode)
        
        # 获取目标版本配置
        if version.startswith("v"):
            version_key = version
        else:
            version_key = f"v{version}"
        node_dir = get_mode_dirpath(mode)
        history_path = f"{node_dir}/history/{version_key}"
        target_value, target_metadata = client.get(history_path)
        
        if target_value is None:
            raise HTTPException(status_code=404, detail=f"版本 {version} 不存在")
        
        # 获取当前配置以保存历史
        current_value, current_metadata = client.get(node_path)
        if current_value:
            current_history_path = f"{node_dir}/history/v{current_metadata.version}"
            client.put(current_history_path, current_value)
        
        # 回滚到目标版本
        client.put(node_path, target_value)
        
        # 添加回滚描述
        desc_path = f"{node_dir}/last_rollback"
        desc_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "from_version": current_metadata.version if current_value else None,
            "to_version": version_key,
            "description": description,
            "user": "API"
        }
        client.put(desc_path, yaml.dump(desc_data, allow_unicode=True))
        
        return {
            "mode": mode,
            "message": "回滚成功",
            "from_version": current_metadata.version if current_value else None,
            "to_version": version_key,
            "description": description,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回滚失败: {str(e)}")

@router.get("/health", summary="健康检查")
async def health_check():
    """
    服务健康检查
    """
    try:
        client = get_etcd_client()
        
        # 测试 ETCD 连接
        status = client.status()
        
        return {
            "status": "healthy",
            "etcd": {
                "connected": True,
                "version": status.version,
                "db_size": status.db_size,
                "leader": str(status.leader),
                "raft_term": status.raft_term
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "etcd": {
                "connected": False,
                "error": str(e)
            },
            "timestamp": datetime.datetime.now().isoformat()
        }

@router.get("/modes", summary="获取所有模式信息")
async def get_all_modes():
    """
    获取所有模式的配置状态
    """
    try:
        client = get_etcd_client()
        modes = []
        
        # 从 ETCD 中读取所有模式
        prefix = "/modes/"
        mode_records = client.get_prefix(prefix)
        
        for value, metadata in mode_records:
            try:
                key_str = metadata.key.decode()
                mode_name = key_str.replace(prefix, "")
                if not mode_name:
                    continue
                    
                mode_info = json.loads(value)
                modes.append({
                    "mode": mode_name,
                    "exists": True,
                    "info": mode_info
                })
            except:
                continue
        
        # 如果没有模式记录，返回空列表
        return {
            "modes": modes,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模式信息失败: {str(e)}")