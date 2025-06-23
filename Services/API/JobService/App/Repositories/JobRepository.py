import base64
from collections import defaultdict
from typing import List
from pymongo import MongoClient
from JobService.App.DTOs import JobDTO


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
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_quotas(self):
        try:
            document = self.quotas_collection.find_one({"_id": "quota_report"})
            if document:
                return document
            else:
                return {}
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def insert_job(self, job: JobDTO):
        try:
            job_data = job.dict()
            job_data["_id"] = job_data.pop("id")

            self.jobs_collection.insert_one(job_data)
            return job_data["_id"]
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_job_by_id(self, job_id: str):
        try:
            job_data = self.jobs_collection.find_one({"_id": job_id})
            if job_data:
                job_data["id"] = str(job_data["_id"])
                del job_data["_id"]
            return job_data if job_data else None
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_all_jobs_for_user(self) -> List[dict]:
        try:
            jobs = self.jobs_collection.find({"user_id": self.user_id})
            jobs_list = list(jobs) if jobs else []

            for job in jobs_list:
                job["id"] = str(job["_id"])
                del job["_id"]
            return jobs_list
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_all_jobs(self) -> List[dict]:
        try:
            jobs = self.jobs_collection.find()
            jobs_list = list(jobs) if jobs else []

            for job in jobs_list:
                job["id"] = str(job["_id"])
                del job["_id"]
            return jobs_list
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def update_job(self, job_id: str, updated_data: dict) -> bool:
        try:
            result = self.jobs_collection.update_one(
                {"_id": job_id},
                {"$set": updated_data}
            )
            return result.modified_count > 0
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_pending_jobs_for_user(self):
        try:
            pending_jobs_for_user = list(self.jobs_collection.find({"user_id": self.user_id, "status": "pending"}))
            return pending_jobs_for_user
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_running_jobs_for_user(self):
        try:
            running_jobs_for_user = list(self.jobs_collection.find({"user_id": self.user_id, "status": "running"}))
            return running_jobs_for_user
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_all_pending_jobs(self):
        try:
            pending_jobs = list(self.jobs_collection.find({"status": "pending"}).sort("beginDate", 1))
            return pending_jobs
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def get_all_running_jobs(self):
        try:
            pending_jobs = list(self.jobs_collection.find({"status": "running"}))
            return pending_jobs
        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def compute_cluster_usage(self):
        try:
            running_jobs = list(self.jobs_collection.find({"status": "running"}))

            running_hostfiles = [running_job["hostFile"] for running_job in running_jobs]
            node_slots = defaultdict(
                lambda: {"jobs": [], "users": set(), "total": 0})

            for running_job in running_jobs:
                encoded_hostfile = running_job["hostFile"]
                decoded_content = base64.b64decode(encoded_hostfile).decode("utf-8")

                lines = decoded_content.splitlines()
                user_id = running_job["user_id"]
                job_id = running_job["_id"]
                begin_date = running_job["beginDate"]

                for line in lines:
                    parts = line.split()
                    if len(parts) == 2 and "slots=" in parts[1]:
                        node = parts[0]
                        slots = int(parts[1].split("=")[1])

                        job_info = {
                            "job_id": job_id,
                            "user_id": user_id,
                            "usage": slots,
                            "begin_date": begin_date
                        }
                        node_slots[node]["jobs"].append(job_info)
                        node_slots[node]["users"].add(user_id)
                        node_slots[node]["total"] += slots

            all_nodes = [f"C05-{i:02d}" for i in range(21)]
            for node in all_nodes:
                if node not in node_slots:
                    node_slots[node] = {"jobs": [], "users": set(),
                                        "total": 0}

            for node in node_slots:
                node_slots[node]["users"] = ",".join(node_slots[node]["users"])

                node_slots[node]["jobs"] = [{"job_id": job["job_id"], "user_id": job["user_id"], "usage": job["usage"],
                                             "begin_date": job["begin_date"]}
                                            for job in node_slots[node]["jobs"]]

            usage_data = {
                "_id": "cluster_usage",
                "usage": node_slots
            }

            self.usage_collection.update_one(
                {"_id": "cluster_usage"},
                {"$set": usage_data},
                upsert=True
            )

            return node_slots

        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def compute_request_usage(self):
        try:
            running_jobs = list(self.jobs_collection.find({"status": "pending"}))

            running_hostfiles = [running_job["hostFile"] for running_job in running_jobs]
            node_slots = defaultdict(
                lambda: {"jobs": [], "users": set(), "total": 0})

            for running_job in running_jobs:
                encoded_hostfile = running_job["hostFile"]
                decoded_content = base64.b64decode(encoded_hostfile).decode("utf-8")

                lines = decoded_content.splitlines()
                user_id = running_job["user_id"]
                job_id = running_job["_id"]
                begin_date = running_job["beginDate"]

                for line in lines:
                    parts = line.split()
                    if len(parts) == 2 and "slots=" in parts[1]:
                        node = parts[0]
                        slots = int(parts[1].split("=")[1])

                        job_info = {
                            "job_id": job_id,
                            "user_id": user_id,
                            "usage": slots,
                            "begin_date": begin_date
                        }
                        node_slots[node]["jobs"].append(job_info)
                        node_slots[node]["users"].add(user_id)
                        node_slots[node]["total"] += slots

            all_nodes = [f"C05-{i:02d}" for i in range(21)]
            for node in all_nodes:
                if node not in node_slots:
                    node_slots[node] = {"jobs": [], "users": set(),
                                        "total": 0}

            for node in node_slots:
                node_slots[node]["users"] = ",".join(node_slots[node]["users"])

                node_slots[node]["jobs"] = [{"job_id": job["job_id"], "user_id": job["user_id"], "usage": job["usage"],
                                             "begin_date": job["begin_date"]}
                                            for job in node_slots[node]["jobs"]]

            usage_data = {
                "_id": "request_usage",
                "usage": node_slots
            }

            self.usage_collection.update_one(
                {"_id": "request_usage"},
                {"$set": usage_data},
                upsert=True
            )

            return node_slots

        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def clear_jobs(self) -> List[str]:
        try:
            cursor = self.jobs_collection.find(
                {"user_id": self.user_id},
                {"_id": 1}
            )
            job_ids = [str(doc["_id"]) for doc in cursor]

            if not job_ids:
                return []

            result = self.jobs_collection.delete_many({"user_id": self.user_id})

            return job_ids

        except Exception as e:
            raise Exception(f"Repository Error: {e}")

    def clear_job(self, job_id: str) -> bool:
        try:
            job = self.jobs_collection.find_one({"user_id": self.user_id, "_id": job_id})
            if not job:
                return False

            result = self.jobs_collection.delete_one({"user_id": self.user_id, "_id": job_id})
            if result.deleted_count > 0:
                return True
            else:
                return False
        except Exception as e:
            raise Exception(f"Repository Error: {e}")
