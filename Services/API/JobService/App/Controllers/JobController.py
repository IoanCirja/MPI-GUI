import logging
from typing import List

import httpx
from fastapi import APIRouter, Depends, WebSocket, BackgroundTasks, Body
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from AuthService.App.Utils.JWTUtils import *
from JobService.App.DTOs.JobUploadDTO import JobUploadDTO
from JobService.App.DTOs.JobDTO import JobDTO
from JobService.App.Services.JobService import JobService, active_connections

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)



@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


AUTH_SERVICE_URL = "http://localhost:8001/api"

logging.basicConfig(level=logging.INFO)


async def get_quota_data(token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    logging.info(f"Sending request to http://localhost:8001/api/users/quotas")
    logging.info(f"Headers: {headers}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://localhost:8001/api/users/quotas", headers=headers)

        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Content: {response}")
        logging.info(f"Response Status Code: {response.status_code}")

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        elif response.status_code == 403:
            raise HTTPException(status_code=403, detail="Access denied")
        elif response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve user data")

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/")
async def upload_file(
        job_data: JobUploadDTO = Body(...),
        decoded_token: str = Depends(get_token_from_header),
        authorization: str = Header(...)
):
    try:
        if not job_data.fileName.endswith(".exe"):
            logger.warning(f"Invalid file type: {job_data.fileName}. Only .exe files are allowed.")
            raise HTTPException(status_code=400, detail="Only .exe files are allowed!")

        userId = decoded_token["sub"]
        logger.info(f"User {userId} is attempting to upload a file: {job_data.fileName}")

        job_service = JobService(userId)
        token = authorization[7:]

        quotas = await get_quota_data(token)
        await job_service.update_quota_data(quotas)



        job_id = await job_service.create_and_save_job(job_data)


        return {"jobId": job_id}

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Validation Error: {str(e)}")
    except HTTPException as e:
        logger.error(f"Failed to upload file and execute command for user {decoded_token['sub']}: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.delete('/jobs/', response_model=List[JobDTO])
async def clear_jobs(        background_tasks: BackgroundTasks
, decoded_token: str = Depends(get_token_from_header), ):
    user_id = decoded_token["sub"]
    try:
        job_service = JobService(user_id)
        if job_service.clear_jobs():
            background_tasks.add_task(job_service.clear_jobs_on_cluster)
            return []
        else:
            raise HTTPException(status_code=400, detail="Failed to clear jobs")


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear jobs: {str(e)}")


@router.delete('/jobs/{job_id}', response_model=List[JobDTO])
async def clear_jobs(
        job_id: str,
        background_tasks: BackgroundTasks,
        decoded_token: str = Depends(get_token_from_header)
):
    user_id = decoded_token["sub"]
    try:

        job_service = JobService(user_id)
        if job_service.clear_job(job_id):
            background_tasks.add_task(job_service.clear_jobs_on_cluster, job_id)
            return []
        else:
            raise HTTPException(status_code=400, detail="Failed to clear jobs")



    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear jobs: {str(e)}")


@router.get('/jobs/', response_model=List[JobDTO])
async def get_job_details(
        decoded_token: str = Depends(get_token_from_header)
):
    userId = decoded_token["sub"]
    try:
        job_service = JobService(userId)
        job_data = job_service.get_all_jobs_for_user()

        return job_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")


@router.post("/jobs/{job_id}/kill")
def kill_job(job_id: str, background_tasks: BackgroundTasks, decoded_token: str = Depends(get_token_from_header)):
    try:
        user_id = decoded_token["sub"]

        job_service = JobService(user_id)
        job_data = job_service.get_job_by_id(job_id)

        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")

        if job_data.status not in ["running", "pending"]:
            raise HTTPException(status_code=400, detail="Job is not currently running")


        background_tasks.add_task(job_service.kill_job_in_background, job_id)

        return {"message": "Process termination initiated", "jobId": job_id}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating job termination: {str(e)}")

