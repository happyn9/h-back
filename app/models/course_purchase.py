from sqlalchemy import Column, Integer, ForeignKey, DateTime,func,String
from app.core.database import Base
from sqlalchemy.orm import relationship




class CoursePurchase(Base):
    __tablename__ = "course_purchases"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    purchased_at = Column(DateTime, server_default=func.now())
    payment = relationship("Payment", back_populates="course_purchases")
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    user = relationship("User")
    course = relationship("Course")
    mode = Column(String, nullable=False, default="standard") 
