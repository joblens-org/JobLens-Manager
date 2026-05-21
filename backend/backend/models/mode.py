from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ModeInfo(BaseModel):
    """模式信息模型"""
    name: str = Field(..., description="模式名称（唯一标识）")
    description: Optional[str] = Field(None, description="模式描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    default: bool = Field(False, description="是否为默认模式")
    config_count: int = Field(0, description="关联的配置数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "develop",
                "description": "开发环境模式",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "default": True,
                "config_count": 1
            }
        }


class ModeCreate(BaseModel):
    """模式创建请求模型"""
    name: str = Field(..., description="模式名称（需唯一）")
    description: Optional[str] = Field(None, description="模式描述")
    default: Optional[bool] = Field(False, description="是否设置为默认模式")


class ModeUpdate(BaseModel):
    """模式更新请求模型"""
    description: Optional[str] = Field(None, description="模式描述")
    default: Optional[bool] = Field(None, description="是否设置为默认模式")


class ModeConfigUpdate(BaseModel):
    """模式配置更新模型（继承自原有的ConfigUpdate）"""
    raw_config: str = Field(..., description="YAML格式的配置内容")
    description: Optional[str] = Field("配置更新", description="更新描述")


class ModeListResponse(BaseModel):
    """模式列表响应模型"""
    modes: List[ModeInfo]
    total: int = Field(..., description="总模式数量")


# 保留原有的ConfigUpdate模型别名以便向后兼容
ConfigUpdate = ModeConfigUpdate