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
            "max_job_time": 60,
            "rights": "base"
        }

        UserRepository.addUser(data)

    @staticmethod
    def getAllNonAdminUsers():
        all_users = UserRepository.getAllUsers()

        non_admin_users = [user for user in all_users if user.get("rights") != "admin"]

        return non_admin_users

    @staticmethod
    def getUserById(user_id: str) -> dict:
        return UserRepository.getUserById(user_id)
    @staticmethod
    def getQuotas() -> dict:
        return UserRepository.getQuotas()

    @staticmethod
    def updateUser(user_id: str, user_data: dict) -> dict:
        existing_user = UserRepository.getUserById(user_id)

        if not existing_user:
            return None  # User does not exist

        # Apply updates to existing user
        updated_user_data = {**existing_user, **user_data}

        # Filter the allowed fields to prevent unauthorized changes
        allowed_fields = {
            "max_processes_per_user",
            "max_parallel_jobs_per_user",
            "max_jobs_in_queue",
            "max_memory_usage_per_user_per_cluster",
            "max_memory_usage_per_process",
            "max_allowed_nodes",
            "max_job_time",
            "username",
            "email",
            "rights"
        }

        filtered_update = {key: value for key, value in updated_user_data.items() if key in allowed_fields}

        # Update the user in the repository
        UserRepository.updateUser(user_id, filtered_update)

        return filtered_update

    @staticmethod
    def suspendUser(user_id: str, suspend_time: int) -> dict:
        """Suspend a user by adding a suspension period."""
        existing_user = UserRepository.getUserById(user_id)

        if not existing_user:
            raise ValueError("User not found")

        # Get current suspensions or initialize an empty list
        suspensions = existing_user.get("suspensions", [])

        # Append a new suspension record
        suspensions.append({
            "start_date": datetime.utcnow().isoformat(),
            "suspend_time": suspend_time
        })

        # Update user data
        updated_user_data = {"suspensions": suspensions}
        UserRepository.updateUser(user_id, updated_user_data)

        return {**existing_user, **updated_user_data}

