from typing import Dict, List, Optional
from pydantic import BaseModel


class CollectorPerf(BaseModel):
    name: str
    # type: str
    call_cnt: int
    err_cnt: int
    max_us: float
    mean_us: float
    min_us: float
    variance: float
    # metrics_collected: int
    # avg_collection_time: float
    # errors: int
    # last_error: Optional[str] = None


class WriterPerf(BaseModel):
    name: str
    call_cnt: int
    err_cnt: int
    max_us: float
    mean_us: float
    min_us: float
    variance: float
    # metrics_written: int
    # avg_write_time: float
    # buffer_size: int
    # errors: int


class WriterInfo(BaseModel):
    name: str
    type: str
    config: Dict
    status: str
    metrics_written: int


class ServiceMetrics(BaseModel):
    service_id: str
    service_name: str
    collectors: List[CollectorPerf]
    writers: List[WriterPerf]


class PrometheusMetrics(BaseModel):
    content: str
