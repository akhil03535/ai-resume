from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import AppError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.users.models import User
from app.profiles.models import CandidateProfile
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse


def register_user(db: Session, data: RegisterRequest) -> User:
    existing = db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise AppError("An account with this email already exists.", code="email_taken", status_code=409)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.flush()

    # Every user gets an (initially empty) candidate profile - it's the
    # central source of truth referenced throughout the app (spec #8).
    db.add(CandidateProfile(user_id=user.id))
    db.flush()
    return user


def authenticate_user(db: Session, data: LoginRequest) -> User:
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password.")
    if not user.is_active:
        raise UnauthorizedError("This account has been disabled.")
    return user


def issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid or expired refresh token.")

    user = db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise UnauthorizedError("Account not found or disabled.")

    return issue_tokens(user)
