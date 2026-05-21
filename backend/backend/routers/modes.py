import asyncio
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import yaml
import json
from datetime import datetime

from backend.models import (
    ModeInfo, ModeCreate, ModeUpdate, ModeConfigUpdate, ModeListResponse
)
from backend.config import settings
from backend.common.logger import logger
from backend.common.etcd_client import get_etcd_client

router = APIRouter(tags=["modes"])


def get_mode_config_path(mode_name: str) -> str:
    """获取模式配置路径"""
    return f"{settings.etcd_config_prefix}modes/{mode_name}/config/config.yaml".replace('//','/')


def get_mode_info_path(mode_name: str) -> str:
    """获取模式信息路径"""
    return f"{settings.etcd_config_prefix}modes/{mode_name}/info".replace('//','/')


def get_mode_config_history_path(mode_name: str, version: str) -> str:
    """获取模式配置历史路径"""
    return f"{settings.etcd_config_prefix}modes/{mode_name}/config/history/{version}".replace('//','/')

def set_default_mode(client, mode_name: str):
    """设置默认模式，确保只有一个默认模式"""
    default_mode_path = f"{settings.etcd_config_prefix}/modes/default_name".replace('//','/')
    # 先将当前默认模式的default设置为False
    value, _ = client.get(default_mode_path)
    if value:
        current_default = value.decode('utf-8')
        if current_default != mode_name:
            # 更新当前默认模式的信息
            current_default_info_path = get_mode_info_path(current_default)
            current_default_info_json, _ = client.get(current_default_info_path)
            if current_default_info_json:
                current_default_info_dict = json.loads(current_default_info_json)
                current_default_info_dict["default"] = False
                client.put(current_default_info_path, json.dumps(current_default_info_dict))
        else:
            # 已经是默认模式，无需更新
            return

    client.put(default_mode_path, mode_name)
    current_default_path = get_mode_info_path(mode_name)
    current_default_info_json, _ = client.get(current_default_path)
    if current_default_info_json:
        current_default_info_dict = json.loads(current_default_info_json)
        current_default_info_dict["default"] = True
        client.put(current_default_path, json.dumps(current_default_info_dict))


def get_default_mode(client) -> Optional[str]:
    """获取当前默认模式名称"""
    default_mode_path = f"{settings.etcd_config_prefix}modes/default_name"
    value, _ = client.get(default_mode_path)
    if value:
        return value.decode('utf-8')
    return None


def create_mode_sync(
    client,
    name: str,
    description: str = "",
    default: bool = False
) -> ModeInfo:
    """
    同步创建新模式（用于初始化）
    
    Args:
        client: ETCD 客户端
        name: 模式名称
        description: 模式描述
        default: 是否为默认模式
        
    Returns:
        ModeInfo: 创建的模式信息
        
    Raises:
        ValueError: 如果模式名称不合法
        Exception: 如果模式已存在或创建失败
    """
    logger.info(f"创建模式: name={name}, default={default}")
    
    # 验证模式名称
    if not validate_mode_name(name):
        logger.warning(f"模式名称不合法: name={name}")
        raise ValueError("模式名称不合法，只允许字母、数字和短横线，且长度不超过50字符")
    
    mode_info_path = get_mode_info_path(name)
    
    # 检查模式是否已存在
    existing_info, _ = client.get(mode_info_path)
    if existing_info is not None:
        logger.warning(f"模式已存在: name={name}")
        raise Exception(f"模式 '{name}' 已存在")
    
    # 创建模式信息
    mode_info = ModeInfo(
        name=name,
        description=description,
        default=default
    )
    
    # 保存模式信息到ETCD
    client.put(mode_info_path, mode_info.model_dump_json())
    
    # 创建配置目录结构
    config_path = get_mode_config_path(name)
    client.put(config_path, "# 新建模式配置\n# 请在此处添加配置内容\n")
    
    # 如果是默认模式，更新其他模式的default状态
    if default:
        set_default_mode(client=client, mode_name=name)
        logger.info(f"设置模式为默认: name={name}")
    
    logger.info(f"模式创建成功: name={name}")
    return mode_info



