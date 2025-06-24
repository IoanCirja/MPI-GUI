import asyncio

from fastapi import APIRouter
from starlette import websockets
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketDisconnect

from Gateway.App.Services.Service import forward_request

router = APIRouter()
AUTH_SERVICE_URL = "http://localhost:8001/api"
JOB_SERVICE_URL = "http://localhost:8002/api"
JOB_SERVICE_WS_URL = "ws://localhost:8002/api/ws"

@router.websocket("/ws")
async def websocket_proxy(websocket: WebSocket):

    await websocket.accept()

    try:
        async with websockets.connect(JOB_SERVICE_WS_URL) as ws:
            async def send_to_job_service():
                try:
                    while True:
                        message = await websocket.receive_text()
                        await ws.send(message)
                except WebSocketDisconnect:
                    pass

            async def receive_from_job_service():
                try:
                    while True:
                        message = await ws.recv()
                        await websocket.send_text(message)
                except WebSocketDisconnect:
                    pass

            await asyncio.gather(send_to_job_service(), receive_from_job_service())

    except Exception as e:
        await websocket.close()
        print(f"WebSocket Proxy Error: {e}")
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

@router.post("/jobs/{job_id}/kill")
async def kill_job(request: Request, job_id: str):
    return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/{job_id}/kill")

@router.delete("/jobs/")
async def clear_all_jobs(request: Request):
    return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/")

@router.delete("/jobs/{job_id}")
async def clear_job(request: Request, job_id: str):
    return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/{job_id}")

@router.get("/jobs/admin")
async def get_all_jobs_admin(request: Request):
    return await forward_request(request, f"{JOB_SERVICE_URL}/jobs/admin")