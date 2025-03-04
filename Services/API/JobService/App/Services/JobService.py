import base64
import logging
from typing import List

from JobService.App.DTOs.JobDTO import JobDTO
from JobService.App.Entities.JobEntities import JobEntity
from JobService.App.Repositories.JobRepository import JobRepository


class JobService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.repository = JobRepository(user_id)

    def encode_file_to_base64(self, file_content: bytes) -> str:
        return base64.b64encode(file_content).decode('utf-8')

    def create_and_save_job(self, job_data: JobDTO, file_content: bytes, hostfile_content: bytes, command: str):
        file_base64 = self.encode_file_to_base64(file_content)
        hostfile_base64 = self.encode_file_to_base64(hostfile_content)

        job = JobDTO(
            jobName=job_data.jobName,
            jobDescription=job_data.jobDescription,
            beginDate=job_data.beginDate,
            endDate=job_data.endDate,
            numProcesses=job_data.numProcesses,
            allowOverSubscription=job_data.allowOverSubscription,
            file=file_base64,
            hostfile=hostfile_base64,
            command=command,
            output=job_data.output,
            status='pending',
            environmentVars=job_data.environmentVars,
            displayMap=job_data.displayMap,
            rankBy=job_data.rankBy,
            mapBy=job_data.mapBy
        )

        job_id = self.repository.insert_job(job)
        return job_id
    def get_job_by_id(self, job_id: str):
        try:
            job_data = self.repository.get_job_by_id(job_id)
            if job_data:
                return JobDTO(**job_data)
            return None
        except Exception as e:
            print(f"Error fetching job by ID: {str(e)}")
            return None

    def get_all_jobs(self) -> List[JobEntity]:
        try:
            jobs_data = self.repository.get_all_jobs()
            if not jobs_data:
                return []

            return [JobEntity(**job) for job in jobs_data]
        except Exception as e:
            print(f"Error fetching all jobs: {str(e)}")
            return []

    def update_job_status_and_output(self, job_id: str, job_data: JobDTO):
        updated_data = {
            "status": job_data.status,
            "output": job_data.output,
            "endDate": job_data.endDate,
        }
        success = self.repository.update_job(job_id, updated_data)
        if not success:
            logging.error(f"Failed to update job with ID {job_id}")
        return success