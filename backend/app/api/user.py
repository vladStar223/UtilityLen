"""User profile and statistics API endpoints."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.bills import _resolve_user
from app.core.auth import get_current_user_optional
from app.db import crud
from app.db.database import get_db
from app.db.models import User

router = APIRouter()


# =============================================================================
# Request / Response Schemas
# =============================================================================

class UserProfileResponse(BaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    personal_account: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    personal_account: Optional[str] = None


class UserStatsResponse(BaseModel):
    total_bills: int
    total_amount_rub: float
    anomalies_detected: int
    overpayment_identified_rub: float
    average_monthly_bill_rub: float


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Получение профиля пользователя",
    description="Возвращает персональные данные текущего пользователя.",
)
def get_user_profile(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> UserProfileResponse:
    active_user = _resolve_user(db, user)
    return UserProfileResponse.model_validate(active_user)


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Обновление профиля пользователя",
    description="Обновляет персональные данные текущего пользователя.",
)
def update_user_profile(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> UserProfileResponse:
    active_user = _resolve_user(db, user)
    updated_user = crud.update_user_profile(
        db,
        active_user,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        address=payload.address,
        personal_account=payload.personal_account,
    )
    return UserProfileResponse.model_validate(updated_user)


@router.get(
    "/stats",
    response_model=UserStatsResponse,
    summary="Статистика проверок",
    description="Возвращает агрегированную статистику по проверкам квитанций пользователя.",
)
def get_user_stats(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> UserStatsResponse:
    active_user = _resolve_user(db, user)
    stats = crud.calculate_user_stats(db, active_user.user_id)
    return UserStatsResponse(**stats)
