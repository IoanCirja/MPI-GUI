import logging
from typing import List

from pymongo import MongoClient

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
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["job_service_db"]
        self.jobs_collection = self.db["jobs"]

    def insert_job(self, job: JobDTO):
        try:
            job_data = job.dict()
            job_data["_id"] = job_data.pop("id")
            job_data["user_id"] = self.user_id

            self.jobs_collection.insert_one(job_data)
            return job_data["_id"]
        except Exception as e:
            logging.error(f"Error inserting job: {str(e)}")
            return None

    def get_job_by_id(self, job_id: str):
        try:
            job_data = self.jobs_collection.find_one({"_id": job_id, "user_id": self.user_id})
            if job_data:
                job_data["id"] = str(job_data["_id"])
                del job_data["_id"]
            return job_data if job_data else None
        except Exception as e:
            logger.error(f"Error fetching job by ID: {str(e)}")
            return None

    def get_all_jobs(self) -> List[dict]:
        try:
            jobs = self.jobs_collection.find({"user_id": self.user_id})
            jobs_list = list(jobs) if jobs else []

            for job in jobs_list:
                job["id"] = str(job["_id"])
                del job["_id"]
            return jobs_list
        except Exception as e:
            logger.error(f"Error fetching all jobs: {str(e)}")
            return []

    def update_job(self, job_id: str, updated_data: dict) -> bool:
        try:
            result = self.jobs_collection.update_one(
                {"_id": job_id, "user_id": self.user_id},
                {"$set": updated_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating job: {str(e)}")
            return False

    def get_pending_jobs_count_for_user(self):
        try:
            pending_jobs_count = self.jobs_collection.count_documents({"user_id": self.user_id, "status": "pending"})
            return pending_jobs_count
        except Exception as e:
            logger.error(f"Error fetching pending jobs count: {str(e)}")
            return 0