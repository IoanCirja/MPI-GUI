import asyncio
import os
import re
import smtplib
import tempfile
import uuid
from datetime import datetime
from email.message import EmailMessage
from typing import List
import base64
import logging
import requests


from decouple import RepositoryEnv, Config
from starlette.exceptions import HTTPException

from JobService.App.DTOs.JobDTO import JobDTO
from JobService.App.DTOs.JobUploadDTO import JobUploadDTO
from JobService.App.Repositories.JobRepository import JobRepository
from JobService.App.Services.SSHService import SSHService
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))

UPLOAD_DIRECTORY = "uploaded_files"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

BASE_DIRECTORY = env('BASE_DIRECTORY')

SSH_HOST = env('SSH_HOST')
SSH_PORT = env('SSH_PORT')
SSH_USERNAME = env('SSH_USERNAME')
SSH_PASSWORD = env('SSH_PASSWORD')

active_connections = []
active_tcp_comm_node_ports = {}

vtKey = env('VT_API_KEY')
VT_UPLOAD_URL = "https://www.virustotal.com/api/v3/files"
VT_ANALYSIS_URL = "https://www.virustotal.com/api/v3/analyses/{}"

class JobService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.repository = JobRepository(user_id)

    def allocate_port_range(self, job_id: str) -> str:
        try:
            global active_tcp_comm_node_ports
            start_port = 12000
            end_port = 30000
            port_range_size = 20

            for port in range(start_port, end_port, port_range_size):
                port_range = f"{port}-{port + port_range_size - 1}"
                if port_range not in active_tcp_comm_node_ports.values():
                    active_tcp_comm_node_ports[job_id] = port_range
                    return port_range

            raise Exception("Service Error: No available ports. Please try again later.")
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def release_port_range(self, job_id: str):
        try:
            global active_tcp_comm_node_ports
            if job_id in active_tcp_comm_node_ports:
                del active_tcp_comm_node_ports[job_id]
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def validate_environment_vars(self, environmentVars: str) -> str:
        try:
            env_vars_list = []
            if environmentVars.strip():
                env_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=[^;&|$()<>`]+$")
                for env_var in environmentVars.split(","):
                    env_var = env_var.strip()
                    if not env_pattern.match(env_var):
                        raise Exception(f"Service Error: Invalid environment variable: {env_var}")
                    env_vars_list.append(f"-x {env_var}")
            return " ".join(env_vars_list)
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def create_and_save_job(self, job_data: JobUploadDTO) -> str:
        try:
            job_id = str(uuid.uuid4())
            beginDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            job = JobDTO(
                id=job_id,
                jobName=job_data.jobName,
                jobDescription=job_data.jobDescription,
                beginDate=beginDate,
                endDate="",
                fileName=job_data.fileName,
                fileContent=job_data.fileContent,
                hostFile=job_data.hostFile,
                hostNumber=job_data.hostNumber,
                numProcesses=job_data.numProcesses,
                allowOverSubscription=job_data.allowOverSubscription,
                environmentVars=job_data.environmentVars,
                displayMap=job_data.displayMap,
                rankBy=job_data.rankBy,
                mapBy=job_data.mapBy,
                status="pending",
                output="",
                alertOnFinish=job_data.alertOnFinish,
                user_id=job_data.user_id,
                userEmail=job_data.userEmail,
            )

            self.repository.insert_job(job)
            return job_id

        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def get_job_by_id(self, job_id: str):
        try:
            job_data = self.repository.get_job_by_id(job_id)
            if job_data:
                return JobDTO(**job_data)
            return None
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def compute_cluster_usage(self):
        try:
            return self.repository.compute_cluster_usage()
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def compute_request_usage(self):
        try:
            return self.repository.compute_request_usage()
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def update_job_status_and_output(self, job_id: str, job_data: JobDTO):
        try:
            updated_data = {
                "status": job_data.status,
                "output": job_data.output,
                "endDate": job_data.endDate,
            }
            success = self.repository.update_job(job_id, updated_data)
            return success
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def notify_frontend(self, job_id: str, status: str, output: str, endDate: str) -> None:
        try:
            for connection in active_connections:
                asyncio.create_task(
                    connection.send_json({
                        "jobId": job_id,
                        "status": status,
                        "output": output,
                        "endDate": endDate
                    })
                )
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def clear_jobs_on_cluster(self, jobId: str = None):
        try:
            ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
            ssh_service.connect()
            await ssh_service.clear_jobs_in_background(jobId)
        except Exception as e:
            raise Exception(f"Service Error: {e}")


    async def update_quota_data(self, quota_data: dict):
        try:
            self.repository.update_quota(quota_data)
        except Exception as e:
            raise Exception(f"Service Error: {e}")
    async def get_quotas(self):
        try:
            return self.repository.get_quotas()
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def send_job_status_email(self, job_id: str, job_data_db):
        smtp_email = env("SMTP_EMAIL")
        smtp_password = env("SMTP_PASSWORD")
        smtp_server = env("SMTP_SERVER")
        smtp_port = 587

        if not smtp_email or not smtp_password or not smtp_server:
            raise ValueError("SMTP configuration is missing in environment variables.")

        subject = f"[Job Status: {job_data_db.status.upper()}"
        body = f"""
        Hello,

        This is an automated message from the MPI Launcher Job Processing System.

        Your submitted job has completed processing. Below are the execution details:

        ────────────────────────────────────────
        🧾 Job Details
        ────────────────────────────────────────
        Job ID      : {job_id}
        Job Name    : {job_data_db.jobName}
        Status      : {job_data_db.status.upper()}
        Start Time  : {job_data_db.beginDate or 'N/A'}
        End Time    : {job_data_db.endDate or 'N/A'}

        ────────────────────────────────────────
        📄 Job Output
        ────────────────────────────────────────
        {job_data_db.output or 'No output was produced during execution.'}

        ────────────────────────────────────────
        📬 Notes
        ────────────────────────────────────────
        - If the job status is "FAILED", please check the output section for error details.
        - If the job was terminated manually, the status will show as "KILLED".

        Thank you for using MPI Launcher.

        Best regards,  
        MPI Launcher Job Processing System
        """

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_email
        msg["To"] = job_data_db.userEmail
        msg.set_content(body)

        try:
            logger.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.ehlo()
                server.starttls()
                logger.info("Starting TLS encryption.")
                server.login(smtp_email, smtp_password)
                logger.info(f"Logged in as {smtp_email}. Sending email...")
                server.send_message(msg)
                logger.info("Email sent successfully.")
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def execute_job_in_background(self, job_id: str, job_data: JobUploadDTO, timeout: int):
        temp_exe_path = None
        temp_hostfile_path = None
        try:
            updated_data = {
                "status": 'running',
                "output": '',
                "endDate": '',
            }
            success = self.repository.update_job(job_id, updated_data)
            if success:
                self.notify_frontend(job_id, 'running', '', '')

                ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
                ssh_service.connect()

                port_range = self.allocate_port_range(job_id)

                remote_job_dir = f"{BASE_DIRECTORY}/job_{job_id}"
                remote_path_exe = f"{remote_job_dir}/job_{job_id}.exe"
                remote_path_host = f"{remote_job_dir}/hostfile_{job_id}.txt"
                remote_pid_path = f"{remote_job_dir}/pid_{job_id}.txt"
                output_path = f"{BASE_DIRECTORY}/job_{job_id}/output_{job_id}"

                env_vars_str = self.validate_environment_vars(job_data.environmentVars)

                with tempfile.NamedTemporaryFile(delete=False) as temp_exe:
                    temp_exe.write(base64.b64decode(job_data.fileContent.encode('utf-8')))
                    temp_exe.flush()

                correct_exe_path = os.path.join(os.path.dirname(temp_exe.name), f"job_{job_id}.exe")
                if os.path.exists(correct_exe_path):
                    os.remove(correct_exe_path)

                os.rename(temp_exe.name, correct_exe_path)
                temp_exe_path = correct_exe_path

                # scan_result = self.scan_file_with_virustotal(temp_exe_path)
                # if scan_result != 0:
                #     raise Exception("File flagged by VirusTotal")

                with tempfile.NamedTemporaryFile(delete=False) as temp_hostfile:
                    temp_hostfile.write(base64.b64decode(job_data.hostFile.encode('utf-8')))
                    temp_hostfile.flush()

                correct_hostfile_path = os.path.join(os.path.dirname(temp_hostfile.name), f"hostfile_{job_id}.txt")
                if os.path.exists(correct_hostfile_path):
                    os.remove(correct_hostfile_path)
                os.rename(temp_hostfile.name, correct_hostfile_path)
                temp_hostfile_path = correct_hostfile_path

                await ssh_service.send_file_to_hosts(job_id, temp_exe_path, temp_hostfile_path)

                mpirun_command = f"mpirun {env_vars_str if env_vars_str else ''} -hostfile {remote_path_host} -np {job_data.numProcesses} --mca oob_tcp_dynamic_ipv4_ports {port_range} --report-pid {remote_pid_path} --output-filename {output_path}"

                if job_data.mapBy:
                    mpirun_command += f" --map-by {job_data.mapBy}"
                if job_data.rankBy:
                    mpirun_command += f" --rank-by {job_data.rankBy}"
                if job_data.displayMap:
                    mpirun_command += " --display-map"
                if job_data.allowOverSubscription:
                    mpirun_command += " --oversubscribe"

                mpirun_command += f" {remote_path_exe}"

                try:
                    output = await asyncio.wait_for(
                        asyncio.to_thread(ssh_service.execute_command, mpirun_command, remote_path_exe, remote_path_host),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    job_data_db = self.get_job_by_id(job_id)
                    job_data_db.endDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    job_data_db.status = "failed"
                    job_data_db.output = f"Job execution timed out."
                    await self.kill_job_in_background(job_id)

                    self.update_job_status_and_output(job_id, job_data_db)
                    self.notify_frontend(job_id, job_data_db.status, job_data_db.output, job_data_db.endDate)
                    if job_data.alertOnFinish:
                        self.send_job_status_email(job_id, job_data_db)
                    return

                job_data_db = self.get_job_by_id(job_id)
                if job_data_db.status != "killed":
                    job_data_db.endDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    job_data_db.output = output
                    job_data_db.status = "completed"

                    self.update_job_status_and_output(job_id, job_data_db)
                    self.notify_frontend(job_id, job_data_db.status, job_data_db.output, job_data_db.endDate)
                    if job_data.alertOnFinish:
                        self.send_job_status_email(job_id, job_data_db)

        except Exception as e:
            job_data_db = self.get_job_by_id(job_id)

            job_data_db.status = "failed"
            job_data_db.output = str(e)

            self.update_job_status_and_output(job_id, job_data_db)

            self.notify_frontend(job_id, job_data_db.status, job_data_db.output, job_data_db.endDate)
            if job_data.alertOnFinish:
                self.send_job_status_email(job_id, job_data_db)
        finally:
            if temp_exe_path and os.path.exists(temp_exe_path):
                os.remove(temp_exe_path)
            if temp_hostfile_path and os.path.exists(temp_hostfile_path):
                os.remove(temp_hostfile_path)
            self.release_port_range(job_id)

    async def kill_job_in_background(self, job_id: str):
        try:
            job_data_db = self.get_job_by_id(job_id)
            if job_data_db and job_data_db.status == "pending":
                job_data_db.status = "killed"
                job_data_db.output = "Job was killed before it started."
                job_data_db.endDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.update_job_status_and_output(job_id, job_data_db)
                self.notify_frontend(job_id, job_data_db.status, job_data_db.output, job_data_db.endDate)
                return

            ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
            ssh_service.connect()

            success = await ssh_service.request_kill(job_id)

            if success:
                job_data_db.status = "killed"
                job_data_db.output = "Job was successfully killed."
                job_data_db.endDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


                self.update_job_status_and_output(job_id, job_data_db)
                self.notify_frontend(job_id, job_data_db.status, job_data_db.output, job_data_db.endDate)

        except Exception as e:
            job_data_db = self.get_job_by_id(job_id)
            job_data_db.status = "failed"
            job_data_db.output = f"Error killing job: {str(e)}"

            self.update_job_status_and_output(job_id, job_data_db)

            self.notify_frontend(job_id, job_data_db.status, job_data_db.output, job_data_db.endDate)

        finally:
            if ssh_service:
                ssh_service.close()


    def scan_file_with_virustotal(self, path: str) -> int:
        headers = {"x-apikey": vtKey}

        with open(path, "rb") as file:
            files = {"file": (os.path.basename(path), file, "application/x-msdownload")}
            logger.info("Uploading file to VirusTotal...")
            response = requests.post(VT_UPLOAD_URL, headers=headers, files=files)

        if response.status_code not in [200, 201]:
            logger.error(f"File upload failed: {response.status_code}")
            raise HTTPException(status_code=500, detail="VirusTotal upload failed")

        analysis_id = response.json().get("data", {}).get("id")
        if not analysis_id:
            raise HTTPException(status_code=500, detail="VirusTotal analysis ID missing")

        return self.get_analysis_report(analysis_id)

    def get_analysis_report(self, analysis_id: str) -> int:
        headers = {"x-apikey": vtKey}
        url = VT_ANALYSIS_URL.format(analysis_id)

        logger.info("Waiting for scan results...")
        while True:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error("Failed to fetch VirusTotal report.")
                raise HTTPException(status_code=500, detail="VirusTotal report fetch failed")

            data = response.json()
            if "data" in data and "attributes" in data["data"]:
                stats = data["data"]["attributes"]["stats"]

                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                undetected = stats.get("undetected", 0)

                logger.info(f"Scan Results - undetected: {undetected}, Suspicious: {suspicious}")
                if malicious > 0:
                    return 1
                elif suspicious > 0:
                    return 2
                else:
                    return 0

    async def get_pending_jobs_for_user(self):
        try:
            pending_jobs = self.repository.get_pending_jobs_for_user()
            return pending_jobs
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def get_running_jobs_for_user(self):
        try:
            running_jobs = self.repository.get_running_jobs_for_user()
            return running_jobs
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def get_all_pending_jobs(self):
        try:
            pending_jobs = self.repository.get_all_pending_jobs()
            return pending_jobs
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    async def get_all_running_jobs(self):
        try:
            pending_jobs = self.repository.get_all_running_jobs()
            return pending_jobs
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def get_all_jobs(self) -> List[JobDTO]:
        try:
            jobs_data = self.repository.get_all_jobs()
            if not jobs_data:
                return []

            return [JobDTO(**job) for job in jobs_data]
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def get_all_jobs_for_user(self) -> List[JobDTO]:
        try:
            jobs_data = self.repository.get_all_jobs_for_user()
            if not jobs_data:
                return []

            return [JobDTO(**job) for job in jobs_data]
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def clear_jobs(self) -> List[str]:
        try:
            job_ids = self.repository.clear_jobs()
            if not job_ids:
                return []
            return job_ids
        except Exception as e:
            raise Exception(f"Service Error: {e}")

    def clear_job(self, job_id):
        try:
            success = self.repository.clear_job(job_id)
            return success
        except Exception as e:
            raise Exception(f"Service Error: {e}")
