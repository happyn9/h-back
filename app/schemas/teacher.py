from pydantic import BaseModel, EmailStr
from typing import Optional

class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    password: str 
    photo_url: Optional[str] = None

class TeacherOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None