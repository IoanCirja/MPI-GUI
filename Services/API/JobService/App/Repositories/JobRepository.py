import logging
from typing import List

from firebase_admin import db

from JobService.App.DTOs import JobDTO

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
class JobRepository:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.ref = db.reference(f"users/{self.user_id}/jobs")

    def insert_job(self, job: JobDTO):
        try:
            job_data = job.dict()
            self.ref.child(job.id).set(job_data)
            return job.id
        except Exception as e:
            logging.error(f"Error inserting job: {str(e)}")
            return None

    def get_job_by_id(self, job_id: str):
        try:
            job_ref = self.ref.child(job_id)
            job_data = job_ref.get()



            return job_data
        except Exception as e:
            logging.error(f"Error fetching job by ID: {str(e)}")
            return None

    def get_all_jobs(self) -> List[dict]:
        try:
            jobs_ref = self.ref.get()

            if not jobs_ref:
                return []

            return [{"id": job_id, **job_data} for job_id, job_data in jobs_ref.items()]

        except Exception as e:
            logger.error(f"Error fetching all jobs: {str(e)}")
            return []

    def update_job(self, job_id: str, updated_data: dict):
        try:
            job_ref = self.ref.child(job_id)

            job_ref.update(updated_data)

            logging.info(f"Job with ID {job_id} successfully updated with data: {updated_data}")
            return True
        except Exception as e:
            logging.error(f"Error updating job: {str(e)}")
            return False

