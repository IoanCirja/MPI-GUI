from firebase_admin import db
class UserRepository:
    @staticmethod
    def addUser(data: dict) -> dict:
        ref = db.reference("users")
        newUserRef = ref.push(data)

        user_data = ref.child(newUserRef.key).get()

        user_data["id"] = newUserRef.key

        return user_data
    @staticmethod
    def getUserByEmail(email: str) -> dict:
        ref = db.reference("users")
        users = ref.order_by_child("email").equal_to(email).get()
        if users:
            return next(iter(users.values()))
        return None