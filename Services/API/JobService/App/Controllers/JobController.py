import logging
from typing import List
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


@router.post("/upload/")
async def upload_file(
        background_tasks: BackgroundTasks,
        job_data: JobUploadDTO = Body(...),
        decoded_token: str = Depends(get_token_from_header),
):
    try:
        if not job_data.fileName.endswith(".exe"):
            logger.warning(f"Invalid file type: {job_data.fileName}. Only .exe files are allowed.")
            raise HTTPException(status_code=400, detail="Only .exe files are allowed!")

        userId = decoded_token["sub"]
        logger.info(f"User {userId} is attempting to upload a file: {job_data.fileName}")

        job_service = JobService(userId)

        pending_jobs_count = await job_service.get_pending_jobs_for_user()
        if pending_jobs_count > 3:
            logger.info(f"User {userId} already has {pending_jobs_count} pending job(s).")
            raise HTTPException(
                status_code=409,
                detail=f"You have reached your maximum allowed concurrent jobs. Please wait for finishing before submitting jobs."
            )
        job_id = await job_service.create_and_save_job(job_data)
        logger.info(f"Job {job_id} created for user {userId}.")

        background_tasks.add_task(job_service.execute_job_in_background, job_id, job_data)
        logger.info(f"Job {job_id} execution started in the background.")

        return {"jobId": job_id}

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Validation Error: {str(e)}")
    except HTTPException as e:
        logger.error(f"Failed to upload file and execute command for user {decoded_token['sub']}: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.get('/jobs/', response_model=List[JobDTO])
async def get_job_details(
        decoded_token: str = Depends(get_token_from_header)
):
    userId = decoded_token["sub"]
    try:
        job_service = JobService(userId)
        job_data = job_service.get_all_jobs()

        return job_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")

@router.get('/jobs/{job_id}', response_model=JobDTO)
async def get_job_details(job_id: str,
                          decoded_token: str = Depends(get_token_from_header)
                          ):
    userId = decoded_token["sub"]

    try:
        job_service = JobService(userId)
        job_data = job_service.get_job_by_id(job_id)

        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")

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

