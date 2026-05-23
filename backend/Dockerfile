# syntax=docker/dockerfile:1.6

# Imagen base con Python 3.12 slim
FROM python:3.12-slim AS base

# uv - package manager moderno (10-100x mas rapido que pip)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Crear usuario no-root para correr la app
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

# Variables para instalacion limpia
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Instalar dependencias del sistema (psycopg2 necesita libpq)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias y instalar (cache layer separado)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project 2>/dev/null || uv sync --no-install-project

# Copiar codigo fuente
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# Instalar el proyecto en si
RUN uv sync 2>/dev/null || uv sync --frozen

# Cambiar a usuario no-root
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Entrypoint: corre migraciones y luego arranca uvicorn
# Si no hay migraciones todavia, alembic upgrade head es no-op
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn mis_eventos.main:app --host 0.0.0.0 --port 8000"]
