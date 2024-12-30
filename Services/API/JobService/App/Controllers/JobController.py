import tempfile

import vt
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from decouple import RepositoryEnv, Config
from JobService.App.Services.SSHService import SSHService
import os


envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))
UPLOAD_DIRECTORY = "uploaded_files"
SSH_HOST = env('SSH_HOST')
SSH_PORT = env('SSH_PORT')
SSH_USERNAME = env('SSH_USERNAME')
SSH_PASSWORD = env('SSH_PASSWORD')
router = APIRouter()

vtClient = vt.Client(env('VT_API_KEY'))





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


@router.post("/upload/")
async def upload_file(numProcesses: int = Form(...), file: UploadFile = File(...)):
    try:
        if not (file.filename.endswith(".exe") or file.filename.endswith(".cpp")):
            raise HTTPException(status_code=400, detail="Only .exe or .cpp files are allowed!")

        content = await file.read()

        numProcesses = int(numProcesses)
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as f:
            f.write(content)

        print(f"Received num_processes: {numProcesses}")

        ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
        ssh_service.connect()

        remote_path = f"/home/mpi.cluster/mpi-apps-ioan/{file.filename}"
        ssh_service.upload_file(file_path, remote_path)

        mpirun_command = f"mpirun -np {numProcesses} {remote_path}"

        output = ssh_service.execute_command(mpirun_command, remote_path)

        if not output:
            output = "No output from mpirun, please check the command execution or file permissions."

        ssh_service.delete_file(remote_path)
        ssh_service.close()

        return {"message": f"File '{file.filename}' uploaded and executed successfully!",
                "file_path": file_path, "execution_output": output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file and execute command: {str(e)}")
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