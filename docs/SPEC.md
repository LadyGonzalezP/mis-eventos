# SPEC — Mis Eventos

> **Plataforma web Full Stack para gestión de eventos**
> Reto técnico Serviinformación · Senior Developer / Tech Lead · Colombia 2026
> Plazo: 5 días hábiles desde 22-may-2026 · Deadline objetivo: jueves 28-may-2026

---

## 1. Objetivo

Construir una aplicación web que permita a la empresa **Mis Eventos** gestionar su operación de forma centralizada, reemplazando los procesos 100% manuales actuales. El sistema debe permitir a **organizadores** crear y gestionar eventos con sesiones programadas, a **asistentes** inscribirse en autoservicio respetando cupos, y a **administradores** supervisar todo el sistema.

**Criterio de éxito del producto:** un asistente puede registrarse, encontrar un evento e inscribirse en menos de 2 minutos sin asistencia humana.

**Criterio de éxito del reto:** entrega que demuestre criterio de ingeniería sólido —no solo código que funciona— alineado con la rúbrica (20% funcionalidad, 20% decisiones documentadas, 15% IA con criterio, 15% calidad, 15% CI/CD, 8% seguridad, 7% observabilidad).

---

## 2. Alcance

### ✅ Dentro del alcance (obligatorio MVP)

- Autenticación con JWT + 3 roles (RBAC)
- CRUD de eventos con state machine de 4 estados
- CRUD de sesiones con ponentes asignados
- Validación de conflictos de horario por ponente
- Inscripción de asistentes con control de cupo
- Búsqueda y filtros de eventos con paginación
- Frontend responsive (móvil + desktop) con feedback visual
- OpenAPI/Swagger autogenerado
- Docker + Docker Compose funcional
- CI/CD con GitHub Actions
- Tests con cobertura > 50% backend
- Logging estructurado JSON + endpoint `/health`

### ⭐ Bonus (solo si se completa el MVP antes del jueves)

- IA en producto: generación automática de descripciones desde el título
- Deploy a la nube (Fly.io o Railway)
- CORS restrictivo + headers HTTP de seguridad
- `request_id` único por petición en logs

### ❌ Fuera del alcance (declarado, no deuda oculta)

| Funcionalidad | Razón |
|---|---|
| Notificaciones por email | Requiere SMTP, fuera del scope |
| Pagos / eventos pagos | No pedido |
| Upload de imágenes | No esencial |
| Reset de password / verificación de email | Out of scope |
| Dashboard de métricas avanzadas | Modelo lo soporta, UI queda para después |
| Internacionalización | Solo español |
| App móvil nativa | Web responsive cubre móvil |
| Soft delete / audit log | Complica el modelo |
| Multi-tenant | Una sola "Mis Eventos" |
| QR de check-in | Complica scope |

---

## 3. Usuarios y roles (RBAC)

| Rol | Puede | NO puede |
|---|---|---|
| 👤 **Asistente** | Ver eventos publicados · Inscribirse · Ver "mis eventos" · Cancelar su inscripción | Crear/editar eventos · Ver borradores |
| 🎯 **Organizador** | Todo lo del Asistente · Crear sus eventos · Editar/cancelar SUS eventos · Crear sesiones · Asignar ponentes · Ver inscritos a sus eventos | Editar eventos de otros · Vistas de Admin |
| 🛡️ **Admin** | Todo lo del Organizador · Ver TODOS los eventos · Editar/cancelar cualquier evento · Gestionar usuarios y roles | — |

**Reglas críticas de permisos:**
- Solo el creador del evento (o un Admin) puede editarlo
- Solo Admins pueden cambiar el rol de un usuario
- En registro, el rol seleccionable es solo `Asistente` u `Organizador` (Admin se crea por seed o asignación manual)

---

## 4. Funcionalidades — detalle por dominio

### 4.1 Autenticación

**Registro** `POST /auth/register`
- Campos: `name`, `email`, `password`, `role` (asistente | organizador)
- Validaciones: email único, password ≥ 8 chars con al menos 1 número
- Devuelve: JWT + datos del usuario

