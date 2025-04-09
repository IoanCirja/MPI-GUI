from datetime import datetime
import jwt
from fastapi import APIRouter, HTTPException, Request
from AuthService.App.Services.AuthService import UserService, env

user_router = APIRouter()




@user_router.get("/users/quotas")
async def get_quotas(request: Request):
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

        quotas = UserService.getQuotas()

        return {"quotas": quotas}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve userff: {str(e)}")
