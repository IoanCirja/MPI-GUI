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
            "exp": datetime.utcnow() + timedelta(hours=1),  # 1 minute expiration
            "jti": str(uuid.uuid4()),
            'username':userData["username"],
            'email': userData["email"],
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
            "salt": salt
        }

        UserRepository.addUser(data)
