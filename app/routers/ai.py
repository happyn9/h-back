from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import RateLimitError

from app.ai.openai_client import ask_ai
from app.ai.prompt import get_prompt
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.ai_quota import check_and_increment_quota, QuotaExceeded

router = APIRouter(prefix="/ai", tags=["AI"])

_MESSAGES = {
    "en": {
        "subscribe_required": "You've used your 10 free questions this month. Subscribe to a plan with AI access to keep chatting.",
        "limit_reached": "You've reached your monthly AI question limit.",
        "rate_limit": "AI service is temporarily overloaded. Please try again shortly.",
    },
    "fr": {
        "subscribe_required": "Tu as utilisé tes 10 questions gratuites ce mois-ci. Abonne-toi à un plan avec accès IA pour continuer.",
        "limit_reached": "Tu as atteint ta limite mensuelle de questions IA.",
        "rate_limit": "Le service IA est temporairement surchargé. Réessaie dans un instant.",
    },
}

# 402 Payment Required pour l'upsell abonnement, 429 pour un quota payant dépassé
_STATUS_CODES = {
    "subscribe_required": 402,
    "limit_reached": 429,
}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lang = user.language if user.language in _MESSAGES else "en"

    try:
        check_and_increment_quota(db, user.id)
    except QuotaExceeded as e:
        raise HTTPException(_STATUS_CODES[e.reason], _MESSAGES[lang][e.reason])

    messages = [
        {"role": "system", "content": get_prompt(lang)},
        {"role": "user", "content": req.message},
    ]

    try:
        reply = ask_ai(messages)
    except RateLimitError:
        reply = _MESSAGES[lang]["rate_limit"]

    return {"reply": reply}