def get_services_by_mode(client, mode_name: str) -> List[str]:
    """获取使用指定模式的服务列表"""
    # TODO: 这里如果要优化性能，需要进行反查，可以在服务注册时维护一个模式到服务ID的映射关系，避免全量扫描
    services = []
    registry_path_prefix = f"{settings.etcd_services_prefix}"
    try:
        for value, metadata in client.get_prefix(registry_path_prefix):
            if metadata.key.endswith(b'/mode'):
                service_mode_name = value.decode('utf-8')
                if service_mode_name == mode_name:
                    service_id = metadata.key.decode('utf-8').split('/')[-2]
                    services.append(service_id)
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")


def is_mode_exist(client, mode_name: str) -> bool:
    """检查模式是否存在"""
    mode_info_path = f"{settings.etcd_config_prefix}modes/{mode_name}/info"
    mode_info_json, _ = client.get(mode_info_path)
    return mode_info_json is not None


def validate_mode_name(mode_name: str) -> bool:
    """验证模式名称是否合法（只允许字母、数字、短横线）"""
    if not mode_name or len(mode_name) > 50:
        return False
    # 只允许字母、数字、短横线
    return all(c.isalnum() or c == '-' for c in mode_name)


def validate_yaml(content: str) -> bool:
    """验证 YAML 内容是否合法"""
    try:
        yaml.safe_load(content)
        return True
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 格式错误: {str(e)}")
    except Exception as e:
        raise ValueError(f"YAML 验证失败: {str(e)}")


async def get_all_modes_from_etcd(client) -> List[ModeInfo]:
    """从ETCD获取所有模式信息"""
    modes_path_prefix = f"{settings.etcd_config_prefix}modes/"
    modes = []
    try:
        for value, metadata in client.get_prefix(modes_path_prefix):
            # 只处理模式信息文件（/info结尾）
            if metadata.key.endswith(b'/info'):
                mode_info_dict = json.loads(value)
                modes.append(ModeInfo(**mode_info_dict))
        return modes
    except Exception as e:
        logger.error(f"从ETCD获取模式列表失败: {str(e)}")
        return []


@router.get("/", response_model=ModeListResponse, summary="获取所有模式列表")
async def get_modes():
    """获取所有模式列表"""
    logger.info("获取模式列表")
    try:
        client = get_etcd_client()
        modes = await get_all_modes_from_etcd(client)
        logger.info(f"获取模式列表成功: 总数={len(modes)}")
        return ModeListResponse(modes=modes, total=len(modes))
    except Exception as e:
        logger.error(f"获取模式列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模式列表失败: {str(e)}")


