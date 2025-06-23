from datetime import datetime
import jwt
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from AuthService.App.Services.AuthService import UserService, env
from AuthService.App.Utils.JWTUtils import get_token_from_header

user_router = APIRouter()

@user_router.get("/users/quotas")
async def get_quotas(decoded_token: dict = Depends(get_token_from_header)):
    try:
        quotas = UserService.getQuotas()
        return {"quotas": quotas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/users/quota")
async def get_my_quotas(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=400, detail="Authorization header missing")

    token = auth_header.split(" ")[1] if "Bearer " in auth_header else None

    if not token:
        raise HTTPException(status_code=400, detail="Invalid token format")

    try:
        decoded_token = jwt.decode(token, key=env("SECRET_KEY"), algorithms=[env("ALGORITHM")])

        if datetime.utcnow() > datetime.utcfromtimestamp(decoded_token["exp"]):
            raise HTTPException(status_code=401, detail="Token has expired")

        user_id = decoded_token.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        quotas = UserService.getUserByIdforQuota(user_id)
        if not quotas:
            raise HTTPException(status_code=404, detail="User quotas not found")

        return quotas

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user quotas: {str(e)}")


class UserIdRequest(BaseModel):
    id: str

@user_router.post("/users/email")
async def get_user_email_by_id(payload: UserIdRequest):
    try:
        user = UserService.getUserById(payload.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"email": user.get("email")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve email: {str(e)}")