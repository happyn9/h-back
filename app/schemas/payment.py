from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EnrollRequest(BaseModel):
    mode: str  # "standard" | "premium"


class PaymentInitResponse(BaseModel):
    payment_id: int
    tx_ref: str
    payment_link: str


class PaymentOut(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    flutterwave_tx_ref: str
    flutterwave_tx_id: Optional[str] = None
    payment_method: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CoursePurchaseOut(BaseModel):
    id: int
    course_id: int
    mode: str
    purchased_at: datetime

    model_config = {"from_attributes": True}