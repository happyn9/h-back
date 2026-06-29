from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChapterBase(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int = 1

class ChapterCreate(ChapterBase):
    pass

class ChapterOut(ChapterBase):
    id: int
    course_id: int
    status: str
    rejection_reason: Optional[str] = None
    submitted_by: Optional[int] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChapterReview(BaseModel):
    status: str  # "approved" | "rejected"
    rejection_reason: Optional[str] = None