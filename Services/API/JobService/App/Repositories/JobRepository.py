import base64
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
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
        self.quotas_collection = self.db["quotas"]
        self.usage_collection = self.db["usage"]



    def update_quota(self, quota_data: dict):
        try:

            self.quotas_collection.update_one(
                {"_id": "quota_report"},
                {"$set": quota_data},
                upsert=True

            )
            logging.info(f"Quota data updated.")


        except Exception as e:
            raise Exception(f"Error updating quota data: {e}")

    def get_quotas(self):
        try:
            document = self.quotas_collection.find_one({"_id": "quota_report"})
            if document:
                return document
            else:
                return {}
        except Exception as e:
            return {}


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
            job_data = self.jobs_collection.find_one({"_id": job_id})
            if job_data:
                job_data["id"] = str(job_data["_id"])
                del job_data["_id"]
            return job_data if job_data else None
        except Exception as e:
            logger.error(f"Error fetching job by ID: {str(e)}")
            return None

    def get_all_jobs_for_user(self) -> List[dict]:
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

    def get_all_jobs(self) -> List[dict]:
        try:
            jobs = self.jobs_collection.find()
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
                {"_id": job_id},
                {"$set": updated_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating job: {str(e)}")
            return False

    def get_pending_jobs_for_user(self):
        try:
            pending_jobs_for_user = list(self.jobs_collection.find({"user_id": self.user_id, "status": "pending"}))
            return pending_jobs_for_user
        except Exception as e:
            logger.error(f"Error fetching pending jobs count: {str(e)}")
            return []
    def get_running_jobs_for_user(self):
        try:
            running_jobs_for_user = list(self.jobs_collection.find({"user_id": self.user_id, "status": "running"}))
            return running_jobs_for_user
        except Exception as e:
            logger.error(f"Error fetching pending jobs count: {str(e)}")
            return []

    def get_all_pending_jobs(self):
        try:
            pending_jobs = list(self.jobs_collection.find({"status": "pending"}).sort("beginDate", 1))
            return pending_jobs
        except Exception as e:
            logger.error(f"Error fetching all pending jobs: {str(e)}")
            return []
    def get_all_running_jobs(self):
        try:
            pending_jobs = list(self.jobs_collection.find({"status": "running"}))
            return pending_jobs
        except Exception as e:
            logger.error(f"Error fetching all pending jobs: {str(e)}")
            return []


    def compute_cluster_usage(self):
        try:
            running_jobs = list(self.jobs_collection.find({"status": "running"}))

            running_hostfiles = [running_job["hostFile"] for running_job in running_jobs]
            node_slots = defaultdict(
                lambda: {"jobs": [], "users": set(), "total": 0})  # Store job information, users, and total usage

            # Collect job usage and user IDs from running jobs
            for running_job in running_jobs:
                encoded_hostfile = running_job["hostFile"]
                decoded_content = base64.b64decode(encoded_hostfile).decode("utf-8")

                lines = decoded_content.splitlines()
                user_id = running_job["user_id"]  # Assuming each job has a 'user_id' field
                job_id = running_job["_id"]  # Assuming each job has a unique '_id'
                begin_date = running_job["beginDate"]  # Assuming each job has a 'start_date' field

                for line in lines:
                    parts = line.split()
                    if len(parts) == 2 and "slots=" in parts[1]:
                        node = parts[0]
                        slots = int(parts[1].split("=")[1])

                        # Update node job list and total usage
                        job_info = {
                            "job_id": job_id,
                            "user_id": user_id,
                            "usage": slots,
                            "begin_date": begin_date
                        }
                        node_slots[node]["jobs"].append(job_info)
                        node_slots[node]["users"].add(user_id)
                        node_slots[node]["total"] += slots

            # Ensure all 20 nodes are included in the usage data
            all_nodes = [f"C05-{i:02d}" for i in range(21)]  # Create a list of nodes c05-00 to c05-20
            for node in all_nodes:
                if node not in node_slots:
                    node_slots[node] = {"jobs": [], "users": set(),
                                        "total": 0}  # Initialize unused nodes with no jobs, users, and 0 total usage

            # Convert users set to comma-separated strings
            for node in node_slots:
                node_slots[node]["users"] = ",".join(node_slots[node]["users"])
                # Convert jobs list to a more readable format (optional: could keep as is if raw data is needed)
                node_slots[node]["jobs"] = [{"job_id": job["job_id"], "user_id": job["user_id"], "usage": job["usage"],
                                             "begin_date": job["begin_date"]}
                                            for job in node_slots[node]["jobs"]]

            # Update the usage collection
            usage_data = {
                "_id": "cluster_usage",  # Unique identifier for current cluster usage
                "usage": node_slots  # Store node usage, jobs, and users
            }

            # Upsert the data to the usage collection
            self.usage_collection.update_one(
                {"_id": "cluster_usage"},
                {"$set": usage_data},
                upsert=True
            )

            # Now we handle the history insertion with the date and checking for changes
            # Get the last two history records to check if any changes occurred
            # last_two_history = list(self.usage_collection.find({"_id": "history"}).sort([("date", -1)]).limit(2))
            #
            # if len(last_two_history) < 2:
            #     # If less than two records are found, insert the new history entry
            #     self.insert_history(node_slots)
            # else:
            #     # Compare the node values of the last two entries
            #     last_history = last_two_history[0]["usage"]
            #     second_last_history = last_two_history[1]["usage"]
            #     last_date = datetime.strptime(last_two_history[0]["date"], "%Y-%m-%d %H:%M:%S")
            #     second_last_date = datetime.strptime(last_two_history[1]["date"], "%Y-%m-%d %H:%M:%S")
            #
            #     # If node values are the same and the date difference is less than 1 minute, skip insertion
            #     if last_history == second_last_history and (last_date - second_last_date) < timedelta(minutes=1):
            #         logger.info("No significant change detected in node values or time, skipping history insertion.")
            #     else:
            #         # Insert a new history entry since there's a change
            #         self.insert_history(node_slots)

            return node_slots  # Return the computed node usage

        except Exception as e:
            logger.error(f"Error computing cluster usage: {str(e)}")
            return {}

    def compute_request_usage(self):
        try:
            running_jobs = list(self.jobs_collection.find({"status": "pending"}))

            running_hostfiles = [running_job["hostFile"] for running_job in running_jobs]
            node_slots = defaultdict(
                lambda: {"jobs": [], "users": set(), "total": 0})  # Store job information, users, and total usage

            # Collect job usage and user IDs from running jobs
            for running_job in running_jobs:
                encoded_hostfile = running_job["hostFile"]
                decoded_content = base64.b64decode(encoded_hostfile).decode("utf-8")

                lines = decoded_content.splitlines()
                user_id = running_job["user_id"]  # Assuming each job has a 'user_id' field
                job_id = running_job["_id"]  # Assuming each job has a unique '_id'
                begin_date = running_job["beginDate"]  # Assuming each job has a 'start_date' field

                for line in lines:
                    parts = line.split()
                    if len(parts) == 2 and "slots=" in parts[1]:
                        node = parts[0]
                        slots = int(parts[1].split("=")[1])

                        # Update node job list and total usage
                        job_info = {
                            "job_id": job_id,
                            "user_id": user_id,
                            "usage": slots,
                            "begin_date": begin_date
                        }
                        node_slots[node]["jobs"].append(job_info)
                        node_slots[node]["users"].add(user_id)
                        node_slots[node]["total"] += slots

            # Ensure all 20 nodes are included in the usage data
            all_nodes = [f"C05-{i:02d}" for i in range(21)]  # Create a list of nodes c05-00 to c05-20
            for node in all_nodes:
                if node not in node_slots:
                    node_slots[node] = {"jobs": [], "users": set(),
                                        "total": 0}  # Initialize unused nodes with no jobs, users, and 0 total usage

            # Convert users set to comma-separated strings
            for node in node_slots:
                node_slots[node]["users"] = ",".join(node_slots[node]["users"])
                # Convert jobs list to a more readable format (optional: could keep as is if raw data is needed)
                node_slots[node]["jobs"] = [{"job_id": job["job_id"], "user_id": job["user_id"], "usage": job["usage"],
                                             "begin_date": job["begin_date"]}
                                            for job in node_slots[node]["jobs"]]

            # Update the usage collection
            usage_data = {
                "_id": "request_usage",  # Unique identifier for current cluster usage
                "usage": node_slots  # Store node usage, jobs, and users
            }

            # Upsert the data to the usage collection
            self.usage_collection.update_one(
                {"_id": "request_usage"},
                {"$set": usage_data},
                upsert=True
            )

            return node_slots  # Return the computed node usage

        except Exception as e:
            logger.error(f"Error computing cluster usage: {str(e)}")
            return {}

    def insert_history(self, node_slots):
        """Helper function to insert node usage history."""
        history_data = {
            "_id": str(int(time.time())),  # Unique identifier based on timestamp
            "usage": node_slots,
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())  # Current timestamp as date
        }

        # Insert the history data into the history collection
        try:
            self.usage_collection.update_one(
                {"_id": "history"},
                {"$push": {"history": history_data}},
                upsert=True  # Create the document if it doesn't exist
            )
            logger.info(f"History data inserted: {history_data}")
        except Exception as e:
            logger.error(f"Error inserting history data: {str(e)}")

    def clear_jobs(self) -> bool:
        try:
            result = self.jobs_collection.delete_many({"user_id": self.user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error clearing jobs: {str(e)}")
            return False

    def clear_job(self, job_id: str) -> bool:
        try:
            job = self.jobs_collection.find_one({"user_id": self.user_id, "_id": job_id})
            if not job:
                logger.warning(f"Job {job_id} not found for user {self.user_id}")
                return False

            result = self.jobs_collection.delete_one({"user_id": self.user_id, "_id": job_id})
            if result.deleted_count > 0:
                logger.info(f"Job {job_id} successfully deleted for user {self.user_id}")
                return True
            else:
                logger.warning(f"Failed to delete job {job_id} for user {self.user_id}")
                return False
        except Exception as e:
            logger.error(f"Error clearing job {job_id} for user {self.user_id}: {str(e)}")
            return False