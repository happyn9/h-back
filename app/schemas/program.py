from pydantic import BaseModel
from typing import Optional

class ProgramBase(BaseModel):
    title: str
    description: Optional[str] = None
    code: str
    semester: Optional[str] = None
    is_active: bool = True
    category: str = "IT"            
    language: Optional[str] = None

class ProgramCreate(ProgramBase):
    pass

class ProgramOut(ProgramBase):
    id: int
    model_config = {"from_attributes": True}