
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from JobService.App.Controllers.JobController import router
from JobService.App.Utils.FirebaseConnection import initializeFirebaseConnection

MONITOR_INTERVAL = 120
NODES = [f"c05-{str(i).zfill(2)}.cs.tuiasi.ro" for i in range(21)]
status_active_connections = []



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

initializeFirebaseConnection()


