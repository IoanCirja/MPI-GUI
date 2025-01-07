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
