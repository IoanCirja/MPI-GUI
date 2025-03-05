import os
import jwt
from datetime import datetime, timedelta
from decouple import RepositoryEnv, Config
from fastapi import HTTPException, Header, status

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
        payload = jwt.decode(token, env("SECRET_KEY"), algorithms=[env("ALGORITHM")])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_token_from_header(authorization: str = Header(...)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token not found"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token format"
        )

    token = authorization[7:]
    return verifyAccessToken(token)