**Login** `POST /auth/login`
- Campos: `email`, `password`
- Devuelve: JWT + datos del usuario
- Expiración: 24h (configurable por `.env`)

**Logout** — frontend borra el token. Backend stateless (sin endpoint).

### 4.2 Eventos

**Atributos:**
- `id` (UUID), `name` (≤200), `description` (≤2000), `start_date`, `end_date` (>start), `location` (≤200), `capacity` (>0), `status` (enum), `organizer_id` (FK), `created_at`, `updated_at`

**State machine:**

```
       (al crear)
         ↓
    [borrador] ──── (publish) ───→ [publicado]
                                       │
                                       ├── (cancel) ──→ [cancelado]
                                       │
                                       └── (fecha pasada) ──→ [finalizado]
```

- `finalizado` y `cancelado` son terminales (no se vuelve atrás)
- Solo se permite inscripción cuando `status = publicado`
- Para publicar se requiere ≥ 1 sesión

**Búsqueda y filtros (`GET /events`):**
- `?q=texto` → ILIKE en `name`
- `?status=publicado` → solo Admin puede ver no-publicados
- `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` → rango
- `?page=1&limit=10` → paginación (default 10, max 100)
- Orden default: `start_date ASC`

### 4.3 Sesiones y ponentes

**Speaker:** `id`, `name`, `bio`, `email` — entidad reusable entre eventos.

**Session:** `id`, `event_id`, `title`, `description`, `start_time`, `end_time`, `speaker_id` (nullable), `capacity` (≤ capacity del evento padre, >0).

**Reglas:**
- `start_time`/`end_time` deben estar dentro del rango del evento padre
- `capacity` de sesión ≤ `capacity` del evento padre
- Eliminar Speaker → sus sesiones quedan con `speaker_id = NULL` (ON DELETE SET NULL)
- Eliminar Event → cascadea sesiones y registros (ON DELETE CASCADE)

### 4.4 Validación de conflictos de horario ⭐

**Regla:** un mismo ponente no puede estar asignado a dos sesiones que se solapan en el tiempo, sin importar si son del mismo evento o de eventos distintos.

**Algoritmo (al crear/editar sesión):**

```
1. Si la sesión no tiene speaker_id → OK (sin conflicto posible)
2. Buscar todas las sesiones existentes con el mismo speaker_id (excluyendo la propia en edit)
3. Para cada sesión existente:
     if (nueva.start_time < existente.end_time) AND
        (nueva.end_time > existente.start_time):
        → CONFLICTO → HTTP 409 con detalle
4. Si ninguna se solapa → guardar
```

**Respuesta de conflicto (HTTP 409):**
```json
{
  "error": "schedule_conflict",
  "message": "El ponente Juan Pérez ya tiene una sesión en ese horario",
  "conflict_with": {
    "session_id": "...",
    "event_name": "Conferencia XYZ",
    "start_time": "2026-06-01T10:00:00",
    "end_time": "2026-06-01T11:30:00"
  }
}
```

**Tests obligatorios:**
- ✅ Sesiones que no se solapan → pasa
- ✅ Sesiones consecutivas (`end_time` = `start_time`) → pasa
- ❌ Solapamiento total → falla
- ❌ Solapamiento parcial → falla
- ❌ Sesión nueva dentro de otra existente → falla
- ✅ Sesiones simultáneas con ponentes distintos → pasa

### 4.5 Inscripciones

**Inscribirse** `POST /events/{id}/register` (sin body)
- Cualquier usuario autenticado
- Validaciones: evento en `publicado`, cupos > 0, no duplicado

**Cancelar inscripción** `DELETE /events/{id}/register`
- El propio usuario inscrito

**Mis eventos** `GET /me/registrations`
- Lista de eventos donde el usuario está inscrito + estado de cada uno

### 4.6 ⭐ Bonus: IA generadora de descripciones

