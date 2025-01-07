import logging
from typing import List

from firebase_admin import db
from JobService.App.Entities.JobEntities import JobEntity


class JobRepository:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.ref = db.reference(f"users/{self.user_id}/jobs")

    def insert_job(self, job: JobEntity):
        try:
            job_ref = self.ref.push()
            job_data = job.dict()

            logging.info(f"Inserting job into Firebase: {job_data}")

            job_ref.set(job_data)
            logging.info(f"Job successfully inserted with ID: {job_ref.key}")
            return job_ref.key
        except Exception as e:
            logging.error(f"Error inserting job: {str(e)}")
            return None

    def get_job_by_id(self, job_id: str):
        try:
            job_ref = self.ref.child(job_id)
            job_data = job_ref.get()

            if job_data:
                logging.info(f"Fetched job data: {job_data}")
            else:
                logging.warning(f"No job found with ID: {job_id}")

            return job_data
        except Exception as e:
            logging.error(f"Error fetching job by ID: {str(e)}")
            return None
    def get_all_jobs(self) -> List[dict]:
        try:
            jobs_ref = self.ref.get()
            if not jobs_ref:
                return []

            return list(jobs_ref.values())
        except Exception as e:
            print(f"Error fetching all jobs: {str(e)}")
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

