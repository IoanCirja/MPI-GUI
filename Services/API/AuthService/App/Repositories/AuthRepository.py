import uuid
from datetime import datetime
from typing import Optional, List, Dict

from pymongo import MongoClient
from bson.objectid import ObjectId


class UserRepository:
    # shared Mongo client & collection
    _client = MongoClient("mongodb://localhost:27019/")
    _db = _client["auth_service_db"]
    _users = _db["users"]

    # fields to include in quota-only views
    _quota_fields = {
        "max_processes_per_user",
        "max_processes_per_node_per_user",
        "max_running_jobs",
        "max_pending_jobs",
        "max_job_time",
        "allowed_nodes",
        "max_nodes_per_job",
        "max_total_jobs",
    }

    @staticmethod
    def addUser(data: dict):
        """Insert a new user document (no return, to match original)."""
        UserRepository._users.insert_one(data)

    @staticmethod
    def getUserByEmail(email: str) -> Optional[dict]:
        doc = UserRepository._users.find_one({"email": email})
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def getUserByUsername(username: str) -> Optional[dict]:
        doc = UserRepository._users.find_one({"username": username})
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def getAllUsers() -> List[dict]:
        cursor = UserRepository._users.find()
        all_users = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            all_users.append(doc)
        return all_users

    @staticmethod
    def getUserByIdforQuota(user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None

        doc = UserRepository._users.find_one({"_id": oid})
        if not doc:
            return None

        filtered = {k: v for k, v in doc.items() if k in UserRepository._quota_fields}
        filtered["id"] = user_id
        return filtered

    @staticmethod
    def getUserById(user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None

        doc = UserRepository._users.find_one({"_id": oid})
        if not doc:
            return None

        doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def getQuotas() -> Dict[str, dict]:
        quotas = {}
        for doc in UserRepository._users.find():
            filtered = {k: v for k, v in doc.items() if k in UserRepository._quota_fields}
            if filtered:
                user_id = str(doc["_id"])
                quotas[user_id] = filtered
        return quotas

    @staticmethod
    def updateUser(user_id: str, data: dict):
        """Partial update; no return to match original signature."""
        try:
            oid = ObjectId(user_id)
        except Exception:
            return
        UserRepository._users.update_one({"_id": oid}, {"$set": data})

    @staticmethod
    def suspendUser(user_id: str, suspend_time: int) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None

        user = UserRepository._users.find_one({"_id": oid})
        if not user:
            return None

        suspensions = user.get("suspensions", [])
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "start_date": datetime.utcnow().isoformat(),
            "suspend_time": suspend_time,
        }
        suspensions.append(entry)
        UserRepository._users.update_one({"_id": oid}, {"$set": {"suspensions": suspensions}})
        return {"id": user_id, "suspensions": suspensions}

    @staticmethod
    def removeSuspension(user_id: str, suspension_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None

        user = UserRepository._users.find_one({"_id": oid})
        if not user:
            return None

        suspensions = user.get("suspensions", [])
        updated = [s for s in suspensions if s.get("id") != suspension_id]
        if len(updated) == len(suspensions):
            return None  # no change

        UserRepository._users.update_one({"_id": oid}, {"$set": {"suspensions": updated}})
        return {"id": user_id, "suspensions": updated}
