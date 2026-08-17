import asyncio
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime
from ..common.logger import logger
from backend.common.etcd_client import get_etcd_client

from backend.models import (
    RoleInfo, RoleCreate, RoleUpdate, RoleListResponse,
    RuleInfo, RuleListResponse
)
from backend.config import settings

router = APIRouter(tags=["roles"])


def get_role_info_path(role_id: str) -> str:
    """获取角色信息路径"""
    return f"{settings.etcd_config_prefix}/roles/{role_id}/info".replace('//','/')


def set_default_role_id(client, role_id: str):
    default_mode_path = f"{settings.etcd_config_prefix}/roles/default_roleid".replace('//','/')
    # 先将当前默认模式的default设置为False
    value, _ = client.get(default_mode_path)
    if value:
        current_default = value.decode('utf-8')
        if current_default != role_id:
            # 更新当前默认模式的信息
            current_default_info_path = get_role_info_path(current_default)
            current_default_info_json, _ = client.get(current_default_info_path)
            if current_default_info_json:
                current_default_info_dict = json.loads(current_default_info_json)
                current_default_info_dict["default"] = False
                client.put(current_default_info_path, json.dumps(current_default_info_dict))
        else:
            # 已经是默认模式，无需更新
            return

    client.put(default_mode_path, role_id)
    current_default_path = get_role_info_path(role_id)
    current_default_info_json, _ = client.get(current_default_path)
    if current_default_info_json:
        current_default_info_dict = json.loads(current_default_info_json)
        current_default_info_dict["default"] = True
        client.put(current_default_path, json.dumps(current_default_info_dict))


def get_default_role_id(client) -> Optional[str]:
    """获取默认角色ID"""
    default_mode_path = f"{settings.etcd_config_prefix}/roles/default_roleid".replace('//','/')
    value, _ = client.get(default_mode_path)
    if value:
        return value.decode('utf-8')
    return None


def get_service_by_role_id(client, role_id: str) -> List[str]:
    """获取使用指定角色的服务列表"""
    # TODO: 这里如果要优化性能，需要进行反查，可以在服务注册时维护一个模式到服务ID的映射关系，避免全量扫描
    services = []
    registry_path_prefix = f"{settings.etcd_services_prefix}"
    try:
        for value, metadata in client.get_prefix(registry_path_prefix):
            if metadata.key.endswith(b'/role'):
                service_role_id = value.decode('utf-8')
                if service_role_id == role_id:
                    service_id = metadata.key.decode('utf-8').split('/')[-2]
                    services.append(service_id)
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")

def validate_role_name(role_name: str) -> bool:
    """验证角色名称是否合法"""
    if not role_name or len(role_name) > 100:
        return False
    # 允许字母、数字、短横线、下划线
    return all(c.isalnum() or c in ['-', '_'] for c in role_name)


async def get_all_roles_from_etcd(client) -> List[RoleInfo]:
    """从ETCD获取所有角色信息"""
    roles_path_prefix = f"{settings.etcd_config_prefix}/roles/".replace('//','/')
    roles = []
    try:
        for value, metadata in client.get_prefix(roles_path_prefix):
            logger.debug(f"ETCD Key: {metadata.key.decode('utf-8')}, Value: {value.decode('utf-8')}")
            if metadata.key.endswith(b'/info'):
                role_info_dict = json.loads(value)
                roles.append(RoleInfo(**role_info_dict))
        return roles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色信息失败: {str(e)}")
    

async def is_role_exist(client, role_id: str) -> bool:
    """检查角色是否存在"""
    role_info_path = get_role_info_path(role_id)
    role_info_json, _ = client.get(role_info_path)
    return role_info_json is not None