`POST /ai/generate-description`
- Body: `{ "title": "Conferencia de IA 2026" }`
- Output: `{ "description": "Texto generado de 150-300 palabras..." }`
- Proveedor: Groq + Llama 3.3 (free tier)
- Reutiliza el patrón `get_llm()` de LexAudit (provider-agnostic)
- Manejo de error: si falla el LLM → HTTP 503 con mensaje claro

---

## 5. Modelo de datos

```
┌─────────────┐
│    User     │
│─────────────│
│ id (UUID)   │
│ name        │
│ email (UQ)  │
│ password_h  │
│ role (enum) │
│ created_at  │
└──────┬──────┘
       │ 1
       │ N (como organizer_id)
       ↓
┌─────────────┐         ┌──────────────┐
│    Event    │1───────N│   Session    │
│─────────────│         │──────────────│
│ id (UUID)   │         │ id (UUID)    │
│ name        │         │ event_id (FK)│
│ description │         │ title        │
│ start_date  │         │ description  │
│ end_date    │         │ start_time   │
│ location    │         │ end_time     │
│ capacity    │         │ capacity     │
│ status      │         │ speaker_id   │──┐
│ organizer_id│──→ User │              │  │ (nullable, SET NULL)
│ created_at  │         └──────────────┘  │
│ updated_at  │                            │
└──────┬──────┘                            │ N
       │ M                                 │ 1
       │ N (M:N via Registration)          ↓
       ↓                            ┌──────────────┐
┌─────────────────┐                 │   Speaker    │
│  Registration   │                 │──────────────│
│─────────────────│                 │ id (UUID)    │
│ id              │                 │ name         │
│ event_id (FK)   │                 │ bio          │
│ user_id (FK)    │                 │ email        │
│ registered_at   │                 └──────────────┘
│ UNIQUE(ev,user) │
└─────────────────┘
```

**Restricciones:**
- `User.email` único
- `Registration.(event_id, user_id)` único
- IDs: UUID v4 en todas las entidades

**Cascadas:**
- `Event` deleted → `Session`s y `Registration`s eliminados (CASCADE)
- `Speaker` deleted → `Session.speaker_id` queda NULL (SET NULL)

---

## 6. API surface (resumen)

### Convención de URLs

Todos los endpoints **de negocio** están prefijados con **`/api/v1/`** para versionado explícito desde día 1. Los endpoints **de sistema** (`/health`, `/docs`, `/openapi.json`) **no llevan prefijo** porque no son parte de la API versionada.

**Ejemplos:**
- `POST /api/v1/auth/login` — endpoint de negocio (versionado)
- `GET /health` — endpoint de sistema (sin versionar)

**Beneficio:** poder lanzar `/api/v2/` en el futuro sin romper clientes existentes.

### Formato estándar de respuesta de error

Todos los endpoints devuelven errores con este **formato consistente**:

```json
{
  "error": "machine_readable_code",
  "detail": "Mensaje legible en español",
  "context": {}
}
```

**Ejemplos:**
- `{"error": "schedule_conflict", "detail": "...", "context": {"session_id": "...", "event_name": "..."}}`
- `{"error": "event_full", "detail": "...", "context": {"available_slots": 0}}`
- `{"error": "forbidden", "detail": "...", "context": {}}`

**Implementación:** custom exception handlers en `core/exceptions.py` con clases `AppError` tipadas.

### OpenAPI tags

Cada router agrupa endpoints con un `tag` legible en Swagger UI:
- `auth` — Autenticación y registro
- `events` — Gestión de eventos
- `sessions` — Sesiones y conflictos
- `speakers` — Ponentes
- `registrations` — Inscripciones
- `users` — Gestión de usuarios (Admin)
- `system` — Health check y meta endpoints

### Auth
- `POST /auth/register` — registro
- `POST /auth/login` — login

