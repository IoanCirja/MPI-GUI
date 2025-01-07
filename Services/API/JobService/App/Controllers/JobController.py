import asyncio
import tempfile
from typing import List
import vt
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Header, Depends, WebSocket, BackgroundTasks
from starlette.responses import FileResponse
from starlette.websockets import WebSocketDisconnect

from AuthService.App.Utils.JWTUtils import *
from JobService.App.DTOs.JobDTO import JobDTO
from JobService.App.Services.JobService import JobService
from JobService.App.Services.SSHService import SSHService
import os
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))
UPLOAD_DIRECTORY = "uploaded_files"
SSH_HOST = env('SSH_HOST')
SSH_PORT = env('SSH_PORT')
SSH_USERNAME = env('SSH_USERNAME')
SSH_PASSWORD = env('SSH_PASSWORD')
router = APIRouter()

vtClient = vt.Client(env('VT_API_KEY'))

uuuid = '-OFLnwLoJaCKPQk7HLeu'



os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scan_file_with_virustotal(file_content: bytes) -> int:
    try:
        logger.info("Starting file scan...")

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        with open(tmp_file_path, 'rb') as tmp_file_obj:
            scan_response = vtClient.scan_file(tmp_file_obj)

            if not scan_response or not scan_response.id:
                raise HTTPException(status_code=500, detail="Failed to upload file to VirusTotal.")

            file_id = scan_response.id
            logger.info(f"File uploaded to VirusTotal with ID: {file_id}")

        file_report = vtClient.get_object(f"/files/{file_id}")

        if not file_report:
            raise HTTPException(status_code=404, detail=f"File report not found for ID: {file_id}")

        malicious_count = file_report.last_analysis_stats.get("malicious", 0)
        logger.info(f"Scan result: {malicious_count} malicious findings.")

        return malicious_count

    except Exception as e:
        logger.error(f"VirusTotal scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"VirusTotal scan failed: {str(e)}")


def get_token_from_header(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid token format")

    token = authorization[7:]
    return token


active_connections = []

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

def notify_frontend(job_id: str, status: str, output: str):
    for connection in active_connections:
        asyncio.create_task(
            connection.send_json({"jobId": job_id, "status": status, "output": output})
        )

async def execute_job_in_background(job_id: str, file_path: str, host_path: str, filename: str, hostname: str, user_id: str, numProcesses: int, allowOverSubscription: bool):
    try:
        
        ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
        ssh_service.connect()

        remote_path_exe = f"/home/mpi.cluster/mpi-apps-ioan/{filename}"
        remote_path_host = f"/home/mpi.cluster/mpi-apps-ioan/{hostname}"

        
        await asyncio.to_thread(ssh_service.upload_file, file_path, remote_path_exe)
        await asyncio.to_thread(ssh_service.upload_file, host_path, remote_path_host)

        oversubscribe_flag = "--oversubscribe" if allowOverSubscription else ""
        mpirun_command = f"mpirun -hostfile {remote_path_host} -np {numProcesses} {remote_path_exe} {oversubscribe_flag}"

        
        await asyncio.to_thread(ssh_service.send_file_to_hosts, file_path, host_path)

        
        output = await asyncio.to_thread(ssh_service.execute_command, mpirun_command, remote_path_exe, remote_path_host)

        if not output:
            output = "No output from mpirun, please check the command execution or file permissions."
        
        job_service = JobService(user_id)
        job_data = job_service.get_job_by_id(job_id)
        job_data.output = output
        job_data.status = "completed"
        job_service.update_job_status_and_output(job_id, job_data)

        
        notify_frontend(job_id, job_data.status, job_data.output)

    except Exception as e:
        
        job_service = JobService(user_id)
        job_data = job_service.get_job_by_id(job_id)
        job_data.status = "failed"
        job_data.output = str(e)
        job_service.update_job_status_and_output(job_id, job_data)

        
        notify_frontend(job_id, job_data.status, job_data.output)
@router.post("/upload/")
async def upload_file(
    background_tasks: BackgroundTasks,
    jobName: str = Form(...),
    file: UploadFile = File(...),
    hostfile: UploadFile = File(...),
    jobDescription: str = Form(...),
    lastExecutionTime: str = Form(...),
    numProcesses: int = Form(...),
    allowOverSubscription: bool = Form(...),
    token: str = Depends(get_token_from_header),
):
    try:
        if not (file.filename.endswith(".exe") or file.filename.endswith(".cpp")):
            raise HTTPException(status_code=400, detail="Only .exe or .cpp files are allowed!")

        decoded_token = verifyAccessToken(token)
        userId = decoded_token["sub"]

        content = await file.read()
        host_content = await hostfile.read()

        numProcesses = int(numProcesses)
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as f:
            f.write(content)

        host_path = os.path.join(UPLOAD_DIRECTORY, hostfile.filename)
        with open(host_path, "wb") as f:
            f.write(host_content)


        remote_path_exe = f"/home/mpi.cluster/mpi-apps-ioan/{file.filename}"
        remote_path_host = f"/home/mpi.cluster/mpi-apps-ioan/{hostfile.filename}"

        oversubscribe_flag = "--oversubscribe" if allowOverSubscription else ""
        mpirun_command = f"mpirun -hostfile {remote_path_host}   -np {numProcesses} {remote_path_exe} {oversubscribe_flag}"

        
        job_service = JobService(userId)
        job_data = JobDTO(
            jobName=jobName,
            jobDescription=jobDescription,
            lastExecutionDate=lastExecutionTime,
            numProcesses=numProcesses,
            allowOverSubscription=allowOverSubscription,
            file=file.filename,
            hostfile=hostfile.filename,
            command=mpirun_command,
            output="",
            status="pending"
        )
        job_id = job_service.create_and_save_job(job_data, content, host_content, mpirun_command)

        
        background_tasks.add_task(execute_job_in_background,job_id, file_path, host_path, file.filename, hostfile.filename, userId, numProcesses, allowOverSubscription)

        return {"jobId": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file and execute command: {str(e)}")



@router.get('/jobs/', response_model=List[JobDTO])
async def get_job_details(
                          token: str = Depends(get_token_from_header)
                          ):
    decoded_token = verifyAccessToken(token)  
    userId = decoded_token["sub"]
    try:
        
        job_service = JobService(userId)  

        
        job_data = job_service.get_all_jobs()

        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")

        
        return job_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")
@router.get("/download/")
async def download_file_from_ssh(remote_file_path: str):
    try:
        local_file_path = os.path.join(UPLOAD_DIRECTORY, os.path.basename(remote_file_path))

        ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
        ssh_service.connect()

        ssh_service.download_file(remote_file_path, local_file_path)

        ssh_service.close()

        return FileResponse(local_file_path, media_type="application/octet-stream", filename=os.path.basename(remote_file_path))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@router.get('/jobs/{job_id}', response_model=JobDTO)
async def get_job_details(job_id: str,
                          token: str = Depends(get_token_from_header)
                          ):
    decoded_token = verifyAccessToken(token)  
    userId = decoded_token["sub"]

    try:
        
        job_service = JobService(userId)  

        
        job_data = job_service.get_job_by_id(job_id)

        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")

        
        return job_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")


@router.post("/uploadsss/")
async def upload_file(jobName: str = Form(...),
                      file: UploadFile = File(...),
                      hostfile: UploadFile = File(...),
                      jobDescription: str = Form(...),
                      lastExecutionTime: str = Form(...),
                      numProcesses: int = Form(...),
                      allowOverSubscription: bool = Form(...),
                      token: str = Depends(get_token_from_header)
                      ):


    try:
        if not (file.filename.endswith(".exe") or file.filename.endswith(".cpp")):
            raise HTTPException(status_code=400, detail="Only .exe or .cpp files are allowed!")



        decoded_token = verifyAccessToken(token)  
        userId = decoded_token["sub"]

        
        

        
            

        content = await file.read()
        host_content = await hostfile.read()

        numProcesses = int(numProcesses)
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as f:
            f.write(content)

        host_path = os.path.join(UPLOAD_DIRECTORY, hostfile.filename)
        with open(host_path, "wb") as f:
            f.write(host_content)




        ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
        ssh_service.connect()

        remote_path_exe = f"/home/mpi.cluster/mpi-apps-ioan/{file.filename}"
        remote_path_host = f"/home/mpi.cluster/mpi-apps-ioan/{hostfile.filename}"

        ssh_service.upload_file(file_path, remote_path_exe)
        ssh_service.upload_file(host_path, remote_path_host)

        oversubscribe_flag = "--oversubscribe" if allowOverSubscription else ""
        mpirun_command = f"mpirun -hostfile {remote_path_host}   -np {numProcesses} {remote_path_exe} {oversubscribe_flag}"
        logger.info(f"Executing MPI command: {mpirun_command}")
        ssh_service.send_file_to_hosts(local_file=file_path, hostfile_path=host_path)

        output = ssh_service.execute_command(mpirun_command, remote_path_exe, remote_path_host)

        if not output:
            output = "No output from mpirun, please check the command execution or file permissions."
        job_service = JobService(userId)
        job_data = JobDTO(
            jobName=jobName,
            jobDescription=jobDescription,
            lastExecutionDate=lastExecutionTime,
            numProcesses=numProcesses,
            allowOverSubscription=allowOverSubscription,
            file=file.filename,
            hostfile=hostfile.filename,
            command=mpirun_command,
            output=output,
            status='pending'
        )

        
        job_id = job_service.create_and_save_job(job_data, content, host_content, mpirun_command)
        
        ssh_service.close()

        return {"jobId": job_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file and execute command: {str(e)}")


