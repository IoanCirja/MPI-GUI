from pydantic import BaseModel


class RemoveSuspensionRequest(BaseModel):
    user_id: str
    suspension_id: str