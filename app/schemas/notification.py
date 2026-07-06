from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys


class NotificationOut(BaseModel):
    id: int
    title: str
    body: str
    url: Optional[str] = None
    type: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    body: str
    url: Optional[str] = None
    type: str = "info"
    send_push: bool = True


class NotificationListOut(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int