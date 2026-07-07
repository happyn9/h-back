from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    old_password_hash = Column(String, nullable=True)

    role = Column(String, default="student")
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    photo_url = Column(String, default="https://i.pravatar.cc/150")
    pin_hash = Column(String, nullable=True)
    onboarding = Column(JSON, default=lambda: {})
    academic = Column(JSON, default=lambda: {})
    onboarding_completed = Column(Boolean, default=False)

    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)

    center_id = Column(Integer, ForeignKey("centers.id"), nullable=True)

    # Relations
    subscriptions = relationship("UserSubscription", back_populates="user")
    notes = relationship("UserNote", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("UserLessonProgress", back_populates="user", cascade="all, delete-orphan")
    activity = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    streaks = relationship("UserStreak", back_populates="user", cascade="all, delete-orphan")
    courses_taught = relationship("Course", back_populates="teacher")
    language = Column(String, default="en", server_default="en")
    push_subscriptions = relationship("PushSubscription", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    center = relationship("Center", back_populates="students")