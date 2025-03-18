import logging
from pymongo import MongoClient

from MonitorService.App.DTOs.NodeStatusDTO import NodeStatusDTO

class MonitorRepository:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27018/")
        self.db = self.client["cluster_status"]
        self.status_collection = self.db["status"]

    def update_all_node_statuses(self, node_statuses: [NodeStatusDTO]):
        try:
            formatted_node_statuses = {dto.node_name: dto.status for dto in node_statuses}
            self.status_collection.update_one(
                {"_id": "status_report"},
                {"$set": {"nodes": formatted_node_statuses}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error updating node statuses in the database: {e}")
