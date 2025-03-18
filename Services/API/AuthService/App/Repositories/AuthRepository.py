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

