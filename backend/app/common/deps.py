from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.common.exceptions import UnauthorizedError
from app.users.models import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header.")

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Session expired or invalid. Please log in again.")

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedError("Invalid session token.")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Account not found or disabled.")

    return user
