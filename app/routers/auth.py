from fastapi import (
    APIRouter,
    Depends,
    Response,
    HTTPException,
    UploadFile,
    Form,
    File,
    Request
)
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import shutil
import os
from uuid import uuid4
import secrets
import random
import requests as http_requests  # appels HTTP vers l'API Google (tokeninfo / userinfo)

from app.models.user import User
from app.schemas.user import (
    RegisterSchema,
    LoginSchema,
    VerifyOTPSchema,
    UserOut,
    ChangePasswordSchema
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

from app.dependencies import get_db, get_current_user
from app.utils.send_email import (
    welcome_email,
    otp_email,
    send_email
)

router = APIRouter(tags=["Auth"])

GOOGLE_CLIENT_ID = "974675121498-ic32r1j1ooto7eq0bnohkh8dk4vfrsgo.apps.googleusercontent.com"

UPLOAD_DIR = "uploads/users"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


# ================= REGISTER =================
@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already exists")

    otp_code = str(random.randint(100000, 999999))
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Si le frontend envoie la langue courante d'i18n (recommandé, voir note
    # plus bas), on la stocke tout de suite. Sinon, "en" par défaut.
    user_language = getattr(data, "language", None) or "en"

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        otp_code=otp_code,
        otp_expires_at=otp_expires_at,
        email_verified=False,
        onboarding_completed=False,
        role="student",
        language=user_language,
    )
    db.add(user)
    db.flush()
    db.commit()
    db.refresh(user)

    try:
        subject, html = welcome_email(data.name, lang=user.language)
        send_email(data.email, subject, html)

        subject, html = otp_email(otp_code, lang=user.language)
        send_email(data.email, subject, html)
    except Exception as e:
        print(f"[EMAIL] Failed: {e}")

    return {"message": "OTP sent to your email!"}


# ================= LOGIN =================
@router.post("/login")
def login(data: LoginSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=404, detail="Wrong Email or password")

    now = datetime.now(timezone.utc)
    if not (user.otp_code and user.otp_expires_at and user.otp_expires_at > now):
        otp_code = str(random.randint(100000, 999999))

        user.otp_code = otp_code
        user.otp_expires_at = now + timedelta(minutes=5)
        db.commit()
        db.refresh(user)

        print(f"otp {user.otp_code}")

        try:
            subject, html = otp_email(otp_code, lang=user.language or "en")
            send_email(user.email, subject, html)
        except Exception as e:
            print(f"[EMAIL] Failed: {e}")

    return {"message": "OTP sent to your email!"}


# ================= RESEND OTP =================
@router.post("/resend-otp")
def resend_otp(data: dict, db: Session = Depends(get_db)):
    email = data.get("email")
    if not email:
        raise HTTPException(400, "Email required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")

    otp_code = str(random.randint(100000, 999999))
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    user.otp_code = otp_code
    user.otp_expires_at = otp_expires_at
    db.flush()
    db.commit()
    db.refresh(user)

    try:
        subject, html = otp_email(otp_code, lang=user.language or "en")
        send_email(email, subject, html)
    except Exception as e:
        print(f"[EMAIL] Failed: {e}")

    return {"message": "New OTP sent!"}


# ================= VERIFY OTP =================
@router.post("/verify-otp")
def verify_otp(data: VerifyOTPSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(404, "User not found")

    print(f"[OTP] Comparing: received={data.otp} stored={user.otp_code}")

    if not user.otp_code:
        raise HTTPException(400, "No OTP found, request a new one")

    if user.otp_code != data.otp:
        raise HTTPException(400, "Invalid OTP")

    if user.otp_expires_at and datetime.now(timezone.utc) > user.otp_expires_at:
        raise HTTPException(400, "OTP expired")

    user.email_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()

    token = create_access_token({"user_id": user.id}, data.remember_me)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="none",
        secure=True,
        path="/"
    )

    return {"message": "Authenticated"}


# ================= LOGOUT =================
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


# ================= ME =================
@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


# ================= CHANGE PASSWORD =================
@router.post("/change-password")
def change_password(
    data: ChangePasswordSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    user.old_password_hash = user.password_hash
    user.password_hash = hash_password(data.new_password)

    db.add(user)
    db.commit()

    return {"message": "Password changed successfully"}


# ================= UPDATE PROFILE =================
@router.put("/update-profile")
def update_profile(
    name: str = Form(...),
    email: str = Form(...),
    university: str = Form(None),
    program: str = Form(None),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    existing_user = db.query(User).filter(
        User.email == email,
        User.id != user.id
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    user.name = name
    user.email = email.lower()

    if university:
        user.onboarding = user.onboarding or {}
        user.onboarding["university"] = university

    if program:
        user.onboarding = user.onboarding or {}
        user.onboarding["program"] = program

    if photo:
        filename = f"{uuid4().hex}_{photo.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        user.photo_url = f"/{UPLOAD_DIR}/{filename}"

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "name": user.name,
            "email": user.email,
            "photo_url": user.photo_url,
            "university": university,
            "program": program
        }
    }


# ================= GOOGLE LOGIN =================
# Le front envoie désormais un access_token OAuth (via useGoogleLogin),
# plus un id_token/credential JWT. On ne peut donc plus utiliser
# id_token.verify_oauth2_token ici (ça n'accepte que des JWT).
#
# À la place :
# 1. On vérifie via /tokeninfo que ce token a bien été émis pour NOTRE
#    client Google (champ "aud") — sans ça, un access_token obtenu pour
#    une autre appli Google pourrait être accepté par erreur.
# 2. On récupère le profil (email, nom) via /userinfo avec ce token.
@router.post("/google")
def google_login(data: dict, response: Response, db: Session = Depends(get_db)):
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(400, "Missing access_token")

    try:
        tokeninfo_resp = http_requests.get(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            params={"access_token": access_token},
            timeout=5,
        )
        tokeninfo_resp.raise_for_status()
        tokeninfo = tokeninfo_resp.json()

        if tokeninfo.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(400, "Invalid Google token")

        userinfo_resp = http_requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        userinfo_resp.raise_for_status()
        idinfo = userinfo_resp.json()
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GOOGLE] Token verification failed: {e}")
        raise HTTPException(400, "Invalid Google token")

    email = idinfo.get("email")
    name = idinfo.get("name", "User")

    if not email:
        raise HTTPException(400, "Google account has no email")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(secrets.token_hex(16)),
            email_verified=True,        
            onboarding_completed=False,  
            role="student",               
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:

        if not user.email_verified:
            user.email_verified = True
            db.commit()
            db.refresh(user)

    token = create_access_token({"user_id": user.id}, False)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="none",
        secure=True,
        path="/"
    )

    return {"message": "Google login success"}