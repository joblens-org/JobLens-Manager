import asyncio
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime
from ..common.logger import logger
from backend.common.etcd_client import get_etcd_client

from backend.models import (
    RuleInfo, RuleCreate, RuleUpdate, RuleListResponse
)
from backend.config import settings
from backend.services import get_lua_validator

router = APIRouter(tags=["rules"])


def get_rule_path(rule_id: str) -> str:
    """获取规则存储路径（扁平化存储）"""
    return f"{settings.etcd_config_prefix}rules/{rule_id}"


def get_rule_history_path(rule_id: str, version: str) -> str:
    """获取规则历史路径"""
    return f"{settings.etcd_config_prefix}rules/{rule_id}/history/{version}"


async def is_role_exist(client, role_id: str) -> bool:
    """检查角色是否存在"""
    role_info_path = f"{settings.etcd_config_prefix}roles/{role_id}/info"
    role_info_json, _ = client.get(role_info_path)
    return role_info_json is not None


@router.get("/", response_model=RuleListResponse, summary="获取所有规则列表")
async def get_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取所有规则列表（支持分页）"""
    try:
        client = get_etcd_client()
        rules_path_prefix = f"{settings.etcd_config_prefix}rules/"
        
        all_rules = []
        for value, metadata in client.get_prefix(rules_path_prefix):
            # 跳过历史记录路径
            if b'/history/' in metadata.key:
                continue
            rule_info_dict = json.loads(value)
            all_rules.append(RuleInfo(**rule_info_dict))
        
        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_rules = all_rules[start_idx:end_idx]
        
        return RuleListResponse(rules=paginated_rules, total=len(all_rules))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取规则列表失败: {str(e)}")


@router.post("/", response_model=RuleInfo, summary="创建规则")
async def create_rule(rule_create: RuleCreate):
    """创建新规则"""
    try:
        client = get_etcd_client()
        
        # 检查角色是否存在
        if not await is_role_exist(client, rule_create.role_id):
            raise HTTPException(status_code=404, detail=f"角色 '{rule_create.role_id}' 不存在")
        
        # 验证Lua规则
        validator = get_lua_validator()
        try:
            rule_structure = validator.validate_rule(rule_create.lua_content)
            logger.info(f"规则验证成功: {rule_structure.get('name', 'unknown')}")
        except HTTPException as e:
            logger.error(f"规则验证失败: {e.detail}")
            raise
        
        # 创建规则信息
        rule_info = RuleInfo(
            rule_id=str(uuid.uuid4()),
            role_id=rule_create.role_id,
            name=rule_create.name,
            lua_content=rule_create.lua_content,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
            metadata=rule_create.metadata
        )
        
        # 保存规则到ETCD（扁平化存储）
        rule_path = get_rule_path(rule_info.rule_id)
        client.put(rule_path, rule_info.model_dump_json())
        
        # 更新角色的规则ID列表
        role_info_path = f"{settings.etcd_config_prefix}roles/{rule_create.role_id}/info"
        role_info_json, _ = client.get(role_info_path)
        if role_info_json:
            role_info_dict = json.loads(role_info_json)
            from backend.models import RoleInfo
            role_info = RoleInfo(**role_info_dict)
            role_info.rule_ids.append(rule_info.rule_id)
            role_info.updated_at = datetime.now()
            client.put(role_info_path, role_info.model_dump_json())
        
        return rule_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建规则失败: {str(e)}")


@router.get("/{rule_id}", response_model=RuleInfo, summary="获取规则详情")
async def get_rule(rule_id: str):
    """获取规则详情"""
    try:
        client = get_etcd_client()
        rule_path = get_rule_path(rule_id)
        
        rule_info_json, _ = client.get(rule_path)
        if rule_info_json is None:
            raise HTTPException(status_code=404, detail=f"规则 '{rule_id}' 不存在")
        
        rule_info_dict = json.loads(rule_info_json)
        return RuleInfo(**rule_info_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取规则详情失败: {str(e)}")


@router.put("/{rule_id}", response_model=RuleInfo, summary="更新规则")
async def update_rule(rule_id: str, rule_update: RuleUpdate):
    """更新规则信息（采用删除然后创建新rule的方法，触发watch机制）"""
    try:
        client = get_etcd_client()
        rule_path = get_rule_path(rule_id)
        
        # 获取现有规则信息
        rule_info_json, _ = client.get(rule_path)
        if rule_info_json is None:
            raise HTTPException(status_code=404, detail=f"规则 '{rule_id}' 不存在")
        
        # 解析现有信息
        rule_info_dict = json.loads(rule_info_json)
        existing_rule = RuleInfo(**rule_info_dict)
        role_id = existing_rule.role_id
        
        # 验证Lua规则（如果提供了新的lua_content）
        if rule_update.lua_content:
            validator = get_lua_validator()
            try:
                rule_structure = validator.validate_rule(rule_update.lua_content)
                logger.info(f"规则验证成功: {rule_structure.get('name', 'unknown')}")
            except HTTPException as e:
                logger.error(f"规则验证失败: {e.detail}")
                raise
        
        # 1. 删除旧规则
        client.delete(rule_path)
        
        # 2. 创建新规则（使用新的rule_id）
        new_rule_id = str(uuid.uuid4())
        new_rule_info = RuleInfo(
            rule_id=new_rule_id,
            role_id=existing_rule.role_id,
            name=rule_update.name if rule_update.name else existing_rule.name,
            lua_content=rule_update.lua_content if rule_update.lua_content else existing_rule.lua_content,
            created_at=existing_rule.created_at,  # 保留创建时间
            updated_at=datetime.now(),
            version=existing_rule.version + 1,
            metadata=rule_update.metadata if rule_update.metadata else existing_rule.metadata
        )
        
        # 保存新规则
        new_rule_path = get_rule_path(new_rule_id)
        client.put(new_rule_path, new_rule_info.model_dump_json())
        
        # 3. 更新角色rule_ids列表
        role_info_path = f"{settings.etcd_config_prefix}roles/{role_id}/info"
        role_info_json, _ = client.get(role_info_path)
        if role_info_json:
            from backend.models import RoleInfo
            role_info_dict = json.loads(role_info_json)
            role_info = RoleInfo(**role_info_dict)
            
            # 移除旧规则ID
            if rule_id in role_info.rule_ids:
                role_info.rule_ids.remove(rule_id)
            
            # 添加新规则ID
            role_info.rule_ids.append(new_rule_id)
            
            # 4. 更新角色updated_at时间戳（触发watch机制）
            role_info.updated_at = datetime.now()
            
            # 保存角色信息
            client.put(role_info_path, role_info.model_dump_json())
        
        return new_rule_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新规则失败: {str(e)}")


@router.delete("/{rule_id}", summary="删除规则")
async def delete_rule(rule_id: str):
    """删除规则"""
    try:
        client = get_etcd_client()
        rule_path = get_rule_path(rule_id)
        
        # 获取规则信息
        rule_info_json, _ = client.get(rule_path)
        if rule_info_json is None:
            raise HTTPException(status_code=404, detail=f"规则 '{rule_id}' 不存在")
        
        rule_info_dict = json.loads(rule_info_json)
        rule_info = RuleInfo(**rule_info_dict)
        role_id = rule_info.role_id
        
        # 删除规则
        client.delete(rule_path)
        
        # 从角色的规则ID列表中移除
        role_info_path = f"{settings.etcd_config_prefix}roles/{role_id}/info"
        role_info_json, _ = client.get(role_info_path)
        if role_info_json:
            from backend.models import RoleInfo
            role_info_dict = json.loads(role_info_json)
            role_info = RoleInfo(**role_info_dict)
            if rule_id in role_info.rule_ids:
                role_info.rule_ids.remove(rule_id)
                role_info.updated_at = datetime.now()
                client.put(role_info_path, role_info.model_dump_json())
        
        return {"message": f"规则 '{rule_id}' 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除规则失败: {str(e)}")