import uuid
from datetime import datetime

from firebase_admin import db


class UserRepository:
    @staticmethod
    def addUser(data: dict):
        ref = db.reference("users")

        ref.push(data)

    @staticmethod
    def getUserByEmail(email: str) -> dict:
        ref = db.reference("users")
        users = ref.order_by_child("email").equal_to(email).get()

        if users:
            for user_id, user_data in users.items():
                user_data["id"] = user_id
                return user_data
        return None

    @staticmethod
    def getUserByUsername(username: str) -> dict:
        ref = db.reference("users")
        users = ref.order_by_child("username").equal_to(username).get()

        if users:
            for user_id, user_data in users.items():
                user_data["id"] = user_id
                return user_data
        return None

    @staticmethod
    def getAllUsers() -> list:
        ref = db.reference("users")
        users_snapshot = ref.get()

        if not users_snapshot:
            return []

        all_users = []
        for user_id, user_data in users_snapshot.items():
            user_data["id"] = user_id
            all_users.append(user_data)

        return all_users

    @staticmethod
    def getUserByIdforQuota(user_id: str) -> dict:
        ref = db.reference(f"users/{user_id}")
        user_data = ref.get()

        if user_data:
            user_data["id"] = user_id

            allowed_keys = {
                "max_processes_per_user",
                "max_parallel_jobs_per_user",
                "max_jobs_in_queue",
                "max_memory_usage_per_user_per_cluster",
                "max_memory_usage_per_process",
                "max_allowed_nodes",
                "max_job_time",
            }
            filtered_user = {key: value for key, value in user_data.items() if key in allowed_keys}

            return filtered_user

        return None

    @staticmethod
    def getUserById(user_id: str) -> dict:
        ref = db.reference(f"users/{user_id}")
        user_data = ref.get()

        if user_data:
            user_data["id"] = user_id

            return user_data

        return None

    @staticmethod
    def getQuotas() -> dict:
        ref = db.reference("users")
        users_data = ref.get()

        if users_data:
            allowed_keys = {
                "max_processes_per_user",
                "max_processes_per_node_per_user",
                "max_running_jobs",
                "max_pending_jobs",
                "max_job_time",
                "allowed_nodes",
                "max_nodes_per_job",
                "max_total_jobs",
            }

            user_quotas = {}

            for user_id, user_data in users_data.items():
                filtered_user = {key: value for key, value in user_data.items() if key in allowed_keys}
                if filtered_user:
                    user_quotas[user_id] = filtered_user

            return user_quotas

        return {}

    @staticmethod
    def updateUser(user_id: str, data: dict):
        ref = db.reference(f"users/{user_id}")
        ref.update(data)

    @staticmethod
    def suspendUser(user_id: str, suspend_time: int) -> dict:
        ref = db.reference(f"users/{user_id}")
        user_data = ref.get()

        if not user_data:
            return None

        suspensions = user_data.get("suspensions", [])

        suspensions.append({
            "id": str(uuid.uuid4()),
            'user_id': user_id,
            "username": user_data.get("username", ""),
            "email": user_data.get("email", ""),
            "start_date": datetime.utcnow().isoformat(),
            "suspend_time": suspend_time
        })

        ref.update({"suspensions": suspensions})

        return {"id": user_id, "suspensions": suspensions}

    @staticmethod
    def removeSuspension(user_id: str, suspension_id: str) -> dict:
        """Remove a suspension by suspension_id for the given user."""
        ref = db.reference(f"users/{user_id}")
        user_data = ref.get()

        if not user_data:
            return None  # User not found

        suspensions = user_data.get("suspensions", [])

        # Filter out the suspension with the given ID
        updated_suspensions = [suspension for suspension in suspensions if suspension["id"] != suspension_id]

        # If no suspensions were removed, return None
        if len(updated_suspensions) == len(suspensions):
            return None

        # Update the user with the new suspensions list
        ref.update({"suspensions": updated_suspensions})

        return {"id": user_id, "suspensions": updated_suspensions}