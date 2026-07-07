from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subscription import Subscription, UserSubscription
from app.models.ai_usage import AIUsage

FREE_TIER_MONTHLY_LIMIT = 10


class QuotaExceeded(Exception):
    """reason: 'limit_reached' | 'subscribe_required'"""
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


def _get_or_create_usage(db: Session, user_id: int) -> AIUsage:
    current_month = date.today().strftime("%Y-%m")  # ex: "2026-07"
    usage = (
        db.query(AIUsage)
        .filter_by(user_id=user_id, month=current_month)
        .first()
    )
    if not usage:
        usage = AIUsage(user_id=user_id, month=current_month, questions_used=0)
        db.add(usage)
    return usage


def check_and_increment_quota(db: Session, user_id: int) -> None:
    """
    Lève QuotaExceeded si l'utilisateur a atteint sa limite (gratuite ou
    payante). Incrémente le compteur sinon.
    """
    subscription = get_active_subscription(db, user_id)
    usage = _get_or_create_usage(db, user_id)

    if subscription and subscription.has_ai_assistant:
        limit = subscription.ai_monthly_question_limit  # None = illimité
        if limit is not None and usage.questions_used >= limit:
            raise QuotaExceeded("limit_reached")
    else:
        # Pas d'abonnement donnant accès à l'IA -> tier gratuit
        if usage.questions_used >= FREE_TIER_MONTHLY_LIMIT:
            raise QuotaExceeded("subscribe_required")

    usage.questions_used += 1
    db.commit()