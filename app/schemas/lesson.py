from pydantic import BaseModel
from typing import Optional

class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str  # "video" | "pdf" | "quiz"
    video_url: Optional[str] = None
    pdf_url: Optional[str] = None

    duration_seconds: Optional[int] = None
    order_index: int = 1
    is_preview: bool = False

class LessonCreate(LessonBase):
    pass

class LessonOut(LessonBase):
    id: int
    chapter_id: int

    model_config = {"from_attributes": True}