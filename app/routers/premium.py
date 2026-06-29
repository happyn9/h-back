from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.core.database import get_db
from app.models.course import Course
from app.models.program import Program
from app.schemas.course import CourseOut

router = APIRouter(prefix="/premium", tags=["Premium"])


@router.get("/courses/it", response_model=List[CourseOut])
def get_premium_it_courses(db: Session = Depends(get_db)):
    courses = (
        db.query(Course)
        .join(Program)
        .filter(Course.is_premium == True, Program.category == "IT")
        .all()
    )
    return courses


@router.get("/courses/language", response_model=List[CourseOut])
def get_premium_language_courses(db: Session = Depends(get_db)):
    courses = (
        db.query(Course)
        .join(Program)
        .filter(Course.is_premium == True, Program.category == "LANGUAGE")
        .all()
    )
    return courses


# Optionnel : filtrer aussi par langue précise (en/fr)
@router.get("/courses/language/{lang}", response_model=List[CourseOut])
def get_premium_courses_by_language(lang: str, db: Session = Depends(get_db)):
    courses = (
        db.query(Course)
        .join(Program)
        .filter(
            Course.is_premium == True,
            Program.category == "LANGUAGE",
            Program.language == lang
        )
        .all()
    )
    return courses