import re
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body
from backend.services import RegistryService, CollectorService, get_registry_service, get_collector_service
from backend.models import (
    ServiceInfo, ServiceHealth, RegistryStats, RegistryHealth,
    PaginatedServicesResponse,
    ModeInfo, RoleInfo
)
from backend.common.logger import logger
from backend.common.etcd_client import get_etcd_client
from .roles import is_role_exist, get_default_role_id, get_all_roles_from_etcd
from .modes import is_mode_exist, get_default_mode

router = APIRouter()
registry_service = get_registry_service()
collector_service = get_collector_service()

from backend.config import settings


def update_service_mode(service_id: str, mode: Optional[str]):
    """更新服务的模式属性，传入None表示触发watch更新"""
    client = get_etcd_client()
    service_mode_path = f"{settings.etcd_services_prefix}/{service_id}/mode".replace("//", "/") 
    
    # 获取现有属性
    current_mode_value, _ = client.get(service_mode_path)
    if current_mode_value:
        current_mode = current_mode_value.decode("utf-8")
    else:
        current_mode = None
    
    if mode is None:
        # 重写回去触发update，触发服务的watch进行模式更新
        client.put(service_mode_path, current_mode if current_mode else get_default_mode(client))
        return
    
    if mode == current_mode:
        return  # 模式未改变，无需更新
    else:
        if not is_mode_exist(client, mode):
            raise HTTPException(status_code=404, detail=f"模式 '{mode}' 不存在")
        client.put(service_mode_path, mode)


def update_service_role(service_id: str, role_id: Optional[str]):
    """更新服务的角色属性"""
    client = get_etcd_client()
    service_role_path = f"{settings.etcd_services_prefix}/{service_id}/role".replace("//", "/") 
    
    # 获取现有属性
    current_role_value, _ = client.get(service_role_path)
    if current_role_value:
        current_role = current_role_value.decode("utf-8")
    else:
        current_role = None
    
    if role_id is None:
        # 重写回去触发update，触发服务的watch进行模式更新
        client.put(service_role_path, current_role if current_role else get_default_role_id(client))
        return
    
    if role_id == current_role:
        return  # 模式未改变，无需更新
    else:
        if not is_role_exist(client, role_id):
            raise HTTPException(status_code=404, detail=f"角色 '{role_id}' 不存在")
        client.put(service_role_path, role_id)


# 排序允许的字段集合
_VALID_SORT_FIELDS = {
    "name", "host", "port", "version", "build_id",
    "build_time", "mode", "role", "status", "last_heartbeat",
}


def _parse_version(version_str: str):
    """解析版本字符串: 'v1.0.0 build123 2025/12/16 16:51:44' -> (ver, bid, btime)"""
    ver_str = (version_str or "").strip()
    m = re.match(r'^(\S+)\s+(\S+)\s+(.+)$', ver_str)
    if not m:
        return "", "", None
    ver = m.group(1)
    bid = m.group(2)
    btime_str = m.group(3).replace("CST", "").strip()
    try:
        btime = datetime.strptime(btime_str, "%Y/%m/%d %H:%M:%S")
    except ValueError:
        btime = None
    return ver, bid, btime


def _get_sort_key(service: ServiceInfo, sort_by: str, role_name_map: dict):
    """根据排序字段提取排序键"""
    if sort_by == "name":
        return (service.name or "").lower()
    if sort_by == "host":
        return (service.host or "").lower()
    if sort_by == "port":
        return service.port or 0
    if sort_by == "version":
        return _parse_version(service.version)[0]
    if sort_by == "build_id":
        return _parse_version(service.version)[1]
    if sort_by == "build_time":
        return _parse_version(service.version)[2] or datetime.min
    if sort_by == "mode":
        return (service.mode or "").lower()
    if sort_by == "role":
        return (role_name_map.get(service.role_id, "")).lower()
    if sort_by == "status":
        return service.status or ""
    if sort_by == "last_heartbeat":
        return service.last_heartbeat or datetime.min
    return ""


