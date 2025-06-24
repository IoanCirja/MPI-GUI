import asyncio

from fastapi import APIRouter, Depends, HTTPException
from starlette import websockets, status
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketDisconnect

from AuthService.App.Utils.JWTUtils import get_token_from_header
from Gateway.App.Services.Service import forward_request

router = APIRouter()
AUTH_SERVICE_URL = "http://localhost:8001/api"
JOB_SERVICE_URL = "http://localhost:8002/api"
JOB_SERVICE_WS_URL = "ws://localhost:8002/api/ws"

@router.post("/signup/")
async def signup(request: Request):
    try:
        return await forward_request(request, f"{AUTH_SERVICE_URL}/signup/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")
@router.post("/login/")
async def login(request: Request):
    try:
        return await forward_request(request, f"{AUTH_SERVICE_URL}/login/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")

@router.get("/profile/")
async def profile(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{AUTH_SERVICE_URL}/profile/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")


@router.get("/users/quotas")
async def get_quotas(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{AUTH_SERVICE_URL}/users/quotas")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action Failed: {e}"
        )

@router.get("/users/quota")
async def get_my_quota(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{AUTH_SERVICE_URL}/users/quota")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action Failed: {e}"
        )

@router.get("/admin/users/")
async def admin_list_users(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        return await forward_request(request, f"{AUTH_SERVICE_URL}/admin/users/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action Failed: {e}"
        )

@router.post("/admin/suspend/")
async def admin_suspend_user(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        return await forward_request(request, f"{AUTH_SERVICE_URL}/admin/suspend/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action Failed: {e}"
        )

@router.patch("/admin/users/")
async def admin_bulk_update(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        return await forward_request(request, f"{AUTH_SERVICE_URL}/admin/users/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action Failed: {e}"
        )

@router.get("/admin/suspensions/")
async def admin_list_suspensions(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        return await forward_request(request, f"{AUTH_SERVICE_URL}/admin/suspensions/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action Failed: {e}"
        )

@router.delete("/admin/suspensions/")
async def admin_remove_suspension(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        if decoded_token.get("rights") != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        return await forward_request(request, f"{AUTH_SERVICE_URL}/admin/suspensions/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action Failed: {e}"
        )

#####jobs
@router.post("/upload/")
async def upload(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{JOB_SERVICE_URL}/upload/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")

@router.get("/jobs/")
async def jobs(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")

@router.post("/jobs/{job_id}/kill")
async def kill_job(
    request: Request,
    job_id: str,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/{job_id}/kill")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")

@router.delete("/jobs/")
async def clear_all_jobs(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")

@router.delete("/jobs/{job_id}")
async def clear_job(
    request: Request,
    job_id: str,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/{job_id}")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")

@router.get("/jobs/admin")
async def get_all_jobs_admin(
    request: Request,
    decoded_token: dict = Depends(get_token_from_header),
):
    try:
        return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/admin")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Action Failed: {str(e)}")