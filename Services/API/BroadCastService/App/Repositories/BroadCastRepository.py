import logging
from pymongo import MongoClient

class BroadCastRepository:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27018/")
        self.db = self.client["cluster_status"]
        self.status_collection = self.db["status"]



    def get_all_node_statuses(self):
        try:
            document = self.status_collection.find_one({"_id": "status_report"})
            if document:
                return document.get("nodes", {})
            else:
                return {}
        except Exception as e:
            logging.error(f"Error fetching node statuses from the database: {e}")
            return {}