@router.get("", response_model=PaginatedServicesResponse)
async def list_services(
    healthy_only: bool = Query(False, description="仅显示健康服务"),
    unhealthy_only: bool = Query(False, description="仅显示不健康服务"),
    mode: Optional[str] = Query(None, description="按模式筛选"),
    role_id: Optional[str] = Query(None, description="按角色ID筛选"),
    search: Optional[str] = Query(None, description="模糊搜索：大小写不敏感，匹配服务名/主机地址/服务ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段: name/host/port/version/build_id/build_time/mode/role/status/last_heartbeat"),
    sort_order: Optional[str] = Query("asc", description="排序方向: asc/desc"),
):
    logger.info(f"获取服务列表: healthy_only={healthy_only}, unhealthy_only={unhealthy_only}, mode={mode}, role_id={role_id}, search={search}, page={page}, page_size={page_size}")
    try:
        # 不健康筛选时，需要从注册中心获取全部服务再在后端过滤
        services = await registry_service.get_services(healthy_only=healthy_only)
        logger.debug(f"从注册中心获取到 {len(services)} 个服务")
        
        # 应用不健康筛选：排除 healthy 状态的服务
        if unhealthy_only:
            services = [s for s in services if s.status != 'healthy']
            logger.debug(f"不健康筛选后剩余 {len(services)} 个服务")
        
        # 应用模式和角色筛选（属性已经合并到服务中）
        filtered_services = []
        for service in services:
            # 模式筛选
            if mode is not None:
                if service.mode != mode:
                    continue
            
            # 角色筛选
            if role_id is not None:
                if service.role_id != role_id:
                    continue
            
            filtered_services.append(service)
        
        # 搜索过滤（大小写不敏感，匹配服务名/主机地址/服务ID）
        if search and search.strip():
            search_lower = search.strip().lower()
            filtered_services = [
                s for s in filtered_services
                if search_lower in s.name.lower()
                or search_lower in s.host.lower()
                or search_lower in s.service_id.lower()
            ]
            logger.debug(f"搜索 '{search}' 后剩余 {len(filtered_services)} 个服务")
        
        total = len(filtered_services)
        logger.debug(f"筛选后剩余 {total} 个服务")

        # 应用排序
        if sort_by:
            if sort_by not in _VALID_SORT_FIELDS:
                raise HTTPException(
                    status_code=422,
                    detail=f"无效的排序字段 '{sort_by}'，有效值: {', '.join(sorted(_VALID_SORT_FIELDS))}",
                )
            role_name_map: dict = {}
            if sort_by == "role":
                client = get_etcd_client()
                roles = await get_all_roles_from_etcd(client)
                role_name_map = {r.role_id: r.name for r in roles}
            reverse = sort_order == "desc"
            filtered_services.sort(
                key=lambda s: _get_sort_key(s, sort_by, role_name_map),
                reverse=reverse,
            )
            logger.debug(f"排序: sort_by={sort_by}, sort_order={sort_order}")

        # 应用分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_services = filtered_services[start_idx:end_idx]
        
        logger.info(f"返回服务列表: 总数={total}, 当前页={len(paginated_services)}")
        return PaginatedServicesResponse(services=paginated_services, total=total)
    except Exception as e:
        logger.error(f"获取服务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")


@router.get("/count", response_model=int)
async def get_services_count(
    healthy_only: bool = Query(False, description="仅显示健康服务"),
    unhealthy_only: bool = Query(False, description="仅显示不健康服务"),
    mode: Optional[str] = Query(None, description="按模式筛选"),
    role_id: Optional[str] = Query(None, description="按角色ID筛选"),
    search: Optional[str] = Query(None, description="模糊搜索：大小写不敏感，匹配服务名/主机地址/服务ID")
):
    """获取服务总数"""
    logger.info(f"获取服务总数: healthy_only={healthy_only}, unhealthy_only={unhealthy_only}, mode={mode}, role_id={role_id}, search={search}")
    try:
        # registry_service.get_services 已经自动合并了ETCD中的属性
        services = await registry_service.get_services(healthy_only=healthy_only)
        logger.debug(f"从注册中心获取到 {len(services)} 个服务")
        
        # 应用不健康筛选：排除 healthy 状态的服务
        if unhealthy_only:
            services = [s for s in services if s.status != 'healthy']
            logger.debug(f"不健康筛选后剩余 {len(services)} 个服务")
        
        # 应用模式和角色筛选（属性已经合并到服务中）
        filtered_services = []
        for service in services:
            # 模式筛选
            if mode is not None:
                if service.mode != mode:
                    continue
            
            # 角色筛选
            if role_id is not None:
                if service.role_id != role_id:
                    continue
            
            filtered_services.append(service)
        
        # 搜索过滤（大小写不敏感，匹配服务名/主机地址/服务ID）
        if search and search.strip():
            search_lower = search.strip().lower()
            filtered_services = [
                s for s in filtered_services
                if search_lower in s.name.lower()
                or search_lower in s.host.lower()
                or search_lower in s.service_id.lower()
            ]
        
        count = len(filtered_services)
        logger.info(f"服务总数: {count}")
        return count
    except Exception as e:
        logger.error(f"获取服务总数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务总数失败: {str(e)}")


@router.get("/registry/health", response_model=RegistryHealth)
async def get_registry_health():
    logger.info("获取注册中心健康状态")
    try:
        health = await registry_service.get_registry_health()
        logger.debug(f"注册中心健康状态: {health}")
        return health
    except Exception as e:
        logger.error(f"获取注册中心健康状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取注册中心健康状态失败: {str(e)}")


@router.get("/registry/stats", response_model=RegistryStats)
async def get_registry_stats():
    logger.info("获取注册中心统计信息")
    try:
        stats = await registry_service.get_registry_stats()
        logger.debug(f"注册中心统计: total={stats.total_services}, healthy={stats.healthy_services}")
        return stats
    except Exception as e:
        logger.error(f"获取注册中心统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取注册中心统计信息失败: {str(e)}")


