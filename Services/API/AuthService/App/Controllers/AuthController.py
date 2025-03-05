from datetime import datetime

import jwt
from fastapi import APIRouter, HTTPException, Request

from AuthService.App.DTOs.LoginRequest import LoginRequest
from AuthService.App.DTOs.SignUpRequest import SignUpRequest
from AuthService.App.Services.AuthService import UserService, env

router = APIRouter()

@router.post("/signup/")
async def add_user(request: SignUpRequest):
    try:
        UserService.createUser(request)
        return {"message": "User created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add user: {str(e)}")

@router.post("/login/")
async def loginUser(loginRequest: LoginRequest, request: Request):
    try:
        token = UserService.loginUser(loginRequest, str(request.base_url).rstrip("/"))
        return {"token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to login: {str(e)}")


@router.get("/profile/")
async def get_user_profile(request: Request):
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        raise HTTPException(status_code=400, detail="Authorization header missing")

    token = auth_header.split(" ")[1] if "Bearer " in auth_header else None

    if not token:
        raise HTTPException(status_code=400, detail="Invalid token format")

    try:
        decoded_token = jwt.decode(token, key=env("SECRET_KEY"), algorithms=[env("ALGORITHM")])

        if datetime.utcnow() > datetime.utcfromtimestamp(decoded_token["exp"]):
            raise HTTPException(status_code=401, detail="Token has expired")

        user_data = {
            "token": token,
            "username": decoded_token["username"],
            "email": decoded_token["email"]
        }
        return user_data

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
