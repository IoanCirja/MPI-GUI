import asyncio

from fastapi import FastAPI
from MonitorService.App.Services.MonitorService import run_ssh_cycle_and_notify

MONITOR_INTERVAL = 10
NODES = [f"c05-{str(i).zfill(2)}.cs.tuiasi.ro" for i in range(21)]
status_active_connections = []


app = FastAPI()




@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(run_ssh_cycle_and_notify())

