from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class RuleInfo(BaseModel):
    """规则信息模型"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="规则ID（UUID）")
    role_id: str = Field(..., description="所属角色ID（UUID）")
    name: str = Field(..., description="规则名称")
    lua_content: str = Field(..., description="Lua规则内容")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    version: int = Field(1, description="版本号")
    metadata: Optional[Dict[str, Any]] = Field(None, description="规则元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "550e8400-e29b-41d4-a716-446655440000",
                "role_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "数据验证规则",
                "lua_content": "function validate(data) return true end",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "version": 1,
                "metadata": {"category": "validation"}
            }
        }


class RoleInfo(BaseModel):
    """角色信息模型"""
    role_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="角色ID（UUID）")
    name: str = Field(..., description="角色名称（需唯一）")
    description: Optional[str] = Field(None, description="角色描述")
    parent_role_id: Optional[str] = Field(None, description="父角色ID（用于继承）")
    rule_ids: List[str] = Field(default_factory=list, description="关联的规则ID列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    service_count: int = Field(0, description="使用此角色的服务数量")
    default: bool = Field(False, description="是否为默认角色")
    metadata: Optional[Dict[str, Any]] = Field(None, description="角色元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "basic-user",
                "description": "基础用户角色",
                "parent_role_id": None,
                "rule_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "service_count": 5,
                "default": False,
                "metadata": {"permissions": ["read"]}
            }
        }


class RoleCreate(BaseModel):
    """角色创建请求模型"""
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    parent_role_id: Optional[str] = Field(None, description="父角色ID")
    rule_ids: Optional[List[str]] = Field(None, description="初始规则ID列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="角色元数据")


class RoleUpdate(BaseModel):
    """角色更新请求模型"""
    description: Optional[str] = Field(None, description="角色描述")
    default: Optional[bool] = Field(None, description="是否设置为默认角色")
    metadata: Optional[Dict[str, Any]] = Field(None, description="角色元数据")


class RuleCreate(BaseModel):
    """规则创建请求模型"""
    role_id: str = Field(..., description="所属角色ID（UUID）")
    name: str = Field(..., description="规则名称")
    lua_content: str = Field(..., description="Lua规则内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="规则元数据")


class RuleUpdate(BaseModel):
    """规则更新请求模型"""
    name: Optional[str] = Field(None, description="规则名称")
    lua_content: Optional[str] = Field(None, description="Lua规则内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="规则元数据")


class RoleWithRules(RoleInfo):
    """包含规则详情的角色信息"""
    rules: List[RuleInfo] = Field(default_factory=list, description="规则详情列表")


class RoleListResponse(BaseModel):
    """角色列表响应模型"""
    roles: List[RoleInfo]
    total: int = Field(..., description="总角色数量")


class RuleListResponse(BaseModel):
    """规则列表响应模型"""
    rules: List[RuleInfo]
    total: int = Field(..., description="总规则数量")