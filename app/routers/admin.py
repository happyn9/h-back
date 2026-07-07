from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import require_admin
from app.core.security import verify_pin
from app.schemas.pinschema import UpdatePinSchema
from app.core.security import hash_pin
from app.schemas.pinschema import PinVerify,CourseWithPin
from app.schemas.student import StudentOut, StudentCenterUpdate
from app.schemas.teacher import TeacherUpdate
from app.schemas.center import CenterUpdate
from app.utils.center_capacity import (
    get_center_enrolled_count,
    get_center_assigned_students_count,
    check_center_has_assignment_space,
)

from app.models.course import Course
from app.models.chapter import Chapter
from app.models.program import Program
from app.models.lesson import Lesson

from app.schemas.course import CourseCreate, CourseOut
from app.schemas.chapter import ChapterCreate, ChapterOut
from app.schemas.program import ProgramCreate, ProgramOut
from app.schemas.lesson import LessonCreate, LessonOut
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["Admin"])

# =========================
# PROGRAM
# =========================
@router.post("/programs", response_model=ProgramOut)
def create_program(
    program: ProgramCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    if program.category == "LANGUAGE" and not program.language:
        raise HTTPException(status_code=400, detail="Language is required for LANGUAGE programs")

    existing_program = db.query(Program).filter(Program.code == program.code).first()
    if existing_program:
        raise HTTPException(status_code=400, detail="Program code already exists")

    new_program = Program(**program.model_dump())
    db.add(new_program)
    db.commit()
    db.refresh(new_program)
    return new_program

# =========================
# COURSE (PIN PROTECTED)
# =========================
@router.post("/courses", response_model=CourseOut)
def create_course(
    data: CourseWithPin,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    # ... vérif PIN inchangée ...

    course_data = data.course

    # Vérifier que le prof existe et a bien le rôle "teacher"
    if course_data.teacher_id:
        teacher = db.query(User).filter(
            User.id == course_data.teacher_id,
            User.role == "teacher"
        ).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

    # Vérifier que le centre existe
    if course_data.center_id:
        center = db.get(Center, course_data.center_id)
        if not center:
            raise HTTPException(status_code=404, detail="Center not found")

    new_course = Course(**course_data.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

# =========================
# CHAPTER
# =========================
@router.post("/courses/{course_id}/chapters", response_model=ChapterOut)
def add_chapter(
    course_id: int,
    chapter: ChapterCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):

    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    new_chapter = Chapter(**chapter.dict(), course_id=course_id)
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    return new_chapter


# =========================
# LESSON
# =========================
@router.post("/chapters/{chapter_id}/lessons", response_model=LessonOut)
def add_lesson(
    chapter_id: int,
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):

    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    new_lesson = Lesson(**lesson.dict(), chapter_id=chapter_id)
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return new_lesson


# =========================
# VERIFY PIN (OPTIONAL DEBUG ENDPOINT)
# =========================
@router.post("/verify-pin")
def verify_admin_pin(
    data: PinVerify,
    admin=Depends(require_admin)
):

    if not admin.pin_hash:
        raise HTTPException(
            status_code=400,
            detail="PIN not set"
        )

    if not verify_pin(
        data.pin,
        admin.pin_hash
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid PIN"
        )

    return {
        "message": "PIN verified"
    }


# =========================
# UPDATE ADMIN PIN
# =========================
@router.put("/update-pin")
def update_admin_pin(
    data: UpdatePinSchema,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):

    # FIRST TIME SETUP
    if not admin.pin_hash:

        admin.pin_hash = hash_pin(
            data.new_pin
        )

        db.commit()

        return {
            "message": "PIN created"
        }

    # VERIFY OLD PIN
    if not verify_pin(
        data.current_pin,
        admin.pin_hash
    ):
        raise HTTPException(
            status_code=403,
            detail="Current PIN incorrect"
        )

    # UPDATE
    admin.pin_hash = hash_pin(
        data.new_pin
    )

    db.commit()

    return {
        "message": "PIN updated"
    }

@router.get("/programs", response_model=list[ProgramOut])
def get_programs(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(Program).all()

@router.get("/courses", response_model=list[CourseOut])
def get_courses(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(Course).all()

@router.get("/learners", response_model=list[UserOut])
def get_courses(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(User).all()


@router.get("/chapters", response_model=list[ChapterOut])
def get_chapters(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(Chapter).all()




from app.models.center import Center
from app.models.user import User
from app.schemas.center import CenterCreate, CenterOut
from app.schemas.teacher import TeacherCreate, TeacherOut
from app.core.security import hash_password


@router.post("/centers", response_model=CenterOut)
def create_center(
    center: CenterCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    new_center = Center(**center.model_dump())
    db.add(new_center)
    db.commit()
    db.refresh(new_center)
    return new_center


@router.get("/centers", response_model=list[CenterOut])
def get_centers(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(Center).all()


@router.post("/teachers", response_model=TeacherOut)
def create_teacher(
    data: TeacherCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already used")

    new_teacher = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="teacher",
        photo_url=data.photo_url or "https://i.pravatar.cc/150",
        is_active=True,
    )
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    return new_teacher


@router.get("/teachers", response_model=list[TeacherOut])
def get_teachers(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(User).filter(User.role == "teacher").all()


from datetime import datetime
from app.schemas.chapter import ChapterReview


@router.put("/chapters/{chapter_id}/review", response_model=ChapterOut)
def review_chapter(
    chapter_id: int,
    review: ChapterReview,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if review.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")

    chapter.status = review.status
    chapter.rejection_reason = review.rejection_reason if review.status == "rejected" else None
    chapter.reviewed_by = admin.id
    chapter.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(chapter)
    return chapter


@router.get("/chapters/pending", response_model=list[ChapterOut])
def get_pending_chapters(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(Chapter).filter(Chapter.status == "pending").all()


from app.utils.center_capacity import get_center_enrolled_count

@router.get("/centers/{center_id}/occupancy")
def get_center_occupancy(
    center_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    center = db.get(Center, center_id)
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    enrolled = get_center_enrolled_count(db, center_id)
    return {
        "center_id": center.id,
        "name": center.name,
        "capacity": center.capacity,
        "enrolled": enrolled,
        "available": max(0, center.capacity - enrolled),
        "is_full": enrolled >= center.capacity,
    }





# =========================
# STUDENTS
# =========================
@router.get("/students", response_model=list[StudentOut])
def get_students(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    return db.query(User).filter(User.role == "student").all()

@router.put("/students/{student_id}/center", response_model=StudentOut)
def change_student_center(
    student_id: int,
    data: StudentCenterUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    student = db.query(User).filter(
        User.id == student_id,
        User.role == "student"
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    center = db.get(Center, data.center_id)
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    if not center.is_active:
        raise HTTPException(status_code=400, detail="Center is not active")

    if not check_center_has_assignment_space(db, center.id):
        raise HTTPException(status_code=400, detail="Center is full")

    student.center_id = center.id
    db.commit()
    db.refresh(student)
    return student


@router.put("/teachers/{teacher_id}", response_model=TeacherOut)
def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == "teacher"
    ).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if data.email and data.email != teacher.email:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already used")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(teacher, field, value)

    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == "teacher"
    ).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    linked_courses = db.query(Course).filter(Course.teacher_id == teacher_id).count()
    if linked_courses > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {linked_courses} course(s) linked to this teacher"
        )

    db.delete(teacher)
    db.commit()
    return {"message": "Teacher deleted"}


@router.put("/centers/{center_id}", response_model=CenterOut)
def update_center(
    center_id: int,
    data: CenterUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    center = db.get(Center, center_id)
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(center, field, value)

    db.commit()
    db.refresh(center)
    return center


@router.delete("/centers/{center_id}")
def delete_center(
    center_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    center = db.get(Center, center_id)
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    assigned = get_center_assigned_students_count(db, center_id)
    if assigned > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {assigned} student(s) still assigned to this center"
        )

    db.delete(center)
    db.commit()
    return {"message": "Center deleted"}

