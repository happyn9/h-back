
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subscription import Subscription, UserSubscription
from app.models.ai_usage import AIUsage


class QuotaExceeded(Exception):
    """reason: 'no_ai_access' | 'limit_reached'"""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def get_active_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    today = date.today()
    user_sub = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == user_id,
            UserSubscription.is_active == True,  # noqa: E712
            UserSubscription.start_date <= today,
            UserSubscription.end_date >= today,
        )
        .first()
    )
    return user_sub.subscription if user_sub else None


def check_and_increment_quota(db: Session, user_id: int) -> None:
    """
    Lève QuotaExceeded si l'utilisateur n'a pas accès à l'IA ou a atteint sa
    limite mensuelle de questions. Incrémente le compteur sinon.
    """
    subscription = get_active_subscription(db, user_id)

    if not subscription or not subscription.has_ai_assistant:
        raise QuotaExceeded("no_ai_access")

    limit = subscription.ai_monthly_question_limit  # None = illimité
    if limit is None:
        return

    current_month = date.today().strftime("%Y-%m")  # ex: "2026-07"

    usage = (
        db.query(AIUsage)
        .filter_by(user_id=user_id, month=current_month)
        .first()
    )

    if not usage:
        usage = AIUsage(user_id=user_id, month=current_month, questions_used=0)
        db.add(usage)

    if usage.questions_used >= limit:
        raise QuotaExceeded("limit_reached")

    usage.questions_used += 1
    db.commit()