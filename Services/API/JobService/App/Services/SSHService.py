import asyncio
import asyncssh
import paramiko
import os
from decouple import RepositoryEnv, Config
from fastapi import HTTPException
import logging

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))

BASE_DIRECTORY = env('BASE_DIRECTORY')
SSH_HOST = env('SSH_HOST')
SSH_PORT = env('SSH_PORT')
SSH_USERNAME = env('SSH_USERNAME')
SSH_PASSWORD = env('SSH_PASSWORD')
MPI_HOSTS = env('MPI_HOSTS').split(',')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

master_node = "c05-00"


class SSHService:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.sftp = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            self.sftp = self.client.open_sftp()
        except Exception as e:
            raise Exception(f"SSH connection failed: {e}")

    def execute_command(self, command: str, remote_path_exe: str, remote_path_host:str):
        try:
            chmod_command = f"chmod +x {remote_path_exe}"
            stdin, stdout, stderr = self.client.exec_command(chmod_command)

            chmod_command = f"chmod +x {remote_path_host}"
            stdin, stdout, stderr = self.client.exec_command(chmod_command)

            stdin, stdout, stderr = self.client.exec_command(command)
            command_output = stdout.read().decode('utf-8')
            command_error = stderr.read().decode('utf-8')

            if command_error:
                raise Exception(f"Error executing command: {command_error}")

            return command_output
        except Exception as e:
            raise Exception(f"Error executing command: {str(e)}")

    async def send_file_to_host(self, fqdn, job_id, local_exe, local_hostfile):
        remote_job_dir = f"{BASE_DIRECTORY}/job_{job_id}"
        try:
            async with asyncssh.connect(fqdn, port=self.port, username=self.username, password=self.password, known_hosts=None) as conn:

                await conn.run(f"mkdir -p {remote_job_dir}", check=True)

                remote_exe_path = f"{remote_job_dir}/{os.path.basename(local_exe)}"
                await asyncssh.scp(local_exe, (conn, remote_exe_path))

                remote_hostfile_path = f"{remote_job_dir}/hostfile_{job_id}.txt"
                await asyncssh.scp(local_hostfile, (conn, remote_hostfile_path))

                await conn.run(f"chmod +x {remote_exe_path}", check=True)

        except Exception as e:
            raise Exception(f"Error sending files to {fqdn}: {str(e)}")

    async def send_file_to_hosts(self, job_id, local_exe, local_hostfile):
        try:
            with open(local_hostfile, 'r') as hostfile:
                hosts = [line.strip().split()[0] for line in hostfile if line.strip()]

            if not hosts:
                raise ValueError("Hostfile is empty or invalid!")

            if master_node not in hosts:
                hosts.insert(0, master_node)

            tasks = []
            for host in hosts:
                fqdn = f"{host.lower()}.cs.tuiasi.ro"
                tasks.append(self.send_file_to_host(fqdn, job_id, local_exe, local_hostfile))

            await asyncio.gather(*tasks)

        except Exception as e:
            raise Exception(f"Failed to send files to hosts: {str(e)}")


    async def request_kill(self, job_id: str):
        try:
            remote_job_dir = f"{BASE_DIRECTORY}/job_{job_id}"
            pid_file_path = f"{remote_job_dir}/pid_{job_id}.txt"

            try:
                self.sftp.stat(pid_file_path)
            except FileNotFoundError:
                logger.error(f"PID file not found for job {job_id}.")
                raise Exception("PID file not found.")

            with self.sftp.open(pid_file_path, 'r') as pid_file:
                pid = pid_file.read().decode('utf-8').strip()

            kill_command = f"kill -9 {pid}"
            logger.info(f"Attempting to kill process with PID {pid} for job {job_id}.")
            stdin, stdout, stderr = self.client.exec_command(kill_command)

            command_output = stdout.read().decode('utf-8')
            command_error = stderr.read().decode('utf-8')

            if command_error:
                logger.error(f"Error killing process: {command_error}")
                raise Exception(f"Error killing process: {command_error}")

            logger.info(f"Process with PID {pid} killed successfully for job {job_id}.")

            check_command = f"ps -p {pid}"
            stdin, stdout, stderr = self.client.exec_command(check_command)
            command_output = stdout.read().decode('utf-8')
            command_error = stderr.read().decode('utf-8')

            if pid not in command_output:
                logger.info(f"Process with PID {pid} is no longer running.")
                return True
            else:
                logger.error(f"Process with PID {pid} could not be killed.")
                return False

        except Exception as e:
            raise Exception(f"Error killing MPI process: {str(e)}")


    async def clear_jobs_in_background(self, jobId: str = None):
        try:
            ssh_service = SSHService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
            ssh_service.connect()

            tasks = []
            for host in MPI_HOSTS:
                tasks.append(self.clear_job_folders_on_node(host, jobId))

            await asyncio.gather(*tasks)
            return True
        except Exception as e:
            raise Exception(f"Error triggering background job clearing: {str(e)}")

    async def clear_job_folders_on_node(self, fqdn, jobId: str = None):
        try:
            async with asyncssh.connect(fqdn, port=self.port, username=self.username, password=self.password, known_hosts=None) as conn:
                if jobId is not None:
                    await conn.run(f"rm -rf {BASE_DIRECTORY}/job_{jobId}", check=True)
                    return

                result = await conn.run(f"find {BASE_DIRECTORY}/ -mindepth 1 -maxdepth 1 -type d", check=True)

                directories = result.stdout.splitlines()
                logger.info(f"Found the following directories on {fqdn} to clear: {directories}")

                for directory in directories:
                    await conn.run(f"rm -rf {directory}", check=True)
                    logger.info(f"Successfully cleared directory: {directory}")

        except Exception as e:
            raise Exception(f"Error sending files to {fqdn}: {str(e)}")

    def close(self):
        try:
            if self.sftp:
                self.sftp.close()
            if self.client:
                self.client.close()
        except Exception as e:
            raise Exception(f"Service Error in close: {e}")