@router.get("/cluster/tags", summary="获取所有已发现的集群标签")
async def get_cluster_tags():
    """从注册中心获取所有已发现的集群标签"""
    logger.info("获取集群标签")
    try:
        tags = await registry_service.get_cluster_tags()
        logger.debug(f"获取集群标签成功: {tags}")
        return tags
    except Exception as e:
        logger.error(f"获取集群标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取集群标签失败: {str(e)}")


@router.get("/{service_id}", response_model=ServiceInfo)
async def get_service(service_id: str):
    logger.info(f"获取服务详情: service_id={service_id}")
    try:
        # registry_service.get_service 已经自动合并了ETCD中的属性
        service = await registry_service.get_service(service_id)
        if not service:
            logger.warning(f"服务不存在: service_id={service_id}")
            raise HTTPException(status_code=404, detail="服务不存在")
        
        logger.debug(f"获取服务详情成功: service_id={service_id}, name={service.name}, mode={service.mode}, role_id={service.role_id}")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务详情失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务详情失败: {str(e)}")


@router.get("/{service_id}/health", response_model=ServiceHealth)
async def get_service_health(service_id: str):
    logger.info(f"获取服务健康状态: service_id={service_id}")
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            logger.warning(f"服务不存在: service_id={service_id}")
            raise HTTPException(status_code=404, detail="服务不存在")
        
        collector_healthy = await collector_service.check_health(service.host, service.port)
        logger.debug(f"服务健康检查: service_id={service_id}, collector_healthy={collector_healthy}")
        
        return ServiceHealth(
            service_id=service.service_id,
            name=service.name,
            host=service.host,
            port=service.port,
            registry_healthy=collector_healthy,
            collector_healthy=collector_healthy,
            last_heartbeat=service.last_heartbeat,
            version=service.version,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务健康状态失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务健康状态失败: {str(e)}")


@router.delete("/{service_id}")
async def delete_service(service_id: str):
    logger.info(f"注销服务: service_id={service_id}")
    try:
        success = await registry_service.unregister_service(service_id)
        if not success:
            logger.warning(f"服务不存在，无法注销: service_id={service_id}")
            raise HTTPException(status_code=404, detail="服务不存在")
        logger.info(f"服务注销成功: service_id={service_id}")
        return {"message": "服务已注销", "service_id": service_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注销服务失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"注销服务失败: {str(e)}")


@router.put("/{service_id}/attributes", summary="更新服务属性（模式和角色）")
async def update_service_attributes(
    service_id: str,
    attributes: Dict[str, Any] = Body(..., description="要更新的属性")
):
    """更新服务的模式和角色属性"""
    logger.info(f"更新服务属性: service_id={service_id}, attributes={attributes}")
    try:
        # 获取现有服务信息
        service = await registry_service.get_service(service_id)
        if not service:
            logger.warning(f"服务不存在: service_id={service_id}")
            raise HTTPException(status_code=404, detail="服务不存在")
        
        # 验证和更新属性
        updated_attributes = {}
        
        # 获取ETCD客户端用于验证
        client = get_etcd_client()
        
        # 更新模式
        if "mode" in attributes:
            mode = attributes["mode"]
            if mode is not None:
                # 验证模式是否存在
                if not is_mode_exist(client, mode):
                    logger.warning(f"模式不存在: mode={mode}")
                    raise HTTPException(status_code=404, detail=f"模式 '{mode}' 不存在")
                update_service_mode(service_id, mode)  # 更新模式属性
                logger.info(f"服务模式已更新: service_id={service_id}, mode={mode}")
            else:
                update_service_mode(service_id, None)  # 传入None表示触发默认模式更新
                logger.info(f"服务模式已重置为默认: service_id={service_id}")
            updated_attributes["mode"] = mode
        
        # 更新角色
        if "role_id" in attributes:
            role_id = attributes["role_id"]
            if role_id is not None:
                # 验证角色是否存在
                if not await is_role_exist(client, role_id):
                    logger.warning(f"角色不存在: role_id={role_id}")
                    raise HTTPException(status_code=404, detail=f"角色 '{role_id}' 不存在")
                update_service_role(service_id, role_id)  # 更新角色属性
                logger.info(f"服务角色已更新: service_id={service_id}, role_id={role_id}")
            else:
                update_service_role(service_id, None)  # 传入None表示触发默认角色更新
                logger.info(f"服务角色已重置为默认: service_id={service_id}")
            updated_attributes["role_id"] = role_id
        
        logger.info(f"服务属性更新成功: service_id={service_id}, attributes={updated_attributes}")
        return {
            "message": "服务属性已更新",
            "service_id": service_id,
            "attributes": updated_attributes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新服务属性失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"更新服务属性失败: {str(e)}")
