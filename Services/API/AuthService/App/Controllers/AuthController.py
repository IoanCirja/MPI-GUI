from fastapi import APIRouter, HTTPException, Request, Depends
from starlette import status

from AuthService.App.DTOs.LoginRequest import LoginRequest
from AuthService.App.DTOs.SignUpRequest import SignUpRequest
from AuthService.App.Services.AuthService import UserService, env
from AuthService.App.Utils.JWTUtils import get_token_from_header

router = APIRouter()

@router.post("/signup/")
async def add_user(request: SignUpRequest):
    try:
        UserService.createUser(request)
        return {"message": "User created successfully"}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")


@router.post("/login/")
async def loginUser(loginRequest: LoginRequest, request: Request):
    try:
        token = UserService.loginUser(loginRequest, str(request.base_url).rstrip("/"))
        return {"token": token}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")


@router.get("/profile/")
async def get_user_profile(
        request: Request,
        decoded_token: dict = Depends(get_token_from_header)
):
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(" ")[1] if "Bearer " in auth_header else None
    try:
        user_data = {
            "token": token,
            "username": decoded_token["username"],
            "email": decoded_token["email"],
            "rights": decoded_token["rights"]
        }
        return user_data

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")
