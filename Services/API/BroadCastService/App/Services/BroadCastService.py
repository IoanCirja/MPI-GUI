import asyncio
import json
import os

import logging

from decouple import Config, RepositoryEnv
from starlette.websockets import WebSocketDisconnect

from BroadCastService.App.Repositories.BroadCastRepository import BroadCastRepository

envPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env = Config(RepositoryEnv(envPath))
SSH_HOST = env('SSH_HOST')
SSH_PORT = int(env('SSH_PORT'))
SSH_USERNAME = env('SSH_USERNAME')
SSH_PASSWORD = env('SSH_PASSWORD')
MPI_HOSTS = env('MPI_HOSTS').split(',')


status_active_connections = []

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

node_statuses = {node: None for node in MPI_HOSTS}



async def broadcast_node_statuses():
    repo = BroadCastRepository()

    while True:
        try:
            node_statuses = repo.get_all_node_statuses()

            if not node_statuses:
                logging.warning("No node statuses available to broadcast.")
                await asyncio.sleep(60)
                continue

            node_status_data = json.dumps(node_statuses)

            for websocket in status_active_connections:
                try:
                    await websocket.send_text(node_status_data)
                except WebSocketDisconnect:
                    status_active_connections.remove(websocket)

            logging.info(f"Broadcasted node statuses to {len(status_active_connections)} clients.")
            await asyncio.sleep(5)

        except Exception as e:
            logging.error(f"Error while broadcasting node statuses: {e}")
            await asyncio.sleep(60)