def create_role_sync(
    client,
    name: str,
    description: str = "",
    parent_role_id: Optional[str] = None,
    rule_ids: Optional[List[str]] = None
) -> RoleInfo:
    """
    同步创建新角色（用于初始化）
    
    Args:
        client: ETCD 客户端
        name: 角色名称
        description: 角色描述
        parent_role_id: 父角色ID
        rule_ids: 规则ID列表
        
    Returns:
        RoleInfo: 创建的角色信息
        
    Raises:
        ValueError: 如果角色名称不合法
        Exception: 如果角色已存在或创建失败
    """
    logger.info(f"创建角色: name={name}, parent_role_id={parent_role_id}")
    
    # 验证角色名称
    if not validate_role_name(name):
        logger.warning(f"角色名称不合法: name={name}")
        raise ValueError("角色名称不合法，只允许字母、数字、短横线和下划线")
    
    # 检查角色名称是否已存在（需要扫描所有角色）
    all_roles = get_all_roles_from_etcd_sync(client)
    for role in all_roles:
        if role.name == name:
            logger.warning(f"角色名称已存在: name={name}")
            raise Exception(f"角色名称 '{name}' 已存在")
    
    # 如果指定了父角色，验证父角色存在
    if parent_role_id:
        parent_role_info_path = get_role_info_path(parent_role_id)
        parent_role_json, _ = client.get(parent_role_info_path)
        if parent_role_json is None:
            logger.warning(f"父角色不存在: parent_role_id={parent_role_id}")
            raise Exception(f"父角色 '{parent_role_id}' 不存在")
    
    # 创建角色信息
    role_info = RoleInfo(
        name=name,
        description=description,
        parent_role_id=parent_role_id,
        rule_ids=rule_ids or []
    )
    
    # 保存角色信息到ETCD
    role_info_path = get_role_info_path(role_info.role_id)
    client.put(role_info_path, role_info.model_dump_json())
    
    logger.info(f"角色创建成功: role_id={role_info.role_id}, name={role_info.name}")
    return role_info


def get_all_roles_from_etcd_sync(client) -> List[RoleInfo]:
    """从ETCD获取所有角色信息（同步版本）"""
    roles_path_prefix = f"{settings.etcd_config_prefix}/roles/".replace('//','/')
    roles = []
    try:
        for value, metadata in client.get_prefix(roles_path_prefix):
            if metadata.key.endswith(b'/info'):
                role_info_dict = json.loads(value)
                roles.append(RoleInfo(**role_info_dict))
        return roles
    except Exception as e:
        logger.error(f"从ETCD获取角色列表失败: {str(e)}")
        return []






@router.get("", response_model=RoleListResponse, summary="获取所有角色列表")
async def get_roles():
    """获取所有角色列表"""
    logger.info("获取角色列表")
    try:
        client = get_etcd_client()
        roles = await get_all_roles_from_etcd(client)
        logger.info(f"获取角色列表成功: 总数={len(roles)}")
        return RoleListResponse(roles=roles, total=len(roles))
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色列表失败: {str(e)}")


