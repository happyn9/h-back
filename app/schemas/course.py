from pydantic import BaseModel
from typing import List, Optional

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_premium: bool = True
    order_index: int = 0
    tags: List[str] = []
    image_url: Optional[str] = None
    standard_price: float = 0
    premium_price: float = 0
    program_id: int
    course_requirements: List[str] = []
    what_you_will_learn: List[str] = []

    teacher_id: Optional[int] = None
    center_id: Optional[int] = None
    delivery_mode: str = "online"  # online | offline | hybrid

class CourseCreate(CourseBase):
    pass

class CourseOut(CourseBase):
    id: int
    model_config = {"from_attributes": True}