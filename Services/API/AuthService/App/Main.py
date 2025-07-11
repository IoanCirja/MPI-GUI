from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from AuthService.App.Controllers.AdminController import admin_router
from AuthService.App.Controllers.UserController import user_router
from AuthService.App.Controllers.AuthController import router

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
app.include_router(admin_router, prefix="/api")
app.include_router(user_router, prefix="/api")
