from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class Environment(str, Enum):
    """环境枚举"""
    DEVELOP = "Develop"
    TEST = "Test"

class ConfigUpdate(BaseModel):
    """配置更新模型"""
    raw_config:str  # 配置内容
    description: Optional[str] = "配置更新"  # 更新描述

class VersionInfo(BaseModel):
    """版本信息模型"""
    version: int
    revision: int
    timestamp: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None