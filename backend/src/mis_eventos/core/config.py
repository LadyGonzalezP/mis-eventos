"""Configuracion central de la aplicacion.

Toda la configuracion vive en un solo lugar. Los valores sensibles (secrets,
DB URLs) se leen del archivo `.env`; el resto tiene defaults razonables.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Configuracion tipada del sistema. Lee `.env` automaticamente."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Base de datos ---
    database_url: str = "postgresql://postgres:postgres@localhost:5432/mis_eventos"

    # --- JWT ---
    jwt_secret: str = "change-me-in-production-please-use-a-real-secret"
    jwt_expiration_hours: int = 24
    jwt_algorithm: str = "HS256"

    # --- CORS ---
    cors_origins: str = "http://localhost:5173"

    # --- Observabilidad ---
    log_level: str = "INFO"

    # --- App metadata ---
    app_version: str = "0.1.0"
    app_name: str = "Mis Eventos API"

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista de origenes CORS parseados desde la variable separada por coma."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
