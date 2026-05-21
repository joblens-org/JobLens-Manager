import httpx
from typing import List, Optional
from backend.config import settings
from backend.models import ServiceInfo, RegistryStats, RegistryHealth
from backend.common.logger import logger
from backend.common.etcd_client import get_etcd_client


class RegistryService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.collector_timeout)
        self.base_url = settings.registry_url
        self.etcd_client = get_etcd_client()
        logger.info(f"注册中心服务初始化: base_url={self.base_url}, timeout={settings.collector_timeout}")

    def _load_service_attributes_single(self, service: ServiceInfo) -> None:
        """从ETCD加载单个服务的属性（回退方法）"""
        service_id = service.service_id
        service_mode_path = f"{settings.etcd_services_prefix}/{service_id}/mode".replace("//", "/")
        mode_value, _ = self.etcd_client.get(service_mode_path)
        if mode_value:
            service.mode = mode_value.decode("utf-8")
        service_role_path = f"{settings.etcd_services_prefix}/{service_id}/role".replace("//", "/")
        role_value, _ = self.etcd_client.get(service_role_path)
        if role_value:
            service.role_id = role_value.decode("utf-8")

    def _batch_load_service_attributes(self, services: List[ServiceInfo]) -> None:
        """批量从ETCD前缀读取所有服务的属性，替代逐服务调用"""
        if not services:
            return
        prefix = settings.etcd_services_prefix.rstrip("/") + "/"
        try:
            results = list(self.etcd_client.get_prefix(prefix))
        except Exception as e:
            logger.warning(f"批量加载ETCD属性失败，回退到逐服务加载: {str(e)}")
            for service in services:
                self._load_service_attributes_single(service)
            return

        mode_map = {}
        role_map = {}
        for value, meta in results:
            key = meta.key.decode("utf-8") if isinstance(meta.key, bytes) else meta.key
            # key 形如 /joblens_registry/services/{service_id}/mode
            # 提取 service_id 和 attribute 类型
            parts = key.rstrip("/").split("/")
            if len(parts) >= 3:
                attr_type = parts[-1]
                service_id = parts[-2]
                val = value.decode("utf-8")
                if attr_type == "mode":
                    mode_map[service_id] = val
                elif attr_type == "role":
                    role_map[service_id] = val

        for service in services:
            if service.service_id in mode_map:
                service.mode = mode_map[service.service_id]
            if service.service_id in role_map:
                service.role_id = role_map[service.service_id]

    async def get_services(self, healthy_only: bool = False) -> List[ServiceInfo]:
        logger.debug(f"获取服务列表: healthy_only={healthy_only}")
        try:
            params = {"healthy_only": str(healthy_only).lower()}
            response = await self.client.get(f"{self.base_url}/services", params=params)
            response.raise_for_status()
            data = response.json()
            services = [ServiceInfo(**service) for service in data]
            
            # 批量从ETCD加载属性
            self._batch_load_service_attributes(services)
            
            logger.debug(f"获取服务列表成功: 总数={len(services)}")
            return services
        except Exception as e:
            logger.error(f"获取服务列表失败: {str(e)}")
            raise

    async def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        logger.debug(f"获取服务详情: service_id={service_id}")
        try:
            response = await self.client.get(f"{self.base_url}/services/{service_id}")
            if response.status_code == 404:
                logger.debug(f"服务不存在: service_id={service_id}")
                return None
            response.raise_for_status()
            service = ServiceInfo(**response.json())
            
            # 从ETCD加载属性
            self._load_service_attributes_single(service)
            
            logger.debug(f"获取服务详情成功: service_id={service_id}, name={service.name}, mode={service.mode}, role_id={service.role_id}")
            return service
        except Exception as e:
            logger.error(f"获取服务详情失败: service_id={service_id}, error={str(e)}")
            raise

    async def unregister_service(self, service_id: str) -> bool:
        logger.info(f"注销服务: service_id={service_id}")
        try:
            response = await self.client.delete(f"{self.base_url}/unregister/{service_id}")
            if response.status_code == 404:
                logger.warning(f"服务不存在，无法注销: service_id={service_id}")
                return False
            response.raise_for_status()
            logger.info(f"服务注销成功: service_id={service_id}")
            return True
        except Exception as e:
            logger.error(f"注销服务失败: service_id={service_id}, error={str(e)}")
            raise

    async def get_registry_health(self) -> RegistryHealth:
        logger.debug("获取注册中心健康状态")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            health = RegistryHealth(**response.json())
            logger.debug(f"注册中心健康状态: {health}")
            return health
        except Exception as e:
            logger.error(f"获取注册中心健康状态失败: {str(e)}")
            raise

    async def get_registry_stats(self) -> RegistryStats:
        logger.debug("获取注册中心统计信息")
        try:
            response = await self.client.get(f"{self.base_url}/stats")
            response.raise_for_status()
            data = response.json()
            data['healthy_services'] = data['status_distribution'].get('healthy', 0)
            data['unhealthy_services'] = data['total_services'] - data['healthy_services']
            stats = RegistryStats(**data)
            logger.debug(f"注册中心统计: total={stats.total_services}, healthy={stats.healthy_services}")
            return stats
        except Exception as e:
            logger.error(f"获取注册中心统计信息失败: {str(e)}")
            raise

    async def get_cluster_tags(self) -> List[str]:
        """从注册中心获取所有已发现的集群标签"""
        logger.debug("获取集群标签")
        try:
            response = await self.client.get(f"{self.base_url}/cluster/tags")
            response.raise_for_status()
            data = response.json()
            tags = data.get("tags", [])
            logger.debug(f"获取集群标签成功: {tags}")
            return tags
        except Exception as e:
            logger.error(f"获取集群标签失败: {str(e)}")
            raise

    async def close(self):
        logger.debug("关闭注册中心客户端")
        await self.client.aclose()
