from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import require_teacher  # à créer si pas déjà existant
from app.models.course import Course
from app.models.course_purchase import CoursePurchase
from app.models.chapter import Chapter
from app.models.lesson import Lesson
from app.schemas.chapter import ChapterCreate, ChapterOut
from app.schemas.lesson import LessonCreate, LessonOut

router = APIRouter(prefix="/teacher", tags=["Teacher"])


# =========================
# CHAPTER (soumission par le prof)
# =========================
@router.post("/courses/{course_id}/chapters", response_model=ChapterOut)
def submit_chapter(
    course_id: int,
    chapter: ChapterCreate,
    db: Session = Depends(get_db),
    teacher=Depends(require_teacher)
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Vérifier que le prof est bien assigné à ce cours
    if course.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not your course")

    new_chapter = Chapter(
        **chapter.model_dump(),
        course_id=course_id,
        status="pending",
        submitted_by=teacher.id,
    )
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    return new_chapter


# =========================
# LESSON (ajoutée à un chapitre, peu importe son statut)
# =========================
@router.post("/chapters/{chapter_id}/lessons", response_model=LessonOut)
def add_lesson(
    chapter_id: int,
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    teacher=Depends(require_teacher)
):
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if chapter.course.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not your chapter")

    new_lesson = Lesson(**lesson.model_dump(), chapter_id=chapter_id)
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return new_lesson


# =========================
# DASHBOARD PROF
# =========================
@router.get("/dashboard")
def teacher_dashboard(
    db: Session = Depends(get_db),
    teacher=Depends(require_teacher)
):
    courses = db.query(Course).filter(Course.teacher_id == teacher.id).all()
    result = []
    for c in courses:
        student_count = db.query(CoursePurchase).filter(
            CoursePurchase.course_id == c.id
        ).count()
        result.append({
            "course_id": c.id,
            "title": c.title,
            "students_count": student_count,
            "delivery_mode": c.delivery_mode,
            "center": {
                "id": c.center.id,
                "name": c.center.name
            } if c.center else None,
        })
    return result