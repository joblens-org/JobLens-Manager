"""Job模型的单元测试"""
import pytest
from backend.models.job import (
    JobOperation,
    CondorJobOperation,
    JobCreateRequest,
    JobInfo,
    JobListResponse,
    JobCount
)


class TestJobOperation:
    """JobOperation模型测试"""
    
    def test_create_job_operation_add(self):
        """测试创建添加作业操作"""
        operation = JobOperation(
            opt="add",
            type="job.common",
            JobID=123,
            JobPIDs=[1001, 1002],
            Lens=["lens1", "lens2"]
        )
        assert operation.opt == "add"
        assert operation.type == "job.common"
        assert operation.JobID == 123
        assert operation.JobPIDs == [1001, 1002]
        assert operation.Lens == ["lens1", "lens2"]
    
    def test_create_job_operation_remove(self):
        """测试创建移除作业操作"""
        operation = JobOperation(
            opt="remove",
            type="job.condor",
            JobID=456,
            JobPIDs=[2001],
            Lens=["lens3"]
        )
        assert operation.opt == "remove"
        assert operation.type == "job.condor"
        assert operation.JobID == 456
        assert operation.JobPIDs == [2001]
        assert operation.Lens == ["lens3"]
    
    def test_job_operation_validation(self):
        """测试JobOperation验证"""
        # 无效的opt值
        with pytest.raises(ValueError):
            JobOperation(
                opt="invalid",  # 无效值
                type="job.common",
                JobID=123,
                JobPIDs=[1001],
                Lens=["lens1"]
            )
        
        # 无效的type值
        with pytest.raises(ValueError):
            JobOperation(
                opt="add",
                type="invalid",  # 无效值
                JobID=123,
                JobPIDs=[1001],
                Lens=["lens1"]
            )


class TestCondorJobOperation:
    """CondorJobOperation模型测试"""
    
    def test_create_condor_job_operation(self):
        """测试创建Condor作业操作"""
        operation = CondorJobOperation(
            JobID=789,
            JobPIDs=[3001, 3002, 3003],
            Lens=["condor-lens1", "condor-lens2"],
            slot="slot-1"
        )
        assert operation.opt == "add"  # 默认值
        assert operation.type == "job.condor"  # 默认值
        assert operation.JobID == 789
        assert operation.JobPIDs == [3001, 3002, 3003]
        assert operation.Lens == ["condor-lens1", "condor-lens2"]
        assert operation.slot == "slot-1"
    
    def test_condor_job_operation_defaults(self):
        """测试CondorJobOperation默认值"""
        operation = CondorJobOperation(
            JobID=789,
            JobPIDs=[3001],
            Lens=["lens1"]
        )
        assert operation.opt == "add"
        assert operation.type == "job.condor"
        assert operation.slot is None


class TestJobCreateRequest:
    """JobCreateRequest模型测试"""
    
    def test_create_job_create_request_condor(self):
        """测试创建Condor作业请求"""
        request = JobCreateRequest(
            service_id="service-123",
            job_type="job.condor",
            job_id=999,
            job_pids=[4001, 4002],
            lens=["request-lens1"],
            slot="slot-2"
        )
        assert request.service_id == "service-123"
        assert request.job_type == "job.condor"
        assert request.job_id == 999
        assert request.job_pids == [4001, 4002]
        assert request.lens == ["request-lens1"]
        assert request.slot == "slot-2"
    
    def test_create_job_create_request_common(self):
        """测试创建普通作业请求"""
        request = JobCreateRequest(
            service_id="service-456",
            job_type="job.common",
            job_id=888,
            job_pids=[5001],
            lens=["common-lens"]
        )
        assert request.service_id == "service-456"
        assert request.job_type == "job.common"
        assert request.job_id == 888
        assert request.job_pids == [5001]
        assert request.lens == ["common-lens"]
        assert request.slot is None
    
    def test_job_create_request_validation(self):
        """测试JobCreateRequest验证"""
        # 无效的job_type值
        with pytest.raises(ValueError):
            JobCreateRequest(
                service_id="service-123",
                job_type="invalid",
                job_id=123,
                job_pids=[1001],
                lens=["lens1"]
            )


class TestJobInfo:
    """JobInfo模型测试"""
    
    def test_create_job_info(self):
        """测试创建JobInfo"""
        job_info = JobInfo(
            JobID=111,
            jobtype="condor",
            subtype="batch",
            JobPIDs=[6001, 6002],
            CollectorNames=["collector1", "collector2"]
        )
        assert job_info.JobID == 111
        assert job_info.jobtype == "condor"
        assert job_info.subtype == "batch"
        assert job_info.JobPIDs == [6001, 6002]
        assert job_info.CollectorNames == ["collector1", "collector2"]


class TestJobListResponse:
    """JobListResponse模型测试"""
    
    def test_create_job_list_response(self):
        """测试创建JobListResponse"""
        jobs = [
            JobInfo(
                JobID=1,
                jobtype="condor",
                subtype="batch",
                JobPIDs=[1001],
                CollectorNames=["collector1"]
            ),
            JobInfo(
                JobID=2,
                jobtype="common",
                subtype="interactive",
                JobPIDs=[2001],
                CollectorNames=["collector2"]
            )
        ]
        response = JobListResponse(
            service_id="service-123",
            service_name="测试服务",
            jobs=jobs
        )
        assert response.service_id == "service-123"
        assert response.service_name == "测试服务"
        assert len(response.jobs) == 2
        assert response.jobs[0].JobID == 1
        assert response.jobs[1].JobID == 2
    
    def test_job_list_response_empty_jobs(self):
        """测试空作业列表的JobListResponse"""
        response = JobListResponse(
            service_id="service-456",
            service_name="空服务",
            jobs=[]
        )
        assert response.service_id == "service-456"
        assert response.service_name == "空服务"
        assert len(response.jobs) == 0


class TestJobCount:
    """JobCount模型测试"""
    
    def test_create_job_count(self):
        """测试创建JobCount"""
        job_count = JobCount(
            job_count=42,
            status="active"
        )
        assert job_count.job_count == 42
        assert job_count.status == "active"
    
    def test_job_count_with_zero(self):
        """测试零作业数的JobCount"""
        job_count = JobCount(
            job_count=0,
            status="idle"
        )
        assert job_count.job_count == 0
        assert job_count.status == "idle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])