from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.course_purchase import CoursePurchase
from app.models.center import Center
from app.models.user import User


# ============ ENROLLMENT (achats de cours) ============
def get_center_enrolled_count(db: Session, center_id: int) -> int:
    """Élèves ayant acheté un cours rattaché à ce center."""
    return (
        db.query(CoursePurchase.user_id)
        .join(Course, Course.id == CoursePurchase.course_id)
        .filter(Course.center_id == center_id)
        .distinct()
        .count()
    )


def check_center_has_enrollment_space(db: Session, center_id: int) -> bool:
    """Utilisée à l'inscription à un cours (student/enroll_course)."""
    center = db.get(Center, center_id)
    if not center:
        return False
    enrolled = get_center_enrolled_count(db, center_id)
    return enrolled < center.capacity


# ============ ASSIGNATION ADMINISTRATIVE (User.center_id) ============
def get_center_assigned_students_count(db: Session, center_id: int) -> int:
    """Élèves administrativement rattachés à ce center."""
    return (
        db.query(User)
        .filter(User.center_id == center_id, User.role == "student")
        .count()
    )


def check_center_has_assignment_space(db: Session, center_id: int) -> bool:
    """Utilisée à l'assignation admin (admin/change_student_center)."""
    center = db.get(Center, center_id)
    if not center:
        return False
    assigned = get_center_assigned_students_count(db, center_id)
    return assigned < center.capacity