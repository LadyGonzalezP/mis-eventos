"""Schemas Pydantic para autenticacion - DTOs request/response."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from mis_eventos.models.user import UserRole

_PASSWORD_PATTERN = re.compile(r"\d")


class RegisterRequest(BaseModel):
    """Body de POST /auth/register."""

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    role: UserRole = Field(default=UserRole.ASISTENTE)

    @field_validator("password")
    @classmethod
    def password_must_have_digit(cls, value: str) -> str:
        if not _PASSWORD_PATTERN.search(value):
            raise ValueError("La contrasena debe contener al menos un numero")
        return value

    @field_validator("role")
    @classmethod
    def role_at_registration_cannot_be_admin(cls, value: UserRole) -> UserRole:
        if value == UserRole.ADMIN:
            raise ValueError(
                "No se puede registrar como Admin. Los Admin se crean por seed o asignacion manual."
            )
        return value


class LoginRequest(BaseModel):
    """Body de POST /auth/login."""

    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    """Representacion publica de un usuario (sin password_hash)."""

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    """Respuesta de /auth/login y /auth/register: token + datos del usuario."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
