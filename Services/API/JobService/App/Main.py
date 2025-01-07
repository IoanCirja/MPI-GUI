from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from websocket import WebSocket

from JobService.App.Controllers.JobController import router
from JobService.App.Utils.FirebaseConnection import initializeFirebaseConnection

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



@app.get("/")
async def root():
    return {"message": "Hello World"}


initializeFirebaseConnection()