### Eventos
- `GET /events` — listado público con filtros
- `POST /events` — crear (Organizador/Admin)
- `GET /events/{id}` — detalle
- `PATCH /events/{id}` — editar (dueño o Admin)
- `DELETE /events/{id}` — borrar (solo si borrador)
- `POST /events/{id}/publish` — publicar
- `POST /events/{id}/cancel` — cancelar

### Sesiones
- `GET /events/{event_id}/sessions` — listar sesiones de un evento
- `POST /events/{event_id}/sessions` — crear sesión (dueño o Admin)
- `GET /sessions/{id}` — detalle
- `PATCH /sessions/{id}` — editar (dueño del evento o Admin)
- `DELETE /sessions/{id}` — borrar (dueño del evento o Admin)

### Ponentes
- `GET /speakers` — listar (autenticado)
- `POST /speakers` — crear (Organizador/Admin)
- `GET /speakers/{id}` — detalle
- `PATCH /speakers/{id}` — editar (Admin)
- `DELETE /speakers/{id}` — borrar (Admin)

### Inscripciones
- `POST /events/{id}/register` — inscribirse
- `DELETE /events/{id}/register` — cancelar inscripción
- `GET /me/registrations` — mis eventos inscritos

### Usuarios (Admin)
- `GET /users` — listar usuarios (Admin)
- `PATCH /users/{id}/role` — cambiar rol (Admin)

### Sistema
- `GET /health` — health check (público)
- `GET /docs` — Swagger UI
- `GET /openapi.json` — OpenAPI spec

### ⭐ Bonus
- `POST /ai/generate-description` — generar descripción con IA

---

## 7. Pantallas del frontend

| # | Pantalla | Acceso | Propósito |
|---|---|---|---|
| 1 | Login | Público | Iniciar sesión |
| 2 | Registro | Público | Crear cuenta |
| 3 | Listado de eventos | Público | Buscar + filtrar eventos publicados |
| 4 | Detalle de evento | Público | Info + sesiones + botón "Inscribirme" |
| 5 | Mis eventos | Auth | Eventos inscritos (asistente) / organizados (organizador) |
| 6 | Crear/editar evento | Organizador/Admin | Formulario con sesiones |
| 7 | Gestionar sesiones | Organizador/Admin | CRUD de sesiones de un evento |
| 8 | Gestión de usuarios | Admin | Lista + cambio de rol |
| 9 | 404 / 403 | Todos | Errores de navegación y permiso |

**Reglas de UX:**
- Loading states durante peticiones HTTP
- Toast/snackbar para éxito y error
- Confirmación modal antes de acciones destructivas
- Botones deshabilitados durante envío
- Responsive desde 320px (móvil) hasta 1440px (desktop)

---

## 8. Stack técnico

| Capa | Tecnología | Versión |
|---|---|---|
| **Backend lenguaje** | Python | 3.12 |
| **Backend framework** | FastAPI | latest |
| **ORM** | SQLModel (sobre SQLAlchemy 2) | latest |
| **Migraciones** | Alembic | latest |
| **Validación** | Pydantic v2 | (incluido en SQLModel) |
| **Auth** | python-jose (JWT) + passlib[bcrypt] | latest |
| **Base de datos** | PostgreSQL | 16 |
| **Tests backend** | pytest + pytest-asyncio + httpx | latest |
| **Lint backend** | Ruff | latest |
| **Package manager** | uv | latest |
| **Frontend lenguaje** | TypeScript | 5 |
| **Frontend framework** | React | 18 |
| **Build tool** | Vite | latest |
| **UI** | Tailwind CSS + shadcn/ui | latest |
| **Estado cliente** | Zustand | latest |
| **Estado servidor** | TanStack Query | v5 |
| **HTTP client** | Axios | latest |
| **Tests frontend** | Vitest + Testing Library | latest |
| **Lint frontend** | ESLint + Prettier | latest |
| **Containers** | Docker + Docker Compose | latest |
| **CI** | GitHub Actions | — |
| **IA (bonus)** | Groq + Llama 3.3 | free tier |
| **Deploy (bonus)** | Fly.io o Railway | — |

