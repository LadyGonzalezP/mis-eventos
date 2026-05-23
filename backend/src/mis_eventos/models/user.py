"""Modelo User - representa un usuario del sistema con su rol."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class UserRole(StrEnum):
    """Roles del sistema (RBAC).

    - asistente: usuario regular, solo se inscribe a eventos
    - organizador: crea y gestiona sus propios eventos
    - admin: gestiona el sistema completo y a todos los usuarios
    """

    ASISTENTE = "asistente"
    ORGANIZADOR = "organizador"
    ADMIN = "admin"


class User(SQLModel, table=True):
    """Usuario del sistema."""

    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, nullable=False)
    email: str = Field(max_length=200, nullable=False, unique=True, index=True)
    password_hash: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.ASISTENTE, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
