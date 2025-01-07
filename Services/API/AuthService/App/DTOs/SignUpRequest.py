import re
from pydantic import BaseModel, EmailStr, field_validator, model_validator

class SignUpRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    retypePassword: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        return value

    @field_validator("username")
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not re.match(r'^[A-Za-z0-9_.]+$', value):
            raise ValueError("Username can only contain alphanumeric characters and underscores")
        return value

    @field_validator("email")
    def validate_email(cls, value):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", value):
            raise ValueError("Invalid email format")
        return value

    @model_validator(mode='before')
    def check_password_match(cls, values):
        password = values.get("password")
        retypePassword = values.get("retypePassword")
        if password != retypePassword:
            raise ValueError("Passwords do not match")
        return values


class SignUpResponse(BaseModel):
    username: str
    email: str

    @field_validator("username")
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not re.match(r'^[A-Za-z0-9_.]+$', value):
            raise ValueError("Username can only contain alphanumeric characters and underscores")
        return value

    @field_validator("email")
    def validate_email(cls, value):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", value):
            raise ValueError("Invalid email format")
        return value