@router.post("", response_model=RoleInfo, summary="创建新角色")
async def create_role(role_create: RoleCreate):
    """创建新角色"""
    logger.info(f"创建角色: name={role_create.name}, parent_role_id={role_create.parent_role_id}")
    try:
        client = get_etcd_client()
        # 使用 create_role_sync 函数创建角色
        role_info = create_role_sync(
            client=client,
            name=role_create.name,
            description=role_create.description,
            parent_role_id=role_create.parent_role_id,
            rule_ids=role_create.rule_ids
        )
        logger.info(f"角色创建成功: role_id={role_info.role_id}, name={role_info.name}")
        return role_info
    except ValueError as e:
        logger.warning(f"角色名称不合法: name={role_create.name}, error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "已存在" in str(e):
            logger.warning(f"角色名称已存在: name={role_create.name}")
            raise HTTPException(status_code=409, detail=str(e))
        if "父角色" in str(e):
            logger.warning(f"父角色不存在: parent_role_id={role_create.parent_role_id}")
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"创建角色失败: name={role_create.name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"创建角色失败: {str(e)}")


@router.get("/{role_id}", response_model=RoleInfo, summary="获取角色详情")
async def get_role(role_id: str):
    """获取角色详情"""
    logger.info(f"获取角色详情: role_id={role_id}")
    try:
        client = get_etcd_client()
        role_info_path = get_role_info_path(role_id)
        
        role_info_json, _ = client.get(role_info_path)
        if role_info_json is None:
            logger.warning(f"角色不存在: role_id={role_id}")
            raise HTTPException(status_code=404, detail=f"角色 '{role_id}' 不存在")
        
        role_info_dict = json.loads(role_info_json)
        logger.debug(f"获取角色详情成功: role_id={role_id}, name={role_info_dict.get('name')}")
        return RoleInfo(**role_info_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: role_id={role_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色详情失败: {str(e)}")


@router.put("/{role_id}", response_model=RoleInfo, summary="更新角色信息")
async def update_role(role_id: str, role_update: RoleUpdate):
    """更新角色信息"""
    logger.info(f"更新角色信息: role_id={role_id}, update_data={role_update.model_dump(exclude_unset=True)}")
    try:
        client = get_etcd_client()
        role_info_path = get_role_info_path(role_id)
        
        # 获取现有角色信息
        role_info_json, _ = client.get(role_info_path)
        if role_info_json is None:
            logger.warning(f"角色不存在: role_id={role_id}")
            raise HTTPException(status_code=404, detail=f"角色 '{role_id}' 不存在")
        
        # 解析现有信息
        role_info_dict = json.loads(role_info_json)
        existing_role = RoleInfo(**role_info_dict)
        
        # 更新字段
        update_dict = role_update.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(existing_role, key, value)
        
        if existing_role.default:
            set_default_role_id(client=client, role_id=role_id)
            logger.info(f"设置角色为默认: role_id={role_id}")
        
        # 更新时间
        existing_role.updated_at = datetime.now()
        
        # 保存更新
        client.put(role_info_path, existing_role.model_dump_json())
        
        logger.info(f"角色更新成功: role_id={role_id}, name={existing_role.name}")
        return existing_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新角色失败: role_id={role_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"更新角色失败: {str(e)}")


@router.delete("/{role_id}", summary="删除角色")
async def delete_role(role_id: str):
    """删除角色"""
    logger.info(f"删除角色: role_id={role_id}")
    try:
        client = get_etcd_client()
        role_info_path = get_role_info_path(role_id)
        
        # 检查角色是否存在
        role_info_json, _ = client.get(role_info_path)
        if role_info_json is None:
            logger.warning(f"角色不存在: role_id={role_id}")
            raise HTTPException(status_code=404, detail=f"角色 '{role_id}' 不存在")
        
        service_ids = get_service_by_role_id(client, role_id)
        if service_ids:
            logger.warning(f"角色正在被使用，无法删除: role_id={role_id}, service_ids={service_ids}")
            raise HTTPException(
                status_code=400, 
                detail=f"角色 '{role_id}' 正在被以下服务使用，无法删除: {', '.join(service_ids)}"
            )
            return
        # 删除角色信息和规则
        client.delete_prefix(f"{settings.etcd_config_prefix}roles/{role_id}/")
        
        logger.info(f"角色删除成功: role_id={role_id}")
        return {"message": f"角色 '{role_id}' 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除角色失败: role_id={role_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"删除角色失败: {str(e)}")


async def get_role_rules_with_inheritance(client, role_id: str) -> List[RuleInfo]:
    """获取角色的所有规则（包括继承的规则）"""
    try:
        # 获取角色信息
        role_info_path = get_role_info_path(role_id)
        role_info_json, _ = client.get(role_info_path)
        if role_info_json is None:
            raise HTTPException(status_code=404, detail=f"角色 '{role_id}' 不存在")
        
        role_info_dict = json.loads(role_info_json)
        role_info = RoleInfo(**role_info_dict)
        
        # 收集所有规则（包括继承的）
        all_rules = []
        processed_rules = set()
        
        # 递归获取父角色规则
        current_role_id = role_info.parent_role_id
        while current_role_id:
            parent_role_info_path = get_role_info_path(current_role_id)
            parent_role_json, _ = client.get(parent_role_info_path)
            if parent_role_json is None:
                break
                
            parent_role_dict = json.loads(parent_role_json)
            parent_role = RoleInfo(**parent_role_dict)
            
            # 获取父角色规则
            parent_rules = await get_role_rules_from_etcd(client, current_role_id)
            for rule in parent_rules:
                # 检查该规则是否已被子角色覆盖
                if rule.rule_id not in processed_rules:
                    all_rules.append(rule)
                    processed_rules.add(rule.rule_id)
            
            current_role_id = parent_role.parent_role_id
        
        # 添加当前角色规则
        current_rules = await get_role_rules_from_etcd(client, role_id)
        for rule in current_rules:
            all_rules.append(rule)
            processed_rules.add(rule.rule_id)
        
        return all_rules
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色规则失败: {str(e)}")


async def get_role_rules_from_etcd(client, role_id: str) -> List[RuleInfo]:
    """从ETCD获取角色的所有规则（不包含继承的规则）"""
    try:
        # 获取所有规则，过滤出当前角色的规则
        rules_path_prefix = f"{settings.etcd_config_prefix}rules/"
        rules = []
        
        for value, metadata in client.get_prefix(rules_path_prefix):
            # 跳过历史记录路径
            if b'/history/' in metadata.key:
                continue
            rule_info_dict = json.loads(value)
            rule = RuleInfo(**rule_info_dict)
            # 只返回当前角色的规则
            if rule.role_id == role_id:
                rules.append(rule)
        
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色规则失败: {str(e)}")


@router.get("/{role_id}/rules", response_model=RuleListResponse, summary="获取角色规则（包括继承的规则）")
async def get_role_rules(role_id: str):
    """获取角色的所有规则（包括继承的规则）"""
    try:
        client = get_etcd_client()
        rules = await get_role_rules_with_inheritance(client, role_id)
        return RuleListResponse(rules=rules, total=len(rules))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色规则失败: {str(e)}")


@router.get("/{role_id}/rules/effective", response_model=RuleListResponse, summary="获取角色生效的规则（去重后）")
async def get_role_effective_rules(role_id: str):
    """获取角色生效的规则（去重后，子角色规则覆盖父角色规则）"""
    try:
        client = get_etcd_client()
        rules = await get_role_rules_with_inheritance(client, role_id)
        
        # 去重：保留最新的规则（子角色的规则覆盖父角色的规则）
        # 由于我们已经按继承顺序收集规则，后面的规则会覆盖前面的
        unique_rules = []
        seen_rule_ids = set()
        
        for rule in rules:
            if rule.rule_id not in seen_rule_ids:
                unique_rules.append(rule)
                seen_rule_ids.add(rule.rule_id)
        
        return RuleListResponse(rules=unique_rules, total=len(unique_rules))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色生效规则失败: {str(e)}")


@router.get("/default", response_model=RoleInfo, summary="获取默认角色")
async def get_default_role_api():
    """获取当前默认角色的详细信息"""
    try:
        client = get_etcd_client()
        
        # 获取默认角色ID
        default_role_id = get_default_role_id(client)
        if default_role_id is None:
            raise HTTPException(status_code=404, detail="未设置默认角色")
        
        # 获取默认角色的详细信息
        role_info_path = get_role_info_path(default_role_id)
        role_info_json, _ = client.get(role_info_path)
        if role_info_json is None:
            raise HTTPException(status_code=404, detail=f"默认角色 '{default_role_id}' 不存在")
        
        # 解析角色信息
        role_info_dict = json.loads(role_info_json)
        
        return RoleInfo(**role_info_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取默认角色失败: {str(e)}")

