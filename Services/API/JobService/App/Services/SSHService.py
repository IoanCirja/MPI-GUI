import asyncio

import asyncssh

import paramiko
import os
from decouple import RepositoryEnv, Config
from fastapi import HTTPException
envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))

BASE_DIRECTORY = env('BASE_DIRECTORY')
SSH_HOST = env('SSH_HOST')
SSH_PORT = env('SSH_PORT')
SSH_USERNAME = env('SSH_USERNAME')
SSH_PASSWORD = env('SSH_PASSWORD')
MPI_HOSTS = env('MPI_HOSTS').split(',')

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class SSHService:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.sftp = None

        #self.ssh_keyscan()

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            self.sftp = self.client.open_sftp()
            print("SSH connection established.")
        except Exception as e:
            print(f"Error establishing SSH connection: {e}")
            raise HTTPException(status_code=500, detail="SSH connection failed.")


    def execute_command(self, command: str, remote_path_exe: str, remote_path_host:str):
        try:

            chmod_command = f"chmod +x {remote_path_exe}"
            stdin, stdout, stderr = self.client.exec_command(chmod_command)

            chmod_command = f"chmod +x {remote_path_host}"

            stdin, stdout, stderr = self.client.exec_command(chmod_command)

            stdin, stdout, stderr = self.client.exec_command(command)

            command_output = stdout.read().decode('utf-8')
            command_error = stderr.read().decode('utf-8')

            print(f"Command output: {command_output}")
            print(f"Command error: {command_error}")

            if command_error:
                raise Exception(f"Error executing command: {command_error}")

            print(f"Command executed successfully: {command}")
            return command_output

        except Exception as e:
            print(f"Error executing command: {e}")
            raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")


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
            raise HTTPException(status_code=500, detail=f"Error sending files to {fqdn}: {str(e)}")

    async def send_file_to_hosts(self, job_id, local_exe, local_hostfile):
        try:
            with open(local_hostfile, 'r') as hostfile:
                hosts = [line.strip().split()[0] for line in hostfile if line.strip()]

            if not hosts:
                raise ValueError("Hostfile is empty or invalid!")

            master_node = "c05-00"
            if master_node not in hosts:
                hosts.insert(0, master_node)

            tasks = []
            for host in hosts:
                fqdn = f"{host.lower()}.cs.tuiasi.ro"
                tasks.append(self.send_file_to_host(fqdn, job_id, local_exe, local_hostfile))

            await asyncio.gather(*tasks)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send files to hosts: {str(e)}")


    async def request_kill(self, job_id: str):
        try:
            remote_job_dir = f"{BASE_DIRECTORY}/job_{job_id}"
            pid_file_path = f"{remote_job_dir}/pid_{job_id}.txt"

            try:
                self.sftp.stat(pid_file_path)
                logger.info(f"Found PID file at {pid_file_path}.")
            except FileNotFoundError:
                logger.error(f"PID file not found for job {job_id}.")
                raise HTTPException(status_code=404, detail="PID file not found.")

            with self.sftp.open(pid_file_path, 'r') as pid_file:
                pid = pid_file.read().decode('utf-8').strip()
                logger.info(f"Retrieved PID: {pid} for job {job_id}.")

            kill_command = f"kill -9 {pid}"
            logger.info(f"Attempting to kill process with PID {pid} for job {job_id}.")
            stdin, stdout, stderr = self.client.exec_command(kill_command)

            command_output = stdout.read().decode('utf-8')
            command_error = stderr.read().decode('utf-8')

            if command_error:
                logger.error(f"Error killing process: {command_error}")
                raise HTTPException(status_code=500, detail=f"Error killing process: {command_error}")

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
            logger.error(f"Error killing MPI process for job {job_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error killing MPI process: {str(e)}")

    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        print("SSH connection closed.")
