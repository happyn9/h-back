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
        "no_ai_access": "Your current plan doesn't include AI assistant access.",
        "limit_reached": "You've reached your monthly AI question limit.",
        "rate_limit": "AI service is temporarily overloaded. Please try again shortly.",
    },
    "fr": {
        "no_ai_access": "Ton abonnement actuel ne donne pas accès à l'assistant IA.",
        "limit_reached": "Tu as atteint ta limite mensuelle de questions IA.",
        "rate_limit": "Le service IA est temporairement surchargé. Réessaie dans un instant.",
    },
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
        status_code = 403 if e.reason == "no_ai_access" else 429
        raise HTTPException(status_code, _MESSAGES[lang][e.reason])

    messages = [
        {"role": "system", "content": get_prompt(lang)},
        {"role": "user", "content": req.message},
    ]

    try:
        reply = ask_ai(messages)
    except RateLimitError:
        reply = _MESSAGES[lang]["rate_limit"]

    return {"reply": reply}