@router.post("/", response_model=ModeInfo, summary="创建新模式")
async def create_mode(mode_create: ModeCreate):
    """创建新模式"""
    logger.info(f"创建模式: name={mode_create.name}, default={mode_create.default}")
    try:
        client = get_etcd_client()
        # 使用 create_mode_sync 函数创建模式
        mode_info = create_mode_sync(
            client=client,
            name=mode_create.name,
            description=mode_create.description,
            default=mode_create.default or False
        )
        logger.info(f"模式创建成功: name={mode_create.name}")
        return mode_info
    except ValueError as e:
        logger.warning(f"模式名称不合法: name={mode_create.name}, error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "已存在" in str(e):
            logger.warning(f"模式已存在: name={mode_create.name}")
            raise HTTPException(status_code=409, detail=str(e))
        logger.error(f"创建模式失败: name={mode_create.name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"创建模式失败: {str(e)}")


@router.get("/{mode_name}", response_model=ModeInfo, summary="获取模式详情")
async def get_mode(mode_name: str):
    """获取模式详情"""
    logger.info(f"获取模式详情: mode_name={mode_name}")
    try:
        client = get_etcd_client()
        mode_info_path = get_mode_info_path(mode_name)
        
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"模式不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 不存在")
        
        # 解析模式信息
        mode_info_dict = json.loads(mode_info_json)
        
        # 统计配置数量
        config_path = get_mode_config_path(mode_name)
        config_value, _ = client.get(config_path)
        config_count = 1 if config_value is not None else 0
        
        mode_info_dict["config_count"] = config_count
        
        logger.debug(f"获取模式详情成功: mode_name={mode_name}, config_count={config_count}")
        return ModeInfo(**mode_info_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模式详情失败: mode_name={mode_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模式详情失败: {str(e)}")


@router.put("/{mode_name}", response_model=ModeInfo, summary="更新模式信息")
async def update_mode(mode_name: str, mode_update: ModeUpdate):
    """更新模式信息"""
    logger.info(f"更新模式信息: mode_name={mode_name}, update_data={mode_update.model_dump(exclude_unset=True)}")
    try:
        client = get_etcd_client()
        mode_info_path = get_mode_info_path(mode_name)
        
        # 获取现有模式信息
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"模式不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 不存在")
        
        # 解析现有信息
        mode_info_dict = json.loads(mode_info_json)
        existing_mode = ModeInfo(**mode_info_dict)
        
        # 更新字段
        update_dict = mode_update.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(existing_mode, key, value)
        
        if existing_mode.default:
            set_default_mode(client=client, mode_name=mode_name)
            logger.info(f"设置模式为默认: mode_name={mode_name}")
        
        # 更新时间
        existing_mode.updated_at = datetime.now()
        
        # 保存更新
        client.put(mode_info_path, existing_mode.model_dump_json())
        
        logger.info(f"模式更新成功: mode_name={mode_name}, name={existing_mode.name}")
        return existing_mode
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新模式失败: mode_name={mode_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"更新模式失败: {str(e)}")


@router.delete("/{mode_name}", summary="删除模式")
async def delete_mode(mode_name: str):
    """删除模式（危险操作，需要确认）"""
    logger.warning(f"删除模式: mode_name={mode_name}")
    try:
        client = get_etcd_client()
        mode_info_path = get_mode_info_path(mode_name)
        
        # 检查模式是否存在
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"模式不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 不存在")
        
        service_ids = get_services_by_mode(client, mode_name)
        if service_ids:
            logger.warning(f"模式正在被使用，无法删除: mode_name={mode_name}, service_ids={service_ids}")
            raise HTTPException(
                status_code=400, 
                detail=f"模式 '{mode_name}' 正在被以下服务使用，无法删除: {', '.join(service_ids)}"
            )
            return
        # 删除模式信息和配置
        client.delete_prefix(f"{settings.etcd_config_prefix}modes/{mode_name}/")
        
        logger.info(f"模式删除成功: mode_name={mode_name}")
        return {"message": f"模式 '{mode_name}' 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模式失败: mode_name={mode_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"删除模式失败: {str(e)}")


@router.get("/{mode_name}/config", summary="获取模式配置")
async def get_mode_config(mode_name: str, include_metadata: bool = Query(False, description="是否包含元数据")):
    """获取模式配置（YAML格式）"""
    logger.info(f"获取模式配置: mode_name={mode_name}, include_metadata={include_metadata}")
    try:
        client = get_etcd_client()
        config_path = get_mode_config_path(mode_name)
        
        value, metadata = client.get(config_path)
        
        if value is None:
            logger.warning(f"模式配置不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 的配置不存在")
        
        config_yaml = value.decode('utf-8') if isinstance(value, bytes) else value
        
        logger.debug(f"获取模式配置成功: mode_name={mode_name}, 配置长度={len(config_yaml)}")
        
        if include_metadata:
            return {
                "mode": mode_name,
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
                "mode": mode_name,
                "config": config_yaml
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置失败: mode_name={mode_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/{mode_name}/config", summary="更新模式配置")
async def update_mode_config(mode_name: str, config_update: ModeConfigUpdate):
    """更新模式配置"""
    logger.info(f"更新模式配置: mode_name={mode_name}, 配置长度={len(config_update.raw_config)}")
    try:
        # 验证YAML格式
        validate_yaml(config_update.raw_config)
        
        client = get_etcd_client()
        config_path = get_mode_config_path(mode_name)
        
        # 检查模式是否存在
        mode_info_path = get_mode_info_path(mode_name)
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"模式不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 不存在")
        
        # 保存当前配置为历史版本
        current_value, current_metadata = client.get(config_path)
        if current_value is not None:
            version = f"v{current_metadata.mod_revision}"
            history_path = get_mode_config_history_path(mode_name, version)
            history_data = {
                "config": current_value.decode('utf-8') if isinstance(current_value, bytes) else current_value,
                "description": f"自动保存的历史版本 {version}",
                "timestamp": datetime.now().isoformat(),
                "version": version
            }
            client.put(history_path, json.dumps(history_data))
            logger.debug(f"保存当前配置为历史版本: mode_name={mode_name}, version={version}")
        
        # 更新配置
        client.put(config_path, config_update.raw_config)
        
        # 更新模式信息中的更新时间
        mode_info_dict = json.loads(mode_info_json)
        mode_info_dict["updated_at"] = datetime.now().isoformat()
        client.put(mode_info_path, json.dumps(mode_info_dict))
        
        logger.info(f"模式配置更新成功: mode_name={mode_name}")
        return {"message": f"模式 '{mode_name}' 配置已更新"}
    except ValueError as e:
        logger.warning(f"YAML验证失败: mode_name={mode_name}, error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: mode_name={mode_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/{mode_name}/versions", summary="获取配置版本历史")
async def get_mode_config_versions(mode_name: str, limit: int = Query(10, description="返回的历史版本数量")):
    """获取模式配置的版本历史"""
    logger.info(f"获取配置版本历史: mode_name={mode_name}, limit={limit}")
    try:
        client = get_etcd_client()
        
        # 检查模式是否存在
        mode_info_path = get_mode_info_path(mode_name)
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"模式不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 不存在")
        
        # 获取当前配置的元数据
        config_path = get_mode_config_path(mode_name)
        current_value, current_metadata = client.get(config_path)
        
        if current_value is None:
            logger.warning(f"模式配置不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 的配置不存在")
        
        versions = []
        
        # 添加当前版本
        versions.append({
            "version": f"v{current_metadata.mod_revision}",
            "timestamp": datetime.now().isoformat(),
            "is_current": True,
            "description": "当前版本"
        })
        
        # 获取历史版本
        history_prefix = f"{settings.etcd_config_prefix}modes/{mode_name}/config/history/"
        history_records = client.get_prefix(history_prefix)
        
        # 处理历史记录
        history_count = 0
        for value, metadata in history_records:
            try:
                # 从路径中提取版本号
                key_str = metadata.key.decode()
                version_str = key_str.replace(f"{history_prefix}", "")
                
                # 解析历史版本数据
                history_data = json.loads(value)
                version_info = {
                    "version": history_data.get("version", version_str),
                    "timestamp": history_data.get("timestamp", datetime.now().isoformat()),
                    "is_current": False,
                    "description": history_data.get("description", ""),
                    "config_preview": history_data.get("config", "")[:100] + "..." if history_data.get("config") else ""
                }
                versions.append(version_info)
                history_count += 1
            except Exception:
                continue
        
        logger.debug(f"获取到历史版本: mode_name={mode_name}, 历史版本数={history_count}")
        
        # 按版本号降序排序（当前版本在最前面）
        versions.sort(key=lambda x: (x["is_current"], x["version"]), reverse=True)
        
        # 限制返回数量
        versions = versions[:limit]
        
        logger.info(f"获取版本历史成功: mode_name={mode_name}, 总数={len(versions)}, 当前版本=v{current_metadata.mod_revision}")
        return {
            "mode": mode_name,
            "versions": versions,
            "total": len(versions),
            "current_version": f"v{current_metadata.mod_revision}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取版本历史失败: mode_name={mode_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取版本历史失败: {str(e)}")


@router.post("/{mode_name}/rollback/{version}", summary="回滚到指定版本")
async def rollback_mode_config(mode_name: str, version: str):
    """回滚模式配置到指定版本"""
    logger.info(f"回滚配置到指定版本: mode_name={mode_name}, version={version}")
    try:
        client = get_etcd_client()
        
        # 检查模式是否存在
        mode_info_path = get_mode_info_path(mode_name)
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"模式不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 不存在")
        
        # 获取目标版本配置
        history_path = get_mode_config_history_path(mode_name, version)
        target_value, target_metadata = client.get(history_path)
        
        if target_value is None:
            logger.warning(f"版本不存在: mode_name={mode_name}, version={version}")
            raise HTTPException(status_code=404, detail=f"版本 '{version}' 不存在")
        
        # 解析目标版本数据
        target_data = json.loads(target_value)
        target_config = target_data.get("config", "")
        
        # 获取当前配置以保存历史
        config_path = get_mode_config_path(mode_name)
        current_value, current_metadata = client.get(config_path)
        
        if current_value is not None:
            # 保存当前配置为历史版本
            current_version = f"v{current_metadata.mod_revision}"
            current_history_path = get_mode_config_history_path(mode_name, current_version)
            current_history_data = {
                "config": current_value.decode('utf-8') if isinstance(current_value, bytes) else current_value,
                "description": f"回滚前的版本 {current_version}",
                "timestamp": datetime.now().isoformat(),
                "version": current_version
            }
            client.put(current_history_path, json.dumps(current_history_data))
            logger.debug(f"保存当前配置为历史版本: mode_name={mode_name}, version={current_version}")
        
        # 回滚到目标版本
        client.put(config_path, target_config)
        
        # 更新模式信息中的更新时间
        mode_info_dict = json.loads(mode_info_json)
        mode_info_dict["updated_at"] = datetime.now().isoformat()
        client.put(mode_info_path, json.dumps(mode_info_dict))
        
        logger.info(f"配置回滚成功: mode_name={mode_name}, from_version=v{current_metadata.mod_revision if current_value else 'None'}, to_version={version}")
        return {
            "message": f"模式 '{mode_name}' 配置已回滚到版本 {version}",
            "mode": mode_name,
            "from_version": f"v{current_metadata.mod_revision}" if current_value else None,
            "to_version": version,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回滚配置失败: mode_name={mode_name}, version={version}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"回滚配置失败: {str(e)}")


@router.get("/{mode_name}/version/{version}", summary="获取特定版本配置")
async def get_specific_version(mode_name: str, version: str):
    """获取指定模式的特定版本配置（YAML格式原文）"""
    logger.info(f"获取特定版本配置: mode_name={mode_name}, version={version}")
    try:
        client = get_etcd_client()
        
        # 检查模式是否存在
        mode_info_path = get_mode_info_path(mode_name)
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"模式不存在: mode_name={mode_name}")
            raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 不存在")
        
        if version == "current":
            # 获取当前版本
            config_path = get_mode_config_path(mode_name)
            value, metadata = client.get(config_path)
            if value is None:
                logger.warning(f"模式配置不存在: mode_name={mode_name}")
                raise HTTPException(status_code=404, detail=f"模式 '{mode_name}' 的配置不存在")
        else:
            # 获取历史版本
            if not version.startswith("v"):
                version = f"v{version}"
            history_path = get_mode_config_history_path(mode_name, version)
            value, metadata = client.get(history_path)
            
            if value is None:
                logger.warning(f"版本不存在: mode_name={mode_name}, version={version}")
                raise HTTPException(status_code=404, detail=f"版本 '{version}' 不存在")
            
            # 解析历史版本数据
            history_data = json.loads(value)
            config_yaml = history_data.get("config", "")
            logger.debug(f"获取历史版本成功: mode_name={mode_name}, version={version}")
            return {
                "mode": mode_name,
                "version": version,
                "config": config_yaml,
                "metadata": {
                    "timestamp": history_data.get("timestamp"),
                    "description": history_data.get("description", ""),
                }
            }
        
        # 直接返回 YAML 原文
        config_yaml = value.decode('utf-8') if isinstance(value, bytes) else value
        
        logger.debug(f"获取当前版本成功: mode_name={mode_name}, version={version}")
        return {
            "mode": mode_name,
            "version": version if version == "current" else version,
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
        logger.error(f"获取版本配置失败: mode_name={mode_name}, version={version}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取版本配置失败: {str(e)}")


@router.get("/default", response_model=ModeInfo, summary="获取默认模式")
async def get_default_mode_api():
    """获取当前默认模式的详细信息"""
    logger.info("获取默认模式")
    try:
        client = get_etcd_client()
        
        # 获取默认模式名称
        default_mode_name = get_default_mode(client)
        if default_mode_name is None:
            logger.warning("未设置默认模式")
            raise HTTPException(status_code=404, detail="未设置默认模式")
        
        # 获取默认模式的详细信息
        mode_info_path = get_mode_info_path(default_mode_name)
        mode_info_json, _ = client.get(mode_info_path)
        if mode_info_json is None:
            logger.warning(f"默认模式不存在: mode_name={default_mode_name}")
            raise HTTPException(status_code=404, detail=f"默认模式 '{default_mode_name}' 不存在")
        
        # 解析模式信息
        mode_info_dict = json.loads(mode_info_json)
        
        # 统计配置数量
        config_path = get_mode_config_path(default_mode_name)
        config_value, _ = client.get(config_path)
        config_count = 1 if config_value is not None else 0
        
        mode_info_dict["config_count"] = config_count
        
        logger.info(f"获取默认模式成功: mode_name={default_mode_name}")
        return ModeInfo(**mode_info_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取默认模式失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取默认模式失败: {str(e)}")
