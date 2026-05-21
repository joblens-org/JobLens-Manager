from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class JobOperation(BaseModel):
    opt: Literal["add", "remove"]
    type: Literal["job.condor", "job.common"]
    JobID: int
    JobPIDs: List[int]
    Lens: List[str]


class CondorJobOperation(BaseModel):
    opt: Literal["add"] = "add"
    type: Literal["job.condor"] = "job.condor"
    JobID: int
    JobPIDs: List[int]
    Lens: List[str]
    slot: str


class JobCreateRequest(BaseModel):
    service_id: str
    job_type: Literal["job.condor", "job.common"]
    job_id: int
    job_pids: List[int]
    lens: List[str]
    slot: Optional[str] = None


class JobInfo(BaseModel):
    JobID: int
    jobtype: str
    subtype: str
    # job_type: str
    JobPIDs: List[int]
    CollectorNames: List[str]
    # status: str
    # created_at: Optional[str] = None
    # updated_at: Optional[str] = None


class JobListResponse(BaseModel):
    service_id: str
    service_name: str
    jobs: List[JobInfo]


class JobCount(BaseModel):
    job_count: int
    status: str
    # active: int
    # completed: int
    # failed: int
