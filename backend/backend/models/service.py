from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field


class ServiceRegistration(BaseModel):
    host: str
    port: int
    name: str
    version: str


class ServiceInfo(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=False,
    )
    
    service_id: str = Field(alias="id")
    host: str
    port: int
    name: str
    version: str
    base_url: str
    status: str
    registered_at: datetime
    last_heartbeat: Optional[datetime] = None
    mode: Optional[str] = Field(None, description="关联的模式名称")
    role_id: Optional[str] = Field(None, description="关联的角色ID")
    metadata: Optional[dict] = None

    @computed_field
    @property
    def healthy(self) -> bool:
        return self.status == "healthy"


class ServiceHealth(BaseModel):
    service_id: str
    name: str
    host: str
    port: int
    registry_healthy: bool
    collector_healthy: bool
    last_heartbeat: Optional[datetime] = None
    version: Optional[str] = None


class RegistryStats(BaseModel):
    total_services: int
    status_distribution: Dict
    healthy_services: int
    unhealthy_services: int
    # active_services: int
    heartbeat_interval: float
    service_timeout: float
    timestamp: datetime


class PaginatedServicesResponse(BaseModel):
    services: List[ServiceInfo]
    total: int


class RegistryHealth(BaseModel):
    status: str
    details: Dict
