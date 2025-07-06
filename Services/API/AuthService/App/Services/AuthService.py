import hashlib
import os
import uuid
import jwt
from datetime import datetime, timedelta
from decouple import RepositoryEnv, Config

from AuthService.App.DTOs.LoginRequest import LoginRequest
from AuthService.App.DTOs.SignUpRequest import SignUpRequest
from AuthService.App.Repositories.AuthRepository import UserRepository

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))


class UserService:
    @staticmethod
    def loginUser(loginRequest: LoginRequest, iss:str) -> str:
        userData = UserRepository.getUserByEmail(loginRequest.email)
        if not userData:
            raise ValueError("User does not exist")


        suspensions = userData.get("suspensions", [])
        for suspension in suspensions:
            suspend_start = datetime.fromisoformat(suspension["start_date"])
            suspend_duration = timedelta(minutes=suspension["suspend_time"])
            suspend_end = suspend_start + suspend_duration

            if datetime.utcnow() < suspend_end:
                raise ValueError(f"User is currently suspended until {suspend_end}. Try again later.")

        stored_hash = userData["password"]
        salt = userData["salt"]

        input_hash = hashlib.sha256((loginRequest.password + salt).encode('utf-8')).hexdigest()

        if input_hash != stored_hash:
            raise ValueError("Invalid credentials")

        token_data = {
            "iss": iss,
            "sub": str(userData["id"]),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=int(env("ACCESS_TOKEN_EXPIRE_MINUTES"))),
            "jti": str(uuid.uuid4()),
            "username": userData.get("username", ""),
            "email": userData.get("email", ""),
            "max_processes_per_user": userData.get("max_processes_per_user", 0),
            "max_processes_per_node_per_user": userData.get("max_processes_per_node_per_user", 0),
            "max_running_jobs": userData.get("max_running_jobs", 0),
            "max_pending_jobs": userData.get("max_pending_jobs", 0),
            "max_job_time": userData.get("max_job_time", 0),
            "allowed_nodes": userData.get("allowed_nodes", ""),
            "max_nodes_per_job": int(userData.get("max_nodes_per_job", 0)),
            "max_total_jobs": userData.get("max_total_jobs", 0),
            "rights": userData.get("rights", "base")
        }

        token = jwt.encode(token_data, key=env("SECRET_KEY"), algorithm=env("ALGORITHM"))
        return token


    @staticmethod
    def createUser(createUserRequest: SignUpRequest):
        if UserRepository.getUserByUsername(createUserRequest.username):
            raise ValueError("Username already exists")
        if UserRepository.getUserByEmail(createUserRequest.email):
            raise ValueError("Email already exists")
        if createUserRequest.password != createUserRequest.retypePassword:
            raise ValueError("Passwords do not match")

        salt = os.urandom(16).hex()
        hashedPassword = hashlib.sha256((createUserRequest.password + salt).encode('utf-8')).hexdigest()

        ##admin
        # data = {
        #     "username": createUserRequest.username,
        #     "email": createUserRequest.email,
        #     "password": hashedPassword,
        #     "salt": salt,
        #     "max_processes_per_user": 999,
        #     "max_processes_per_node_per_user": 999,
        #     "max_running_jobs": 999,
        #     "max_pending_jobs": 999,
        #     "max_job_time": 999,
        #     "allowed_nodes": "C00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19, C20",
        #     "max_nodes_per_job": 999,
        #     "max_total_jobs": 999,
        #     "suspensions": [],
        #     "rights": 'admin'
        # }

        data = {
            "username": createUserRequest.username,
            "email": createUserRequest.email,
            "password": hashedPassword,
            "salt": salt,
            "max_processes_per_user": 50,
            "max_processes_per_node_per_user": 20,
            "max_running_jobs": 2,
            "max_pending_jobs": 5,
            "max_job_time": 1000,
            "allowed_nodes": "C00, C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, C13, C14, C15",
            "max_nodes_per_job": 10,
            "max_total_jobs": 500,
            "suspensions": [],
            "rights": 'base'
        }

        UserRepository.addUser(data)

    @staticmethod
    def getAllNonAdminUsers():
        all_users = UserRepository.getAllUsers()
        non_admin_users = [user for user in all_users if user.get("rights") != "admin"]
        return non_admin_users

    @staticmethod
    def getUserByIdforQuota(user_id: str) -> dict:
        return UserRepository.getUserByIdforQuota(user_id)

    @staticmethod
    def getQuotas() -> dict:
        return UserRepository.getQuotas()

    @staticmethod
    def updateUser(user_id: str, user_data: dict) -> dict:
        existing_user = UserRepository.getUserByIdforQuota(user_id)

        if not existing_user:
            return None

        updated_user_data = {**existing_user, **user_data}
        allowed_fields = {
            "max_processes_per_user",
            "max_processes_per_node_per_user",
            "max_running_jobs",
            "max_pending_jobs",
            "max_job_time",
            "allowed_nodes",
            "max_nodes_per_job",
            "max_total_jobs",
        }

        filtered_update = {key: value for key, value in updated_user_data.items() if key in allowed_fields}
        UserRepository.updateUser(user_id, filtered_update)

        return filtered_update

    @staticmethod
    def suspendUser(user_id: str, suspend_time: int) -> dict:
        updated_user = UserRepository.suspendUser(user_id, suspend_time)
        if not updated_user:
            raise ValueError("User not found")

        return updated_user

    def removeSuspension(user_id: str, suspension_id: str) -> dict:
        updated_user = UserRepository.removeSuspension(user_id, suspension_id)
        if not updated_user:
            raise ValueError("Suspension not found or user not found")

        return updated_user