Justificación detallada de cada elección en `ARCHITECTURE.md`.

---

## 9. Comandos

### Levantar todo el stack (1 comando)
```bash
docker compose up --build
# Postgres en :5432
# Backend en :8000 (Swagger en :8000/docs)
# Frontend en :5173
```

### Backend en local sin Docker
```bash
cd backend
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn mis_eventos.main:app --reload
```

### Frontend en local sin Docker
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Tests
```bash
# Backend con cobertura
cd backend && uv run pytest --cov=src --cov-report=term --cov-report=html

# Frontend
cd frontend && npm test
```

### Lint
```bash
cd backend && uv run ruff check .
cd frontend && npm run lint
```

### Migraciones (Alembic)
```bash
# Nueva migración auto-generada
cd backend && uv run alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
cd backend && uv run alembic upgrade head

# Revertir última
cd backend && uv run alembic downgrade -1
```

### Crear Admin (seed)
```bash
cd backend && uv run python -m mis_eventos.seed --admin-email admin@example.com
```

---

## 10. Estructura de carpetas

```
D:\mis-eventos\
├── backend/
│   ├── src/mis_eventos/
│   │   ├── api/                  # Routers FastAPI
│   │   │   ├── auth.py
│   │   │   ├── events.py
│   │   │   ├── sessions.py
│   │   │   ├── speakers.py
│   │   │   ├── registrations.py
│   │   │   ├── users.py
│   │   │   └── health.py
│   │   ├── core/                 # Config, seguridad, deps
│   │   │   ├── config.py
│   │   │   ├── security.py       # JWT, hashing, RBAC deps
│   │   │   └── logging.py        # Logging JSON
│   │   ├── models/               # SQLModel entities
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   ├── session.py
│   │   │   ├── speaker.py
│   │   │   └── registration.py
│   │   ├── schemas/              # Pydantic DTOs
│   │   │   ├── auth.py
│   │   │   ├── event.py
│   │   │   └── ...
│   │   ├── services/             # Lógica de negocio
│   │   │   ├── conflict_validator.py
│   │   │   ├── capacity.py
│   │   │   └── event_state.py
│   │   ├── db/
│   │   │   └── session.py        # Engine + get_db dep
│   │   ├── llm/                  # Bonus: provider de IA
│   │   │   └── provider.py
│   │   ├── seed.py               # Crear admin inicial
│   │   └── main.py               # FastAPI app
│   ├── migrations/               # Alembic
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_events.py
│   │   ├── test_sessions.py
│   │   ├── test_conflict_validator.py
│   │   ├── test_registrations.py
│   │   └── conftest.py
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/           # UI reutilizables
│   │   │   ├── ui/               # shadcn components
│   │   │   ├── EventCard.tsx
│   │   │   ├── SessionList.tsx
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── EventList.tsx
│   │   │   ├── EventDetail.tsx
│   │   │   ├── MyEvents.tsx
│   │   │   ├── EventForm.tsx
│   │   │   └── UserManagement.tsx
│   │   ├── stores/               # Zustand
│   │   │   └── authStore.ts
│   │   ├── api/                  # Llamadas al backend
│   │   │   ├── client.ts         # Axios instance + interceptors
│   │   │   ├── events.ts
│   │   │   └── ...
│   │   ├── hooks/                # Custom hooks
│   │   │   ├── useEvents.ts
│   │   │   └── useAuth.ts
│   │   ├── lib/                  # Utils
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── .env.example
├── docs/
│   ├── SPEC.md                   # Este archivo
│   ├── ARCHITECTURE.md
│   └── AI_USAGE.md
├── .github/workflows/
│   └── ci.yml
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 11. Estilo de código

### Backend (Python)
- **Type hints completos** — todo argumento, retorno y variable importante tipada
- **Ruff** como linter (config en `pyproject.toml`)
- **Docstrings** en funciones de servicio (lógica de negocio)
- **Snake_case** para funciones, variables, módulos
- **PascalCase** para clases (modelos, schemas, enums)
- **Imports ordenados**: stdlib → third-party → local (Ruff lo enforza)
- **No `print()`** en código de producción — solo logger
- **Excepciones específicas** — nunca `except:` ni `except Exception:` sin re-raise
- **No mutar argumentos** — devolver nuevos objetos
- **Funciones pequeñas** — idealmente < 30 líneas

### Frontend (TypeScript)
- **`strict: true`** en `tsconfig.json` — no `any` salvo justificación
- **ESLint + Prettier** con config estándar React
- **CamelCase** para variables y funciones, **PascalCase** para componentes
- **Componentes funcionales** únicamente (no class components)
- **Hooks** para estado y efectos
- **Custom hooks** para lógica reutilizable (`useEvents`, `useAuth`)
- **Props tipadas** con interface o type
- **Sin inline styles complejos** — usar Tailwind classes
- **Accesibilidad (a11y) por defecto** — componentes shadcn/ui basados en Radix UI cumplen WAI-ARIA automáticamente; usar `aria-label` en botones sin texto, `role` en elementos custom, contraste mínimo AA

### General
- **Conventional Commits** obligatorio:
  - `feat:` nueva feature
  - `fix:` corrección de bug
  - `docs:` cambios solo en documentación
  - `test:` agregar/cambiar tests
  - `refactor:` refactor sin cambio de comportamiento
  - `chore:` mantenimiento (deps, config)
  - `style:` formato/whitespace
- **Commits atómicos** — un cambio lógico por commit
- **Sin TODOs sin resolver** al entregar
- **Sin código comentado** muerto
- **Sin excepciones silenciosas** (`except: pass`)

---

## 12. Estrategia de testing

### Backend — pytest

**Cobertura objetivo:** > 50% sobre lógica de negocio (`services/` + endpoints críticos).

**Qué SÍ se testea:**
- ✅ Algoritmo de validación de conflictos de horario (casos exhaustivos)
- ✅ State machine de eventos (transiciones válidas e inválidas)
- ✅ Control de cupos (registrarse con cupos / sin cupos / duplicado)
- ✅ Permisos RBAC (Asistente intenta crear evento → 403)
- ✅ Validación de inputs (email mal formado, password corto, etc.)
- ✅ Hashing de password (passwords no se guardan en plano)
- ✅ JWT (expiración, payload correcto, rechazo de token inválido)

**Qué NO se testea:**
- ❌ Frameworks externos (FastAPI, SQLModel) — son responsabilidad del mantenedor
- ❌ Llamadas a Groq/IA en tests unitarios — se mockean

**Estructura de tests:**
- `conftest.py` con fixtures: DB en memoria SQLite (o testcontainers), cliente HTTPX, usuarios de prueba con tokens
- Un archivo por dominio (`test_events.py`, `test_sessions.py`, etc.)
- Tests con nombres descriptivos: `test_conflict_when_speaker_double_booked`

### Frontend — Vitest + Testing Library

**Cobertura objetivo:** componentes clave de UX crítica.

**Qué SÍ se testea:**
- ✅ Formulario de creación de evento (validaciones + submit)
- ✅ Card/listado de eventos (renderizado con datos)
- ✅ Flow de inscripción (botón "Inscribirme" → confirmación)
- ✅ Auth: redirect si no logueado

**Qué NO se testea:**
- ❌ shadcn/ui internals
- ❌ Llamadas reales al backend — se mockean con MSW si hace falta

### CI

- **GitHub Actions** corre en cada `push` y `pull_request`:
  - Backend: `ruff check` + `pytest --cov` con threshold de cobertura
  - Frontend: `npm run lint` + `npm test`
- Build de Docker images como smoke test
- CI debe estar **verde** antes de mergear a `main`

---

## 13. Requisitos no funcionales

### Seguridad
- Passwords con **bcrypt** (cost factor ≥ 12)
- JWT firmado con secret de ≥ 32 bytes (en `.env`)
- Expiración del JWT: 24h
- Secretos solo en `.env` (nunca en código)
- Validación + sanitización Pydantic en TODOS los endpoints
- ⭐ Bonus: CORS configurado restrictivo (whitelist de orígenes)
- ⭐ Bonus: Headers HTTP: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`

