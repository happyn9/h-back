from pydantic import BaseModel, EmailStr
from typing import Optional

class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    password: str  # mot de passe initial, le prof pourra le changer après
    photo_url: Optional[str] = None

class TeacherOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    model_config = {"from_attributes": True}