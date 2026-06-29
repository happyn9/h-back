import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import require_student
from app.core.flutterwave import initiate_payment
from app.utils.center_capacity import check_center_has_space

from app.models.course import Course
from app.models.program import Program
from app.models.chapter import Chapter
from app.models.payment import Payment
from app.models.course_purchase import CoursePurchase

from app.schemas.course import CourseOut
from app.schemas.payment import EnrollRequest, PaymentInitResponse

router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/courses", response_model=list[CourseOut])
def list_courses(
    category: str | None = None,
    language: str | None = None,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    query = db.query(Course).join(Program)
    if category:
        query = query.filter(Program.category == category)
    if language:
        query = query.filter(Program.language == language)
    return query.all()


@router.get("/courses/{course_id}")
def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course_id, Chapter.status == "approved")
        .order_by(Chapter.order_index)
        .all()
    )

    purchase = (
        db.query(CoursePurchase)
        .filter(
            CoursePurchase.user_id == student.id,
            CoursePurchase.course_id == course_id,
        )
        .first()
    )

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "image_url": course.image_url,
        "standard_price": course.standard_price,
        "premium_price": course.premium_price,
        "delivery_mode": course.delivery_mode,
        "course_requirements": course.course_requirements,
        "what_you_will_learn": course.what_you_will_learn,
        "is_enrolled": purchase is not None,
        "enrolled_mode": purchase.mode if purchase else None,
        "teacher": {"id": course.teacher.id, "name": course.teacher.name} if course.teacher else None,
        "center": {"id": course.center.id, "name": course.center.name} if course.center else None,
        "chapters": [
            {
                "id": ch.id,
                "title": ch.title,
                "order_index": ch.order_index,
                "lessons": [
                    {
                        "id": l.id,
                        "title": l.title,
                        "type": l.type,
                        "video_url": l.video_url,
                        "pdf_url": l.pdf_url,
                        "is_preview": l.is_preview,
                    }
                    for l in ch.lessons
                ],
            }
            for ch in chapters
        ],
    }


@router.post("/courses/{course_id}/enroll", response_model=PaymentInitResponse)
def enroll_course(
    course_id: int,
    data: EnrollRequest,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if data.mode not in ("standard", "premium"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    existing = (
        db.query(CoursePurchase)
        .filter(CoursePurchase.user_id == student.id, CoursePurchase.course_id == course_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    if course.center_id and not check_center_has_space(db, course.center_id):
        raise HTTPException(status_code=400, detail="This center is full (30/30 learners)")

    amount = course.standard_price if data.mode == "standard" else course.premium_price
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid price for this mode")

    tx_ref = f"hlearning-{uuid.uuid4().hex[:12]}"

    new_payment = Payment(
        user_id=student.id,
        course_id=course_id,
        mode=data.mode,
        amount=amount,
        currency="ZMW",
        status="pending",
        flutterwave_tx_ref=tx_ref,
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    try:
        fw_response = initiate_payment(
            amount=amount,
            currency="ZMW",
            email=student.email,
            tx_ref=tx_ref,
            name=student.name,
        )
    except Exception:
        new_payment.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Failed to initiate payment with Flutterwave")

    payment_link = fw_response.get("data", {}).get("link")
    if not payment_link:
        new_payment.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail="No payment link returned by Flutterwave")

    return PaymentInitResponse(
        payment_id=new_payment.id,
        tx_ref=tx_ref,
        payment_link=payment_link,
    )