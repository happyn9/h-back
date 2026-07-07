from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base
from sqlalchemy.orm import relationship

class Center(Base):
    __tablename__ = "centers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
    city = Column(String)
    capacity = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True)
    courses = relationship("Course", back_populates="center")
    students = relationship("User", back_populates="center")