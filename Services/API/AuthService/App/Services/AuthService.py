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

        stored_hash = userData["password"]
        salt = userData["salt"]

        input_hash = hashlib.sha256((loginRequest.password + salt).encode('utf-8')).hexdigest()

        if input_hash != stored_hash:
            raise ValueError("Invalid credentials")

        token_data = {
            "iss": iss,
            "sub": userData["id"],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "jti": str(uuid.uuid4()),
            'username': userData["username"],
            'email': userData["email"],
            "max_processes_per_user": userData.get("max_processes_per_user", 5),
            "max_parallel_jobs_per_user": userData.get("max_parallel_jobs_per_user", 3),
            "max_jobs_in_queue": userData.get("max_jobs_in_queue", 10),
            "max_memory_usage_per_user_per_cluster": userData.get("max_memory_usage_per_user_per_cluster", "8GB"),
            "max_memory_usage_per_process": userData.get("max_memory_usage_per_process", "2GB"),
            "max_allowed_nodes": userData.get("max_allowed_nodes", 7),
            "max_job_time": userData.get("max_job_time", "2h"),
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

        data = {
            "username": createUserRequest.username,
            "email": createUserRequest.email,
            "password": hashedPassword,
            "salt": salt,
            "max_processes_per_user": 5,
            "max_parallel_jobs_per_user": 3,
            "max_jobs_in_queue": 10,
            "max_memory_usage_per_user_per_cluster": "8GB", # total memory usage
            "max_memory_usage_per_process": "2GB", # memory for a signle process
            "max_allowed_nodes": 7, # max node job distribution
            "max_job_time": "2h", # max time for a job
            "rights": "base"
        }

        UserRepository.addUser(data)

    @staticmethod
    def getAllNonAdminUsers():
        all_users = UserRepository.getAllUsers()

        non_admin_users = [user for user in all_users if user.get("rights") != "admin"]

        return non_admin_users
