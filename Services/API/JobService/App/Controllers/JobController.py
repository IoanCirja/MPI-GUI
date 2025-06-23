import base64
from typing import List

import httpx
from fastapi import APIRouter, Depends, WebSocket, BackgroundTasks, Body
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from JobService.App.Utils.JWTUtils import *
from JobService.App.DTOs.JobUploadDTO import JobUploadDTO
from JobService.App.DTOs.JobDTO import JobDTO
from JobService.App.DTOs.UserJobDTO import UserJobDTO
from JobService.App.Services.JobService import JobService, active_connections

AUTH_SERVICE_URL = f"http://localhost:8001/api/users/quotas"
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def get_quota_data(token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(AUTH_SERVICE_URL, headers=headers)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return response.json()


@router.post("/upload/", response_model=dict)
async def upload_file(
        upload_dto: UserJobDTO = Body(...),
        decoded_token: str = Depends(get_token_from_header),
        authorization: str = Header(...),
        content_type: str = Header(..., alias="Content-Type"),
):
    try:
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Content-Type must be application/json"
            )

        if not upload_dto.fileName.endswith(".exe"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only .exe files are allowed!")

        user_id = decoded_token["sub"]
        user_email = decoded_token["email"]
        job_service = JobService(user_id)

        job_data = JobUploadDTO(
            **upload_dto.dict(),
            user_id=user_id,
            userEmail=user_email
        )

        token = authorization[7:]
        quotas = await get_quota_data(token)
        quotas_for_user = quotas['quotas'].get(user_id)
        if quotas_for_user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No quota record found for this user!"
            )
        await job_service.update_quota_data(quotas)

        job_history_for_user = job_service.get_all_jobs_for_user()
        running_jobs_for_user = await job_service.get_running_jobs_for_user()
        pending_jobs_for_user = await job_service.get_pending_jobs_for_user()

        if len(job_history_for_user) > int(quotas_for_user['max_total_jobs']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max total jobs limit reached!")

        if len(running_jobs_for_user) > int(quotas_for_user['max_running_jobs']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max running jobs limit reached!")

        if len(pending_jobs_for_user) > int(quotas_for_user['max_pending_jobs']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max pending jobs limit reached!")

        if job_data.numProcesses > int(quotas_for_user['max_processes_per_user']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Exceeded max processes per user!")

        node_request = {}
        encoded_hostfile = job_data.hostFile
        decoded_content = base64.b64decode(encoded_hostfile).decode("utf-8")
        lines = decoded_content.splitlines()

        if len(node_request) > int(quotas_for_user['max_nodes_per_job']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Exceeded max nodes per job!")

        for line in lines:
            parts = line.split()
            if len(parts) == 2 and "slots=" in parts[1]:
                node = parts[0]
                slots = int(parts[1].split("=")[1])
                node_request[node] = slots

        allowed_nodes = quotas_for_user['allowed_nodes'].strip().split(",")
        allowed_nodes_with_prefix = []

        for node in allowed_nodes:
            allowed_nodes_with_prefix.append(node.replace("C", "C05-", 1).strip())


        for node, slots in node_request.items():

            if slots > int(quotas_for_user['max_processes_per_node_per_user']):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Node {node} exceeds the max process count per node!")

            if node not in allowed_nodes_with_prefix:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Node {node} is not allowed!")

        job_id = await job_service.create_and_save_job(job_data)

        return {"jobId": job_id}

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Validation Error: {str(e)}")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")


@router.get('/jobs/', response_model=List[JobDTO])
async def get_job_details(
        decoded_token: str = Depends(get_token_from_header)
):
    try:
        userId = decoded_token["sub"]
        job_service = JobService(userId)
        job_data = job_service.get_all_jobs_for_user()

        return job_data

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")

@router.delete('/jobs/', response_model=dict)
async def clear_jobs(
        background_tasks: BackgroundTasks,
        decoded_token: str = Depends(get_token_from_header),
):
    try:
        user_id = decoded_token["sub"]
        job_service = JobService(user_id)

        all_jobs: List[JobDTO] = job_service.get_all_jobs_for_user()
        job_ids = [job.id for job in all_jobs]

        for job in all_jobs:
            if job.status == "running":
                background_tasks.add_task(job_service.kill_job_in_background, job.id)

        background_tasks.add_task(job_service.clear_jobs_on_cluster)
        background_tasks.add_task(job_service.clear_jobs)


        return {"jobIds": job_ids}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")


@router.delete('/jobs/{job_id}', response_model=dict)
async def clear_jobs(
        job_id: str,
        background_tasks: BackgroundTasks,
        decoded_token: str = Depends(get_token_from_header)
):
    try:
        user_id = decoded_token["sub"]
        job_service = JobService(user_id)

        job = job_service.get_job_by_id(job_id)

        if job and job.status == "running" and job_id:
            background_tasks.add_task(job_service.kill_job_in_background, job_id)

        background_tasks.add_task(job_service.clear_jobs_on_cluster, job_id)
        background_tasks.add_task(job_service.clear_job, job_id)
        return {"jobId": job_id}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")

@router.post("/jobs/{job_id}/kill", response_model=dict)
def kill_job(
        job_id: str,
        background_tasks: BackgroundTasks,
        decoded_token: str = Depends(get_token_from_header)
):
    try:
        user_id = decoded_token["sub"]
        job_service = JobService(user_id)
        job_data = job_service.get_job_by_id(job_id)

        if not job_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if job_data.status not in ["running", 'pending']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job is not currently available")

        background_tasks.add_task(job_service.kill_job_in_background, job_id)

        return {"jobId": job_id}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action Failed: {str(e)}")

@router.get("/jobs/admin", response_model=List[JobDTO])
async def get_all_jobs_admin(
    decoded_token: dict = Depends(get_token_from_header)
):
    if decoded_token.get("rights") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin rights required")
    user_id = decoded_token["sub"]
    job_service = JobService(user_id)
    all_jobs = job_service.get_all_jobs()
    return all_jobs

