import asyncio
from fastapi import APIRouter, HTTPException, Query
from typing import List
from backend.services import RegistryService, CollectorService
from backend.models import CollectorPerf, WriterPerf, WriterInfo, ServiceMetrics, PrometheusMetrics
from backend.common.logger import logger

router = APIRouter()
registry_service = RegistryService()
collector_service = CollectorService()


@router.get("/services/{service_id}/collectors", response_model=List[CollectorPerf])
async def get_collector_performance(service_id: str):
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        return await collector_service.get_collector_perf(service.host, service.port)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取采集器性能失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取采集器性能失败: {str(e)}")


@router.get("/services/{service_id}/writers", response_model=List[WriterPerf])
async def get_writer_performance(service_id: str):
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        return await collector_service.get_writer_perf(service.host, service.port)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Writer性能失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取Writer性能失败: {str(e)}")


@router.get("/services/{service_id}/writers/{writer_name}", response_model=WriterInfo)
async def get_writer_info(service_id: str, writer_name: str):
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        writer_info = await collector_service.get_writer_info(service.host, service.port, writer_name)
        if not writer_info:
            raise HTTPException(status_code=404, detail="Writer不存在")
        
        return writer_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Writer信息失败: service_id={service_id}, writer_name={writer_name}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取Writer信息失败: {str(e)}")


@router.get("/services/{service_id}/all", response_model=ServiceMetrics)
async def get_all_metrics(service_id: str):
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        collectors, writers = await asyncio.gather(
            collector_service.get_collector_perf(service.host, service.port),
            collector_service.get_writer_perf(service.host, service.port),
            return_exceptions=True,
        )
        
        if isinstance(collectors, Exception):
            logger.warning(f"采集器指标获取失败: service_id={service_id}, host={service.host}, port={service.port}, error={str(collectors)}")
            collectors = []
        if isinstance(writers, Exception):
            logger.warning(f"Writer指标获取失败: service_id={service_id}, host={service.host}, port={service.port}, error={str(writers)}")
            writers = []
        
        return ServiceMetrics(
            service_id=service_id,
            service_name=service.name,
            collectors=collectors if isinstance(collectors, list) else [],
            writers=writers if isinstance(writers, list) else [],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务指标失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务指标失败: {str(e)}")


@router.get("/services/{service_id}/prometheus", response_model=PrometheusMetrics)
async def get_prometheus_metrics(service_id: str):
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        metrics_text = await collector_service.get_prometheus_metrics(service.host, service.port)
        return PrometheusMetrics(content=metrics_text)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Prometheus指标失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取Prometheus指标失败: {str(e)}")


@router.get("/registry")
async def get_registry_metrics():
    try:
        health = await registry_service.get_registry_health()
        stats = await registry_service.get_registry_stats()
        
        return {
            "registry_health": health,
            "registry_stats": stats,
        }
    except Exception as e:
        logger.error(f"获取注册中心指标失败: error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取注册中心指标失败: {str(e)}")