**Cobertura OWASP Top 10 (2021):**

| # | Riesgo OWASP | Cómo lo cubrimos |
|---|---|---|
| A01 | **Broken Access Control** | RBAC con 3 roles + dependency `require_role()` en cada endpoint protegido |
| A02 | **Cryptographic Failures** | Passwords con bcrypt (cost ≥ 12) · JWT firmado HS256 con secret ≥ 32 bytes · HTTPS en deploy |
| A03 | **Injection** | SQL injection imposible vía SQLModel (parametrización automática) · validación Pydantic en todos los inputs |
| A04 | **Insecure Design** | Spec-driven · state machine pura · separación servicios/endpoints |
| A05 | **Security Misconfiguration** | `.env` gitignored · `.env.example` documentado · CORS restrictivo · headers HTTP de seguridad |
| A06 | **Vulnerable Components** | `uv.lock` y `package-lock.json` commiteados · dependencias modernas |
| A07 | **Identification & Auth Failures** | JWT con expiración · rate limit por IP en login (mejora futura) · password mínimo 8+1 número |
| A08 | **Software & Data Integrity** | Lock files · CI ejecuta lint+tests antes de merge · Conventional Commits |
| A09 | **Logging Failures** | Logs JSON estructurados · `request_id` por petición · errores con stack trace |
| A10 | **SSRF** | No hay endpoints que reciban URLs externas (los bonus IA usan endpoint fijo de Groq) |

