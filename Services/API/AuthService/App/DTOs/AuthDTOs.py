from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    retypePassword: str

class UserResponse(BaseModel):
    username: str
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str




