import asyncio
import os
import paramiko
import logging
from decouple import Config, RepositoryEnv

from MonitorService.App.DTOs.NodeStatusDTO import NodeStatusDTO
from MonitorService.App.Repositories.MonitorRepository import MonitorRepository

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))
SSH_HOST = env('SSH_HOST')
SSH_PORT = int(env('SSH_PORT'))
SSH_USERNAME = env('SSH_USERNAME')
SSH_PASSWORD = env('SSH_PASSWORD')
MPI_HOSTS = env('MPI_HOSTS').split(',')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

node_statuses = {node: None for node in MPI_HOSTS}

class MonitorService:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh_client = None
        self.repo = MonitorRepository()

    def connect(self):
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.host, port=self.port, username=self.username, password=self.password)
        except Exception as e:
            logging.error(f"SSH connection error: {e}")

    def run_ssh_command(self, node: str):
        try:
            command = f"ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no mpi.cluster@{node} uptime"

            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=10)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if output:
                logging.debug(f"Node {node} is available.")
                return True

            if error:
                logging.warning(f"Node {node} SSH error: {error}")
                return False

            return False

        except Exception as e:
            logging.error(f"Exception while running command on {node}: {e}")
            return False

    def close(self):
        if self.ssh_client:
            self.ssh_client.close()
            logging.info("SSH connection closed.")

    def update_node_statuses_in_db(self):
        node_status_dtos = []
        for node in MPI_HOSTS:
            status = self.run_ssh_command(node)

            node_key = node.split('.')[0]
            formatted_node_key = node_key.upper()

            node_status_dtos.append(NodeStatusDTO(formatted_node_key, status))

        self.repo.update_all_node_statuses(node_status_dtos)


async def run_ssh_cycle_and_notify():
    loop = asyncio.get_event_loop()
    ssh_service = MonitorService(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)

    await loop.run_in_executor(None, ssh_service.connect)

    try:
        while True:
            logging.debug("Starting sequential node checks...")

            ssh_service.update_node_statuses_in_db()

            logging.debug("Sleeping for 60 seconds before next cycle.")
            await asyncio.sleep(60)
    finally:
        await loop.run_in_executor(None, ssh_service.close)