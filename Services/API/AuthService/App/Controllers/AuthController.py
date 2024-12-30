from fastapi import APIRouter, HTTPException
from AuthService.App.DTOs.AuthDTOs import UserResponse, CreateUserRequest, LoginRequest
from AuthService.App.Services.AuthService import UserService
import logging


router = APIRouter()

@router.post("/users/", response_model=UserResponse)
async def add_user(request: CreateUserRequest):
    try:
        user_data = UserService.createUser(request)
        return UserResponse(username=user_data["username"], email=user_data["email"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add user: {str(e)}")

@router.post("/login/")
async def loginUser(request: LoginRequest):
    try:
        token = UserService.loginUser(request)
        return {"token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to login: {str(e)}")
