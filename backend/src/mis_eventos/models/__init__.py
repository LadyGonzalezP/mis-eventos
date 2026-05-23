"""Modelos SQLModel - se importan aqui para que Alembic los detecte."""

from mis_eventos.models.user import User, UserRole

__all__ = ["User", "UserRole"]
