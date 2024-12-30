import hashlib
import os
import jwt
from datetime import datetime, timedelta
import bcrypt

from decouple import RepositoryEnv, Config

from AuthService.App.DTOs.AuthDTOs import LoginRequest, CreateUserRequest
from AuthService.App.Repositories.AuthRepository import UserRepository

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))


def createAccessToken(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, env("SECRET_KEY"), algorithm=env("ALGORITHM"))
    return encoded_jwt


def verifyAccessToken(token: str):
    try:
        payload = jwt.decode(token, env("SECRET_KEY"), algorithms=[env("ALGORITHM"), ])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


class UserService:
    @staticmethod
    def loginUser(loginRequest: LoginRequest) -> str:
        userData = UserRepository.getUserByEmail(loginRequest.email)
        if not userData:
            raise ValueError("User does not exist")

        if not bcrypt.checkpw(loginRequest.password.encode('utf-8'), userData["password"].encode('utf-8')):
            raise ValueError("Invalid credentials")

        token_data = {"sub": userData["email"], "username": userData["username"]}
        token = createAccessToken(data=token_data)

        return token

    @staticmethod
    def createUser(createUserRequest: CreateUserRequest) -> dict:
        if createUserRequest.password != createUserRequest.retypePassword:
            raise ValueError("Passwords do not match")

        hashedPassword = bcrypt.hashpw(createUserRequest.password.encode('utf-8'), bcrypt.gensalt())

        data = {
            "username": createUserRequest.username,
            "email": createUserRequest.email,
            "password": hashedPassword.decode('utf-8')
        }

        user_data = UserRepository.addUser(data)
        return user_data
