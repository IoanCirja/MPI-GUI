from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from BroadCastService.App.Services.BroadCastService import status_active_connections

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    status_active_connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        status_active_connections.remove(websocket)
