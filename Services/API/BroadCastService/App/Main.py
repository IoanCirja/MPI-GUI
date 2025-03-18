import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from BroadCastService.App.Controllers.BroadCastController import router

status_active_connections = []

from BroadCastService.App.Services.BroadCastService import broadcast_node_statuses

app = FastAPI()

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(broadcast_node_statuses())
