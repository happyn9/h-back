from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.course_purchase import CoursePurchase
from app.models.center import Center


def get_center_enrolled_count(db: Session, center_id: int) -> int:
    return (
        db.query(CoursePurchase.user_id)
        .join(Course, Course.id == CoursePurchase.course_id)
        .filter(Course.center_id == center_id)
        .distinct()
        .count()
    )


def check_center_has_space(db: Session, center_id: int) -> bool:
    center = db.get(Center, center_id)
    if not center:
        return False
    enrolled = get_center_enrolled_count(db, center_id)
    return enrolled < center.capacity