**Lo declarado como mejora futura:** rate limiting por IP, autenticación 2FA, audit log inmutable.

### Observabilidad
- **Logging JSON estructurado** con niveles `info | warn | error`
- Cada request loggea: `method`, `path`, `status`, `duration_ms`, `user_id` (si auth), `request_id`
- Endpoint `/health` devuelve:
  ```json
  {
    "status": "ok",
    "db": "ok",
    "version": "1.0.0",
    "timestamp": "2026-05-28T18:00:00Z"
  }
  ```
- Errores no controlados se loggean con stack trace completo
- ⭐ Bonus: `request_id` (UUID) generado por middleware, propagado en headers de respuesta y logs

### Performance
- Paginación obligatoria en listados (default 10, max 100)
- Índices DB en columnas filtradas: `Event.name` (GIN para ILIKE), `Event.start_date`, `Event.status`
- Target informal: < 300ms reads / < 800ms writes

---

## 14. Criterios de aceptación

✅ `docker compose up` levanta todo el stack en menos de **5 minutos** desde clon limpio
✅ Un asistente puede registrarse, buscar un evento publicado e inscribirse desde el frontend
✅ Un organizador puede crear un evento con 2 sesiones, asignar ponentes y publicarlo
✅ Si se intenta crear una sesión con un ponente ya ocupado → HTTP 409 con detalle del choque
✅ Si se intenta inscribir a un evento sin cupo → HTTP 400/409 con mensaje claro
✅ `/docs` muestra toda la API documentada (Swagger UI)
✅ `/health` devuelve 200 con info de DB + versión
✅ Tests pasan en CI con cobertura > 50% en backend
✅ Commits siguen Conventional Commits
✅ `SPEC.md`, `ARCHITECTURE.md`, `AI_USAGE.md`, `README.md` están completos
✅ No hay TODOs, secretos hardcoded, ni excepciones silenciosas en el código

---

## 15. Boundaries

### ✅ ALWAYS DO (sin necesidad de confirmar)

