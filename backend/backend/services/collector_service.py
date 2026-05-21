import httpx
from typing import List, Optional
from backend.config import settings
from backend.models import (
    JobOperation,
    CondorJobOperation,
    JobInfo,
    JobCount,
    CollectorPerf,
    WriterPerf,
    WriterInfo,
)
from backend.common.logger import logger
import json


class CollectorService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.collector_timeout)
        logger.info(f"采集器服务初始化: timeout={settings.collector_timeout}")

    def _get_base_url(self, host: str, port: int) -> str:
        return f"http://{host}:{port}"

    async def get_jobs(self, host: str, port: int) -> List[JobInfo]:
        logger.debug(f"获取作业列表: host={host}, port={port}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/joblens/jobs")
            response.raise_for_status()
            data = response.json()
            jobs = [JobInfo(**job) for job in data['jobs']]
            logger.debug(f"获取作业列表成功: host={host}, port={port}, 总数={len(jobs)}")
            return jobs
        except Exception as e:
            logger.error(f"获取作业列表失败: host={host}, port={port}, error={str(e)}")
            raise

    async def get_job(self, host: str, port: int, job_id: str) -> Optional[JobInfo]:
        logger.debug(f"获取作业详情: host={host}, port={port}, job_id={job_id}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/joblens/jobs/{job_id}")
            if response.status_code == 404:
                logger.debug(f"作业不存在: host={host}, port={port}, job_id={job_id}")
                return None
            response.raise_for_status()
            job = JobInfo(**response.json())
            logger.debug(f"获取作业详情成功: host={host}, port={port}, job_id={job_id}")
            return job
        except Exception as e:
            logger.error(f"获取作业详情失败: host={host}, port={port}, job_id={job_id}, error={str(e)}")
            raise

    async def add_job(
        self,
        host: str,
        port: int,
        job_type: str,
        job_id: int,
        job_pids: List[int],
        lens: List[str],
        slot: Optional[str] = None,
    ) -> bool:
        logger.info(f"添加作业: host={host}, port={port}, job_type={job_type}, job_id={job_id}")
        try:
            base_url = self._get_base_url(host, port)
            
            if job_type == "job.condor":
                operation = CondorJobOperation(
                    JobID=job_id,
                    JobPIDs=job_pids,
                    Lens=lens,
                    slot=slot or "slot1",
                )
                response = await self.client.post(
                    f"{base_url}/joblens/condor_job",
                    json=operation.model_dump(),
                )
            else:
                operation = JobOperation(
                    opt="add",
                    type=job_type,
                    JobID=job_id,
                    JobPIDs=job_pids,
                    Lens=lens,
                )
                response = await self.client.post(
                    f"{base_url}/joblens/job",
                    json=operation.model_dump(),
                )
            
            response.raise_for_status()
            logger.info(f"添加作业成功: host={host}, port={port}, job_id={job_id}")
            return True
        except Exception as e:
            logger.error(f"添加作业失败: host={host}, port={port}, job_id={job_id}, error={str(e)}")
            raise

    async def remove_job(
        self,
        host: str,
        port: int,
        job_type: str,
        job_id: int,
    ) -> bool:
        logger.info(f"移除作业: host={host}, port={port}, job_type={job_type}, job_id={job_id}")
        try:
            base_url = self._get_base_url(host, port)
            operation = JobOperation(
                opt="remove",
                type=job_type,
                JobID=job_id,
                JobPIDs=[],
                Lens=[],
            )
            response = await self.client.post(
                f"{base_url}/joblens/job",
                json=operation.model_dump(),
            )
            response.raise_for_status()
            logger.info(f"移除作业成功: host={host}, port={port}, job_id={job_id}")
            return True
        except Exception as e:
            logger.error(f"移除作业失败: host={host}, port={port}, job_id={job_id}, error={str(e)}")
            raise

    async def get_collector_perf(self, host: str, port: int) -> List[CollectorPerf]:
        logger.debug(f"获取采集器性能: host={host}, port={port}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/joblens/collectors/perf")
            response.raise_for_status()
            data = response.json()
            if data['status'] != 'ok':
                raise ValueError(f"采集器性能数据状态异常: {data['status']}")
            perf_list = [CollectorPerf(**perf) for perf in data['collectors_perf']]
            logger.debug(f"获取采集器性能成功: host={host}, port={port}, 数量={len(perf_list)}")
            return perf_list
        except Exception as e:
            logger.error(f"获取采集器性能失败: host={host}, port={port}, error={str(e)}")
            raise

    async def get_writer_perf(self, host: str, port: int) -> List[WriterPerf]:
        logger.debug(f"获取Writer性能: host={host}, port={port}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/joblens/writers/perf")
            response.raise_for_status()
            data = response.json()
            if data['status'] != 'ok':
                raise ValueError(f"Writer性能数据状态异常: {data['status']}")
            perf_list = [WriterPerf(**perf) for perf in data['writers_perf']]
            logger.debug(f"获取Writer性能成功: host={host}, port={port}, 数量={len(perf_list)}")
            return perf_list
        except Exception as e:
            logger.error(f"获取Writer性能失败: host={host}, port={port}, error={str(e)}")
            raise

    async def get_writer_info(self, host: str, port: int, writer_name: str) -> Optional[WriterInfo]:
        logger.debug(f"获取Writer信息: host={host}, port={port}, writer_name={writer_name}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/joblens/writers/{writer_name}/info")
            if response.status_code == 404:
                logger.debug(f"Writer不存在: host={host}, port={port}, writer_name={writer_name}")
                return None
            response.raise_for_status()
            writer_info = WriterInfo(**response.json())
            logger.debug(f"获取Writer信息成功: host={host}, port={port}, writer_name={writer_name}")
            return writer_info
        except Exception as e:
            logger.error(f"获取Writer信息失败: host={host}, port={port}, writer_name={writer_name}, error={str(e)}")
            raise

    async def get_job_count(self, host: str, port: int) -> JobCount:
        logger.debug(f"获取作业数量: host={host}, port={port}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/joblens/jobs/count")
            response.raise_for_status()
            job_count = JobCount(**response.json())
            logger.debug(f"获取作业数量成功: host={host}, port={port}, count={job_count.job_count}")
            return job_count
        except Exception as e:
            logger.error(f"获取作业数量失败: host={host}, port={port}, error={str(e)}")
            raise

    async def check_health(self, host: str, port: int) -> bool:
        logger.debug(f"检查采集器健康状态: host={host}, port={port}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/joblens/healthy")
            res_j = json.loads(response.content)
            healthy = res_j['healthy']
            logger.debug(f"采集器健康状态: host={host}, port={port}, healthy={healthy}")
            return healthy
        except Exception as e:
            logger.warning(f"检查采集器健康状态失败: host={host}, port={port}, error={str(e)}")
            return False

    async def get_prometheus_metrics(self, host: str, port: int) -> str:
        logger.debug(f"获取Prometheus指标: host={host}, port={port}")
        try:
            base_url = self._get_base_url(host, port)
            response = await self.client.get(f"{base_url}/metrics")
            response.raise_for_status()
            metrics = response.text
            logger.debug(f"获取Prometheus指标成功: host={host}, port={port}, 长度={len(metrics)}")
            return metrics
        except Exception as e:
            logger.error(f"获取Prometheus指标失败: host={host}, port={port}, error={str(e)}")
            raise

    async def close(self):
        logger.debug("关闭采集器客户端")
        await self.client.aclose()
