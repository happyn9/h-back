# app/routers/payment.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.core.flutterwave import initiate_payment as flw_initiate, verify_transaction
from app.dependencies import get_current_user
from app.models.payment import Payment
from app.models.course_purchase import CoursePurchase
from app.models.subscription import Subscription, UserSubscription
from app.routers.subscriptions import create_user_subscription, is_active

router = APIRouter(prefix="/pay", tags=["Payments"])


# ─── Schemas ───────────────────────────────────────────────
class InitiatePaymentIn(BaseModel):
    course_id: int
    billing: str        # "monthly" | "yearly"
    phone: str
    operator: str


# ─── POST /pay/initiate ────────────────────────────────────
@router.post("/initiate")
def initiate(payload: InitiatePaymentIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Trouve le plan correspondant
    sub = db.query(Subscription).filter(
        Subscription.course_id == payload.course_id,
        Subscription.billing_type == payload.billing,
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No subscription plan found for this course/billing")

    if is_active(db, user.id, sub.id):
        raise HTTPException(status_code=400, detail="Already subscribed")

    tx_ref = f"hlearn-{uuid.uuid4().hex}"

    # Crée le Payment en base (status=pending)
    payment = Payment(
        user_id=user.id,
        course_id=payload.course_id,
        amount=sub.price,
        currency="ZMW",
        mode=payload.billing,
        flutterwave_tx_ref=tx_ref,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Appel Flutterwave
    try:
        flw_response = flw_initiate(
            amount=sub.price,
            currency="ZMW",
            email=user.email,
            tx_ref=tx_ref,
            name=getattr(user, "name", user.email),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Flutterwave error: {str(e)}")

    payment_url = flw_response.get("data", {}).get("link")
    if not payment_url:
        raise HTTPException(status_code=502, detail="No payment link returned by Flutterwave")

    return {"payment_url": payment_url}


# ─── GET /pay/check/{course_id} ────────────────────────────
@router.get("/check/{course_id}")
def check_subscription(course_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    sub = db.query(Subscription).filter(
        Subscription.course_id == course_id
    ).first()

    if not sub:
        return {"subscribed": False}

    subscribed = is_active(db, user.id, sub.id)
    return {"subscribed": subscribed}


# ─── POST /pay/webhook ─────────────────────────────────────
@router.post("/webhook")
async def flutterwave_webhook(request: Request, db: Session = Depends(get_db)):
    received_hash = request.headers.get("verif-hash")
    if not received_hash or received_hash != settings.FLUTTERWAVE_WEBHOOK_HASH:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    body = await request.json()
    data = body.get("data", {})
    tx_ref = data.get("tx_ref")
    transaction_id = data.get("id")

    if not tx_ref or not transaction_id:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    payment = db.query(Payment).filter(Payment.flutterwave_tx_ref == tx_ref).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == "success":
        return {"status": "already processed"}

    verification = verify_transaction(str(transaction_id))
    verified_data = verification.get("data", {})

    if (
        verification.get("status") == "success"
        and verified_data.get("status") == "successful"
        and float(verified_data.get("amount", 0)) >= payment.amount
        and verified_data.get("currency") == payment.currency
    ):
        payment.status = "success"
        payment.flutterwave_tx_id = str(transaction_id)
        payment.payment_method = verified_data.get("payment_type")
        payment.paid_at = datetime.utcnow()
        db.commit()

        # Active la subscription
        sub = db.get(Subscription, payment.subscription_id)
        if sub and not is_active(db, payment.user_id, sub.id):
            user_sub = create_user_subscription(payment.user_id, sub)
            db.add(user_sub)

        db.commit()
        return {"status": "ok"}

    payment.status = "failed"
    db.commit()
    return {"status": "failed"}



class VerifyPaymentIn(BaseModel):
    tx_ref: str
    transaction_id: str

@router.post("/verify")
def verify_payment(payload: VerifyPaymentIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    payment = db.query(Payment).filter(Payment.flutterwave_tx_ref == payload.tx_ref).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == "success":
        return {"status": "already_success", "course_id": payment.course_id}

    verification = verify_transaction(payload.transaction_id)
    verified_data = verification.get("data", {})

    if (
        verification.get("status") == "success"
        and verified_data.get("status") == "successful"
        and float(verified_data.get("amount", 0)) >= payment.amount
        and verified_data.get("currency") == payment.currency
    ):
        payment.status = "success"
        payment.flutterwave_tx_id = payload.transaction_id
        payment.payment_method = verified_data.get("payment_type")
        payment.paid_at = datetime.utcnow()

        sub = db.query(Subscription).filter(
            Subscription.course_id == payment.course_id,
            Subscription.billing_type == payment.mode,
        ).first()

        if sub and not is_active(db, payment.user_id, sub.id):
            user_sub = create_user_subscription(payment.user_id, sub)
            db.add(user_sub)

        db.commit()
        return {"status": "success", "course_id": payment.course_id}  # ← ici

    payment.status = "failed"
    db.commit()
    raise HTTPException(status_code=402, detail="Payment verification failed")