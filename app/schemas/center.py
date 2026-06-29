from pydantic import BaseModel
from typing import Optional

class CenterBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    capacity: Optional[int] = None 
    is_active: bool = True

class CenterCreate(CenterBase):
    pass

class CenterOut(CenterBase):
    id: int
    model_config = {"from_attributes": True}