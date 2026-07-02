from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
from pydantic import BaseModel
from datetime import date, timedelta

from app.routers.auth import router as auth_router
from app.routers.programs import router as programs_router
from app.routers.courses import router as courses_router
from app.routers.lessons import router as lessons_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.dashboard import router as dashboard_router
from app.routers.recommendations import router as recommendations_router
from app.routers.premium import router as premium_router
from app.routers.chapters import router as chapters_router
from app.routers.admin import router as admin_router
from app.routers.ai import router as ai_router
from app.routers.upload import router as upload_router
from app.routers.payment import router as payment_router
from app.routers.workspace import router as workspace_router
from app.routers.student import router as student_router
from app.routers.teacher import router as teacher_router

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.database import engine,Base
from app.models import *



# =================== APP ===================
app = FastAPI(title="H-Learning API 🚀")

Base.metadata.create_all(bind=engine)
# =================== MIDDLEWARE ===================
class COOPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
        return response


app.add_middleware(COOPMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://h-learning-wine.vercel.app",
        "https://h-back-2.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================== ROUTERS ===================
app.include_router(auth_router, prefix="/auth")
app.include_router(subscriptions_router)
app.include_router(premium_router)
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(recommendations_router, prefix="/recommendations")
app.include_router(courses_router)
app.include_router(lessons_router)
app.include_router(admin_router)
app.include_router(chapters_router)
app.include_router(ai_router)
app.include_router(programs_router, prefix="/programs")
app.include_router(workspace_router)
app.include_router(upload_router)
app.include_router(payment_router)
app.include_router(student_router)
app.include_router(teacher_router)


# =================== STATIC FILES ===================
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# =================== STARTUP ===================
@app.on_event("startup")
def startup():
    print("🚀 App started - DB managed by Alembic")


# =================== SCHEMAS (OK TEMPORAIRE) ===================
class Summary(BaseModel):
    completed_lessons: int
    progress_percent: float
    streak_days: int


class WeeklyAnalytics(BaseModel):
    date: str
    minutes: int


class Analytics(BaseModel):
    weekly: List[WeeklyAnalytics]
    monthly_minutes: int


# =================== FAKE DATA ===================
fake_summary = Summary(
    completed_lessons=12,
    progress_percent=35.0,
    streak_days=4
)

today = date.today()

fake_weekly = [
    WeeklyAnalytics(date=str(today - timedelta(days=i)), minutes=(i + 1) * 10)
    for i in range(7)
]

fake_analytics = Analytics(
    weekly=fake_weekly[::-1],
    monthly_minutes=sum([w.minutes for w in fake_weekly])
)


# =================== ENDPOINTS ===================
@app.get("/summary", response_model=Summary)
async def get_summary():
    return fake_summary


@app.get("/analytics", response_model=Analytics)
async def get_analytics():
    return fake_analytics


@app.get("/")
def read_root():
    return {"message": "Welcome to H-Learning API 🚀"}



"""from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()
admin_user = User(
    name="happy",
    email="happyneph12@gmail.com",
    password_hash=hash_password("31052003Ne@"),
    role="admin"
)
db.add(admin_user)
db.commit()
db.close()"""
