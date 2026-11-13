"""Authentication API router: register, login, and user profile."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.db import crud
from app.db.database import get_db
from app.db.models import User

try:
    from fastapi import APIRouter, Depends, HTTPException, Request, status
except ImportError:
    # Graceful fallback for offline static analysis or minimal host test environments
    class APIRouter:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.routes = []

        def get(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

        def post(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

    def Depends(dependency=None):  # type: ignore
        return dependency

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: str = "", headers: Optional[dict] = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
            super().__init__(detail)

    class _Status:
        HTTP_201_CREATED = 201
        HTTP_400_BAD_REQUEST = 400
        HTTP_401_UNAUTHORIZED = 401

    status = _Status()  # type: ignore
    Request = None  # type: ignore


router = APIRouter()


# =============================================================================
# Request / Response Schemas
# =============================================================================

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: str = Field(..., description="Email адрес")
    password: str = Field(..., min_length=6, description="Пароль (минимум 6 символов)")


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Имя пользователя или email")
    password: str = Field(..., description="Пароль")


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создаёт новую учётную запись пользователя и возвращает JWT токен.",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new user account."""
    username = payload.username.strip()
    email = payload.email.strip().lower()

    if not username or not email or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Все поля (username, email, password) обязательны для заполнения",
        )

    if crud.get_user_by_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с именем '{username}' уже существует",
        )

    if crud.get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с email '{email}' уже существует",
        )

    user = crud.create_user(
        db,
        username=username,
        email=email,
        password=payload.password,
    )

    token = create_access_token(
        data={
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Авторизация пользователя",
    description="Принимает JSON или Form-data с именем пользователя/email и паролем. Возвращает JWT токен.",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user with username or email and return JWT access token."""
    username = ""
    password = ""

    if request is not None:
        content_type = getattr(request, "headers", {}).get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                username = str(body.get("username", "")).strip()
                password = str(body.get("password", ""))
            except Exception:
                pass
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            try:
                form = await request.form()
                username = str(form.get("username", "")).strip()
                password = str(form.get("password", ""))
            except Exception:
                pass
        else:
            try:
                body = await request.json()
                username = str(body.get("username", "")).strip()
                password = str(body.get("password", ""))
            except Exception:
                try:
                    form = await request.form()
                    username = str(form.get("username", "")).strip()
                    password = str(form.get("password", ""))
                except Exception:
                    pass

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать имя пользователя и пароль",
        )

    # Allow login by username OR email
    user = crud.get_user_by_username(db, username)
    if not user:
        user = crud.get_user_by_email(db, username)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получение профиля текущего пользователя",
    description="Возвращает данные пользователя по переданному Bearer-токену.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
