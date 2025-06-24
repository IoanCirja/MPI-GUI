from fastapi import APIRouter, HTTPException, Depends
from starlette import status

from AuthService.App.Services.AuthService import UserService
from AuthService.App.Utils.JWTUtils import get_token_from_header

user_router = APIRouter()

@user_router.get("/users/quotas")
async def get_quotas(decoded_token: dict = Depends(get_token_from_header)):
    try:
        quotas = UserService.getQuotas()
        return {"quotas": quotas}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")


@user_router.get("/users/quota")
async def get_my_quotas(decoded_token: dict = Depends(get_token_from_header)):
    try:
        user_id = decoded_token.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        quotas = UserService.getUserByIdforQuota(user_id)
        if not quotas:
            raise HTTPException(status_code=404, detail="User quotas not found")

        return quotas

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")
