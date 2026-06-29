from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(String)
    image_url = Column(String)
    tags = Column(JSON, nullable=True)
    is_premium = Column(Boolean, default=True)
    standard_price = Column(Float, default=0)
    premium_price = Column(Float, default=0)
    order_index = Column(Integer, default=1)
    course_requirements = Column(JSON, default=list)
    what_you_will_learn = Column(JSON, default=list)

    program = relationship("Program", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")

    subscriptions = relationship("Subscription", back_populates="course", cascade="all, delete-orphan")

    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    center_id = Column(Integer, ForeignKey("centers.id"), nullable=True)
    delivery_mode = Column(String, default="online")  # online | offline | hybrid
    center = relationship("Center", back_populates="courses")
    teacher = relationship("User", back_populates="courses_taught")


