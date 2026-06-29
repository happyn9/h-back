from sqlalchemy import Column, Integer,String,Float,ForeignKey,DateTime,func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="XAF")
    status = Column(String, default="pending")  # pending | success | failed | refunded
    course_purchases = relationship("CoursePurchase", back_populates="payment")
    flutterwave_tx_ref = Column(String, unique=True, nullable=False)  # généré par toi
    flutterwave_tx_id = Column(String, nullable=True)  # renvoyé par Flutterwave
    payment_method = Column(String, nullable=True)  # card, mobilemoney, banktransfer...
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    user = relationship("User")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    mode = Column(String, nullable=True)  # "standard" | "premium"
    course = relationship("Course")
