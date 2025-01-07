from fastapi import APIRouter, HTTPException, Request

from AuthService.App.DTOs.LoginRequest import LoginRequest
from AuthService.App.DTOs.SignUpRequest import SignUpResponse, SignUpRequest
from AuthService.App.Services.AuthService import UserService

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
