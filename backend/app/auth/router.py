from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.deps import get_current_user
from app.common.rate_limit import rate_limit
from app.users.models import User
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.auth import service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201, dependencies=[Depends(rate_limit("register", max_requests=5, window_seconds=60))])
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = service.register_user(db, data)
    return service.issue_tokens(user)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit("login", max_requests=10, window_seconds=60))])
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, data)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return service.refresh_access_token(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
