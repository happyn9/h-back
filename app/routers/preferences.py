
from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["preferences"])

SUPPORTED_LANGUAGES = ("en", "fr")


class LanguageIn(BaseModel):
    language: str

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        v = v.lower()
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Langue non supportée : {v} (attendu: en, fr)")
        return v


@router.patch("/me/language")
def update_language(
    payload: LanguageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.language = payload.language
    db.commit()
    return {"status": "ok", "language": payload.language}