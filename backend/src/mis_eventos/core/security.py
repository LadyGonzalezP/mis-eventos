"""Seguridad - hashing bcrypt, JWT, dependencies de auth y RBAC.

Punto unico para toda la logica de autenticacion y autorizacion.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import bcrypt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from mis_eventos.core.config import settings
from mis_eventos.core.exceptions import AppError, ForbiddenError
from mis_eventos.db.session import get_db
from mis_eventos.models.user import User, UserRole

# bcrypt con cost factor 12 - default seguro para 2026
_BCRYPT_ROUNDS = 12

# OAuth2PasswordBearer expone en /docs un boton de "Authorize" para tests manuales
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ============================================
# Password hashing (bcrypt directo - evita problemas de passlib con bcrypt >=4)
# ============================================


def hash_password(plain_password: str) -> str:
    """Hashea un password con bcrypt. Maximo 72 bytes (limite de bcrypt)."""
    password_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica un password contra su hash bcrypt."""
    password_bytes = plain_password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ============================================
# JWT
# ============================================


def create_access_token(user_id: uuid.UUID, role: UserRole) -> str:
    """Crea un JWT con sub (user_id), role y exp."""
    now = datetime.now(UTC)
    expire = now + timedelta(hours=settings.jwt_expiration_hours)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un JWT. Lanza AppError 401 si es invalido o expiro."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise AppError(
            error="invalid_token",
            detail="Token invalido o expirado",
            status_code=401,
        ) from exc


# ============================================
# FastAPI dependencies
# ============================================


def _get_token_from_request(request: Request) -> str:
    """Extrae el token Bearer del header Authorization."""
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise AppError(
            error="missing_token",
            detail="Token de autenticacion requerido",
            status_code=401,
        )
    return auth.split(" ", 1)[1].strip()


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Devuelve el User actual a partir del JWT del header Authorization."""
    token = _get_token_from_request(request)
    payload = decode_access_token(token)

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AppError(error="invalid_token", detail="Token sin sub", status_code=401)

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise AppError(
            error="invalid_token", detail="sub no es UUID valido", status_code=401
        ) from exc

    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise AppError(
            error="user_not_found",
            detail="El usuario del token ya no existe",
            status_code=401,
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: UserRole):
    """Factory de dependency: exige que el usuario tenga uno de los roles dados."""

    def _check_role(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            roles_str = ", ".join(r.value for r in allowed_roles)
            raise ForbiddenError(
                detail=f"Acceso denegado - se requiere rol: {roles_str}"
            )
        return current_user

    return _check_role
