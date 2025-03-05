from fastapi import APIRouter
from starlette.requests import Request

from Gateway.App.Services.Service import forward_request

router = APIRouter()
AUTH_SERVICE_URL = "http://localhost:8001/api"
JOB_SERVICE_URL = "http://localhost:8002/api"


@router.post("/signup/")
async def signup(request: Request):
    return await forward_request(request, f"{AUTH_SERVICE_URL}/signup/")

@router.post("/login/")
async def login(request: Request):
    return await forward_request(request, f"{AUTH_SERVICE_URL}/login/")

@router.get("/profile/")
async def profile(request: Request):
    return await forward_request(request, f"{AUTH_SERVICE_URL}/profile/")

@router.post("/upload/")
async def upload(request: Request):
    return await forward_request(request, f"{JOB_SERVICE_URL}/upload/")

@router.get("/jobs/")
async def jobs(request: Request):
    return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/")

@router.get("/jobs/{job_id}")
async def job_details(request: Request, job_id: str):
    return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/{job_id}")

@router.post("/jobs/{job_id}/kill")
async def kill_job(request: Request, job_id: str):
    return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/{job_id}/kill")
