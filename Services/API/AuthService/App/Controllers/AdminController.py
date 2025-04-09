from datetime import datetime
import jwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from AuthService.App.Services.AuthService import UserService, env

admin_router = APIRouter()

@admin_router.get("/admin/users/")
async def get_all_users(request: Request):
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

        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        non_admin_users = UserService.getAllNonAdminUsers()

        return {"users": non_admin_users}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")

class SuspendUserRequest(BaseModel):
    user_id: str
    suspend_time: int

@admin_router.post("/admin/suspend/")
async def suspend_user(request: Request, suspend_request: SuspendUserRequest):

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

        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        # Call the service to handle user suspension
        updated_user = UserService.suspendUser(suspend_request.user_id, suspend_request.suspend_time)

        return {"message": "User suspended successfully", "user": updated_user}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suspend user: {str(e)}")


@admin_router.patch("/admin/users/")
async def bulk_update_users(request: Request):
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

        # Get the payload from the request
        payload = await request.json()
        updated_users = payload.get('users', [])

        if not updated_users:
            raise HTTPException(status_code=400, detail="No users to update")

        # Loop through users and apply updates
        for user in updated_users:
            user_id = user.get("id")
            if user_id:
                updated_user = UserService.updateUser(user_id, user)
                if not updated_user:
                    raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        return {"message": "Users updated successfully"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update users: {str(e)}")
