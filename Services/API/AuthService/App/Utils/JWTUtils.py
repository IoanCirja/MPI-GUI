import os
import jwt
from datetime import datetime, timedelta

from decouple import RepositoryEnv, Config


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

