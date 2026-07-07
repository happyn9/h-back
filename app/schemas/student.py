from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.center import CenterOut


class StudentOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    center_id: Optional[int] = None
    center: Optional[CenterOut] = None

    model_config = {"from_attributes": True}


class StudentCenterUpdate(BaseModel):
    center_id: int