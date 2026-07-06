
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.notification import Notification
from app.models.subscription import UserSubscription
from app.routers.notifications import send_push_to_user
from app.utils.send_email import send_email
from app.services.reminder_templates import (
    subscribed_reminder_email,
    subscribed_reminder_push,
    unsubscribed_reminder_email,
    unsubscribed_reminder_push,
)

logger = logging.getLogger("hlearning.reminders")


def _has_active_subscription(db: Session, user_id: int) -> bool:
   
    today = date.today()
    return (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == user_id,
            UserSubscription.is_active == True,  # noqa: E712
            UserSubscription.start_date <= today,
            UserSubscription.end_date >= today,
        )
        .first()
        is not None
    )


def send_daily_reminders() -> None:

    db: Session = SessionLocal()
    sent, failed = 0, 0

    try:
        users = (
            db.query(User)
            .filter(User.is_active == True, User.email_verified == True)  # noqa: E712
            .all()
        )

        for user in users:
            try:
                lang = getattr(user, "language", None) or "en"
                is_subscribed = _has_active_subscription(db, user.id)

                if is_subscribed:
                    push_title, push_body = subscribed_reminder_push(lang, user.name)
                    subject, html = subscribed_reminder_email(lang, user.name)
                else:
                    push_title, push_body = unsubscribed_reminder_push(lang, user.name)
                    subject, html = unsubscribed_reminder_email(lang, user.name)

                # 1. Email
                send_email(user.email, subject, html)

                # 2. Notification en base (visible dans la cloche de l'app)
                notif = Notification(
                    user_id=user.id,
                    title=push_title,
                    body=push_body,
                    url="/courses",
                    type="reminder",
                )
                db.add(notif)
                db.commit()
                db.refresh(notif)

                # 3. Push navigateur (si l'utilisateur a un abonnement push actif)
                send_push_to_user(db, user.id, push_title, push_body, "/courses")

                sent += 1
            except Exception:
                failed += 1
                db.rollback()
                logger.exception("Échec du rappel pour l'utilisateur %s", user.id)

        logger.info("Rappels quotidiens terminés : %s envoyés, %s échoués", sent, failed)

    except Exception:
        logger.exception("Erreur générale pendant l'envoi des rappels quotidiens")
    finally:
        db.close()