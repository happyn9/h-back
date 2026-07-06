import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pywebpush import webpush, WebPushException

from app.dependencies import get_db, get_current_user, require_admin
from app.core.config import settings
from app.models.notification import PushSubscription, Notification
from app.models.user import User
from app.schemas.notification import (
    PushSubscriptionIn,
    NotificationOut,
    NotificationCreate,
    NotificationListOut,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/subscribe")
def subscribe(
    sub: PushSubscriptionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(PushSubscription).filter_by(endpoint=sub.endpoint).first()
    if existing:
        return {"status": "already_subscribed"}

    new_sub = PushSubscription(
        user_id=current_user.id,
        endpoint=sub.endpoint,
        p256dh=sub.keys.p256dh,
        auth=sub.keys.auth,
    )
    db.add(new_sub)
    db.commit()
    return {"status": "subscribed"}


@router.delete("/unsubscribe")
def unsubscribe(
    endpoint: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(PushSubscription).filter_by(
        endpoint=endpoint, user_id=current_user.id
    ).first()
    if sub:
        db.delete(sub)
        db.commit()
    return {"status": "unsubscribed"}


@router.get("", response_model=NotificationListOut)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifs = (
        db.query(Notification)
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    unread_count = (
        db.query(Notification)
        .filter_by(user_id=current_user.id, is_read=False)
        .count()
    )
    return {"notifications": notifs, "unread_count": unread_count}


@router.patch("/{notif_id}/read")
def mark_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter_by(id=notif_id, user_id=current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    notif.is_read = True
    db.commit()
    return {"status": "ok"}


@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter_by(user_id=current_user.id, is_read=False).update(
        {"is_read": True}
    )
    db.commit()
    return {"status": "ok"}


def send_push_to_user(db: Session, user_id: int, title: str, body: str, url: str = "/"):
    subs = db.query(PushSubscription).filter_by(user_id=user_id).all()
    if not subs:
        return

    payload = json.dumps({"title": title, "body": body, "url": url})

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY_PATH,
                vapid_claims={"sub": settings.VAPID_CLAIMS_EMAIL},
            )
        except WebPushException as e:
            status = e.response.status_code if e.response else None
            if status in (404, 410):
                db.delete(sub)
                db.commit()


@router.post("/send", status_code=201)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),  # protégé, comme tes autres routes admin
):
    notif = Notification(
        user_id=payload.user_id,
        title=payload.title,
        body=payload.body,
        url=payload.url,
        type=payload.type,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    if payload.send_push:
        send_push_to_user(db, payload.user_id, payload.title, payload.body, payload.url or "/")
        notif.is_pushed = True
        db.commit()

    return {"status": "created", "id": notif.id}