- Escribir tests para lógica de negocio antes de mergear a `main`
- Validar inputs con Pydantic en TODOS los endpoints del backend
- Usar Conventional Commits en cada commit
- Hashear passwords con bcrypt (nunca guardar plano)
- Leer secretos solo de `.env` (jamás hardcodear)
- Loggear errores con stack trace + `request_id`
- Type hints completos en Python; TypeScript estricto en frontend
- Manejar errores HTTP con códigos correctos (400, 401, 403, 404, 409, 500)
- Mantener CI en verde antes de mergear
- **Toda migración Alembic debe ser reversible** (tener `downgrade()` válido y testeado con `alembic downgrade -1` antes de mergear)
- Devolver errores con el **formato estándar** definido en §6 (con `error`, `detail`, `context`)

### ⚠️ ASK FIRST (pedir confirmación antes)

- Agregar nuevas dependencias (`uv add` / `npm install`)
- Cambiar el esquema de la base de datos (nuevas migraciones)
- Modificar el contrato público de endpoints existentes
- Cambiar la estructura de carpetas establecida
- Saltarse un test que está fallando
- Implementar features no acordadas en `SPEC.md`
- Cambiar versiones mayores de dependencias clave (FastAPI, React)

### 🚫 NEVER DO

- Commitear secretos, API keys, passwords, tokens
- Usar `git commit --no-verify` (saltar hooks)
- Force push a `main`
- Borrar datos sin confirmación explícita del usuario
- Atribuir commits a Claude (sin "Co-Authored-By: Claude")
- Dejar lógica de negocio sin tests
- Inventar URLs, librerías o APIs que no existen (verificar primero)
- Implementar features fuera del scope acordado
- Usar `except:` o `except Exception:` sin re-raise

---

## 16. Plan de 5 días

| Día | Fecha | Foco |
|---|---|---|
| **Día 1 (½)** | Vie 22 may (tarde) | `SPEC.md` ✅ + `ARCHITECTURE.md` + setup repo + Docker base + `/health` |
| **FDS (opt)** | Sáb-Dom 23-24 | Buffer si quiere adelantar |
| **Día 2** | Lun 25 may | Modelos + migraciones + Auth + RBAC |
| **Día 3** | Mar 26 may | CRUD Eventos + Sesiones + conflictos + inscripciones + tests |
| **Día 4** | Mié 27 may | Frontend completo: Auth + Listado + Detalle + Formularios + Mis eventos |
| **Día 5** | Jue 28 may | CI/CD + docs (`AI_USAGE.md` + `README.md`) + polish + verificación final |
| **Buffer** | Vie 29 may | Bonus (IA en producto + deploy) o cerrar pendientes |

**Deadline objetivo:** jueves 28-may-2026 al final del día (confirmar con el correo de Serviinformación).

---

## 17. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| 5 días es corto para todo el scope | Alta | Bonus solo si MVP está al 100% |
| Conflictos de horario son lógica delicada | Media | Tests exhaustivos del algoritmo (6+ casos) |
| Frontend puede consumir más de un día | Media | Usar shadcn/ui (componentes pre-armados) |
| Falla la demo en evaluación | Baja | Docker Compose + deploy bonus = doble red |
| Test de cobertura no llega al 50% | Baja | Priorizar tests de servicios (lógica de negocio) |
| Deps con incompatibilidades | Media | Lock files (`uv.lock`, `package-lock.json`) commiteados |

---

## 18. Referencias

- **Reto técnico:** `c:\Users\LADY\Downloads\Prueba_Tecnica_Colombia_2026_v2.pdf`
- **Patrones reutilizados de LexAudit:**
  - `docs/decisions.md` → `ARCHITECTURE.md` (mismo formato de trade-offs)
  - `docs/ai-usage.md` → `AI_USAGE.md` (mismo formato spec-driven)
  - `get_llm()` provider-agnostic (para bonus de IA)
  - GitHub Actions CI (mismo workflow base)
- **Convención de paths:** `D:\mis-eventos\` (siguiendo `D:\lexaudit\`, `D:\leaderbot\`)

---

**Versión:** 1.0 · **Fecha:** 22-may-2026 · **Autora:** Lady Katherine Gonzalez
