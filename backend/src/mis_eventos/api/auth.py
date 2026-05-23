"""Endpoints de autenticacion - registro y login."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from mis_eventos.core.exceptions import AppError
from mis_eventos.core.security import create_access_token, hash_password, verify_password
from mis_eventos.db.session import get_db
from mis_eventos.models.user import User
from mis_eventos.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

DbDep = Annotated[Session, Depends(get_db)]


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de usuario nuevo",
)
def register(payload: RegisterRequest, db: DbDep) -> TokenResponse:
    """Crea un usuario nuevo y devuelve el JWT para uso inmediato."""
    existing = db.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise AppError(
            error="email_already_registered",
            detail="Ya existe una cuenta con ese email",
            status_code=409,
            context={"email": payload.email},
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login con email + password",
)
def login(payload: LoginRequest, db: DbDep) -> TokenResponse:
    """Verifica credenciales y devuelve el JWT."""
    user = db.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppError(
            error="invalid_credentials",
            detail="Email o contrasena incorrectos",
            status_code=401,
        )

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        ),
    )
