from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from starlette import status

from AuthService.App.DTOs.RemoveSuspensionRequest import RemoveSuspensionRequest
from AuthService.App.Services.AuthService import UserService, env
from AuthService.App.Utils.JWTUtils import get_token_from_header

admin_router = APIRouter()
class SuspendUserRequest(BaseModel):
    user_id: str
    suspend_time: int

@admin_router.get("/admin/users/")
async def get_all_users(
        request: Request,
        decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        non_admin_users = UserService.getAllNonAdminUsers()
        return {"users": non_admin_users}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")

@admin_router.post("/admin/suspend/")
async def suspend_user(
        request: Request,
        suspend_request: SuspendUserRequest,
        decoded_token: dict = Depends(get_token_from_header),
):

    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        updated_user = UserService.suspendUser(suspend_request.user_id, suspend_request.suspend_time)

        return {"message": "User suspended successfully", "user": updated_user}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")


@admin_router.patch("/admin/users/")
async def bulk_update_users(
        request: Request,
        decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        payload = await request.json()
        updated_users = payload.get('users', [])

        if not updated_users:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users to update")

        for user in updated_users:
            user_id = user.get("id")
            if user_id:
                updated_user = UserService.updateUser(user_id, user)
                if not updated_user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

        return {"message": "Users updated successfully"}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")


@admin_router.get("/admin/suspensions/")
async def get_all_suspensions(
        request: Request,
        decoded_token: dict = Depends(get_token_from_header),
):

    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        all_users = UserService.getAllNonAdminUsers()
        suspensions = []

        for user in all_users:
            user_suspensions = user.get("suspensions", [])
            for suspension in user_suspensions:
                suspensions.append({
                    'id': suspension.get("id"),
                    "user_id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "start_date": suspension.get("start_date"),
                    "suspend_time": suspension.get("suspend_time")
                })

        return {"suspensions": suspensions}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")

@admin_router.delete("/admin/suspensions/")
async def remove_suspension(
        suspension: RemoveSuspensionRequest,
        request: Request,
        decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        success = UserService.removeSuspension(suspension.user_id, suspension.suspension_id)

        if not success:
            raise HTTPException(status_code=404, detail="Suspension not found or already removed")

        return {"message": "Suspension removed successfully"}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")
