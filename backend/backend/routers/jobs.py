import asyncio
from fastapi import APIRouter, HTTPException, Query
from typing import List
from backend.services import RegistryService, CollectorService
from backend.models import JobCreateRequest, JobInfo, JobListResponse, JobCount
from backend.common.logger import logger

router = APIRouter()
registry_service = RegistryService()
collector_service = CollectorService()


@router.get("", response_model=List[JobListResponse])
async def list_all_jobs(
    service_ids: str = Query(None, description="服务ID列表，用逗号分隔"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    logger.info(f"获取作业列表: service_ids={service_ids}, page={page}, page_size={page_size}")
    try:
        # 解析服务ID列表
        selected_service_ids = None
        if service_ids:
            selected_service_ids = [sid.strip() for sid in service_ids.split(",")]
        
        # 获取所有服务或筛选指定服务
        all_services = await registry_service.get_services()
        if selected_service_ids:
            services = [s for s in all_services if s.service_id in selected_service_ids]
        else:
            services = all_services
        
        # 如果没有指定服务ID且服务数量很多，返回空列表（避免性能问题）
        if not selected_service_ids and len(services) > 10:
            logger.info(f"服务数量过多({len(services)}>10)且未指定service_ids，返回空列表")
            return []
        
        # 并发获取作业数据
        tasks = []
        for service in services:
            task = collector_service.get_jobs(service.host, service.port)
            tasks.append((service, task))
        
        results = []
        for service, task in tasks:
            try:
                jobs = await task
                if jobs:
                    results.append(JobListResponse(
                        service_id=service.service_id,
                        service_name=service.name,
                        jobs=jobs
                    ))
            except Exception as e:
                logger.warning(f"从服务获取作业失败: service_id={service.service_id}, host={service.host}, port={service.port}, error={str(e)}")
                continue
        
        # 如果没有指定服务ID，返回前10个服务的作业（避免性能问题）
        if not selected_service_ids:
            results = results[:10]
        
        logger.info(f"返回作业列表: 服务数={len(results)}")
        return results
    except Exception as e:
        logger.error(f"获取作业列表失败: error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取作业列表失败: {str(e)}")


@router.get("/{job_id}", response_model=JobInfo)
async def get_job(job_id: str, service_id: str = Query(..., description="服务ID")):
    logger.info(f"获取作业详情: job_id={job_id}, service_id={service_id}")
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        job = await collector_service.get_job(service.host, service.port, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="作业不存在")
        
        logger.info(f"获取作业详情成功: job_id={job_id}, service_id={service_id}")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业详情失败: job_id={job_id}, service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取作业详情失败: {str(e)}")


@router.post("", response_model=JobInfo)
async def create_job(job_request: JobCreateRequest):
    logger.info(f"创建作业: service_id={job_request.service_id}, job_id={job_request.job_id}, job_type={job_request.job_type}")
    try:
        service = await registry_service.get_service(job_request.service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        if job_request.job_type == "job.condor" and not job_request.slot:
            raise HTTPException(status_code=400, detail="Condor作业需要指定slot")
        
        await collector_service.add_job(
            host=service.host,
            port=service.port,
            job_type=job_request.job_type,
            job_id=job_request.job_id,
            job_pids=job_request.job_pids,
            lens=job_request.lens,
            slot=job_request.slot,
        )
        
        job = await collector_service.get_job(service.host, service.port, str(job_request.job_id))
        if not job:
            raise HTTPException(status_code=500, detail="作业创建成功但查询失败")
        
        logger.info(f"创建作业成功: service_id={job_request.service_id}, job_id={job_request.job_id}")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建作业失败: service_id={job_request.service_id}, job_id={job_request.job_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"创建作业失败: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(job_id: str, service_id: str = Query(..., description="服务ID"), job_type: str = Query(..., description="作业类型")):
    logger.info(f"删除作业: job_id={job_id}, service_id={service_id}, job_type={job_type}")
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        await collector_service.remove_job(
            host=service.host,
            port=service.port,
            job_type=job_type,
            job_id=int(job_id),
        )
        
        logger.info(f"删除作业成功: job_id={job_id}, service_id={service_id}")
        return {"message": "作业已删除", "job_id": job_id, "service_id": service_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除作业失败: job_id={job_id}, service_id={service_id}, job_type={job_type}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"删除作业失败: {str(e)}")


@router.get("/{service_id}/count", response_model=JobCount)
async def get_job_count(service_id: str):
    logger.info(f"获取作业数量: service_id={service_id}")
    try:
        service = await registry_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        result = await collector_service.get_job_count(service.host, service.port)
        logger.info(f"获取作业数量成功: service_id={service_id}, count={result.job_count}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业数量失败: service_id={service_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取作业数量失败: {str(e)}")
