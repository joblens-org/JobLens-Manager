from .registry_service import RegistryService
from .collector_service import CollectorService
from .lua_validator import LuaValidator, get_lua_validator, set_lua_validator, reset_lua_validator

__all__ = [
    "RegistryService", 
    "CollectorService",
    "LuaValidator",
    "get_registry_service", 
    "get_collector_service",
    "get_lua_validator",
    "set_lua_validator",
    "reset_lua_validator",
]

# 全局服务实例（支持测试时替换）
_registry_service_instance = None
_collector_service_instance = None


def get_registry_service() -> RegistryService:
    """获取RegistryService实例（支持测试时替换）"""
    global _registry_service_instance
    if _registry_service_instance is None:
        _registry_service_instance = RegistryService()
    return _registry_service_instance


def get_collector_service() -> CollectorService:
    """获取CollectorService实例（支持测试时替换）"""
    global _collector_service_instance
    if _collector_service_instance is None:
        _collector_service_instance = CollectorService()
    return _collector_service_instance


def set_registry_service(service: RegistryService) -> None:
    """设置RegistryService实例（用于测试）"""
    global _registry_service_instance
    _registry_service_instance = service


def set_collector_service(service: CollectorService) -> None:
    """设置CollectorService实例（用于测试）"""
    global _collector_service_instance
    _collector_service_instance = service


def reset_services() -> None:
    """重置服务实例（用于测试清理）"""
    global _registry_service_instance, _collector_service_instance
    _registry_service_instance = None
    _collector_service_instance = None
