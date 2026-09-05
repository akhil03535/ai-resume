from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.deps import get_current_user
from app.users.models import User
from app.dashboard.service import DashboardResponse, get_dashboard

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_dashboard(db, current_user.id)
