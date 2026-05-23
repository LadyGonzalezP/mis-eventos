# TODO — Mis Eventos

> Lista accionable derivada de [`plan.md`](./plan.md) · Marcá `[x]` a medida que completás.
> **Regla:** no avanzar al siguiente slice sin pasar el checkpoint del actual.

---

## 🏗️ SLICE 0 — Foundations · Vie 22-may (tarde) · Task #29

### Estructura del repo
- [ ] `git init` en `D:\mis-eventos\`
- [ ] Crear estructura de carpetas: `backend/src/mis_eventos/{api,core,db,llm,models,schemas,services}`, `backend/tests`, `backend/migrations`, `frontend/src/{api,components,hooks,lib,pages,stores}`, `frontend/tests`, `.github/workflows`
- [ ] `.gitignore` con: `__pycache__`, `.env`, `node_modules`, `dist`, `.venv`, `*.pyc`, `.coverage`, `htmlcov`, `data/`
- [ ] Initial commit: `chore: bootstrap project structure`

### Backend mínimo
- [ ] `backend/pyproject.toml` con deps: `fastapi`, `sqlmodel`, `alembic`, `psycopg2-binary`, `python-jose[cryptography]`, `passlib[bcrypt]`, `python-dotenv`, `pydantic-settings`, `uvicorn`, `structlog`
- [ ] Dev deps: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`, `ruff`
- [ ] `backend/src/mis_eventos/main.py` con FastAPI app
- [ ] **Router con prefijo `/api/v1/`** configurado en `main.py` (SPEC §6)
- [ ] `backend/src/mis_eventos/core/exceptions.py` con clase base `AppError(Exception)` + handlers que devuelven formato `{error, detail, context}` (SPEC §6)
- [ ] **OpenAPI tags** definidos al instanciar cada router: `auth`, `events`, `sessions`, `speakers`, `registrations`, `users`, `system` (SPEC §6)
- [ ] `backend/src/mis_eventos/api/health.py` con endpoint `/health` que pinguea DB (sin prefix /api/v1/)
- [ ] `backend/src/mis_eventos/core/config.py` con `Settings` (pydantic-settings, lee `.env`)
- [ ] `backend/src/mis_eventos/db/session.py` con `engine` y `get_db` dependency
- [ ] `backend/Dockerfile` (python:3.12-slim, uv install, copy src, uvicorn)
- [ ] `backend/.env.example` con: `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRATION_HOURS`, `CORS_ORIGINS`, `LOG_LEVEL`

### Alembic
- [ ] `cd backend && uv run alembic init migrations`
- [ ] Configurar `alembic.ini` con `DATABASE_URL` desde env
- [ ] Configurar `env.py` para importar `SQLModel.metadata`

### Docker Compose
- [ ] `docker-compose.yml` con servicios: `db` (postgres:16-alpine), `backend`
- [ ] Healthcheck para postgres
- [ ] Volume para datos de Postgres
- [ ] `backend` depende de `db` con `condition: service_healthy`

### Frontend skeleton
- [ ] `cd frontend && npm create vite@latest . -- --template react-ts`
- [ ] Instalar: `tailwindcss`, `postcss`, `autoprefixer`, `@radix-ui/*` (vía shadcn-ui CLI), `zustand`, `@tanstack/react-query`, `axios`, `react-router-dom`
- [ ] Setup Tailwind + shadcn/ui
- [ ] `frontend/Dockerfile` (multi-stage: build + nginx para servir static)
- [ ] `frontend/.env.example` con `VITE_API_BASE_URL`

### CI skeleton
- [ ] `.github/workflows/ci.yml` con 2 jobs:
  - `backend`: setup uv, install, ruff check, pytest
  - `frontend`: setup node, npm ci, lint, vitest run

### Docs iniciales
- [ ] `docs/ARCHITECTURE.md` v1 con:
  - [ ] Diagrama Mermaid del sistema (User → Frontend → Backend → DB)
  - [ ] Tabla de stack
  - [ ] 2 trade-offs iniciales (FastAPI vs Django, React vs Vue)
- [ ] `README.md` v1 con:
  - [ ] Descripción 1 párrafo
  - [ ] **Diagrama Mermaid básico** (la versión completa se completa en S7)
  - [ ] Quick start (`docker compose up`)
  - [ ] Enlaces a docs

### ✅ Checkpoint CP0
- [ ] `docker compose down -v && docker compose up --build` levanta limpio
- [ ] `curl http://localhost:8000/health` devuelve JSON con `"db":"ok"`
- [ ] CI corre y aparece verde en GitHub
- [ ] Commit final del slice: `feat(setup): docker compose + /health + CI skeleton`

---

## 🔐 SLICE 1 — Auth + RBAC · Lun 25-may (AM) · Task #30

### Backend Auth
- [ ] `backend/src/mis_eventos/models/user.py` — SQLModel User con role enum
- [ ] `backend/src/mis_eventos/schemas/auth.py` — RegisterIn, LoginIn, UserOut, TokenOut
- [ ] `backend/src/mis_eventos/core/security.py`:
  - [ ] `hash_password(plain) -> str` con bcrypt
  - [ ] `verify_password(plain, hashed) -> bool`
  - [ ] `create_access_token(user_id, role) -> str` con expiración
  - [ ] `decode_token(token) -> dict`
  - [ ] `get_current_user` dependency
  - [ ] `require_role(*allowed_roles)` dependency factory
- [ ] `backend/src/mis_eventos/api/auth.py`:
  - [ ] `POST /auth/register` (valida email único, password ≥ 8 + 1 número)
  - [ ] `POST /auth/login` (devuelve token + user)
- [ ] Primera migración Alembic: `uv run alembic revision --autogenerate -m "user table"`
- [ ] `uv run alembic upgrade head`
- [ ] `backend/src/mis_eventos/seed.py` con CLI `--admin-email` para crear admin

### Frontend Auth
- [ ] `frontend/src/api/client.ts` — Axios instance con baseURL y interceptor de auth
- [ ] `frontend/src/stores/authStore.ts` (Zustand) con `user`, `token`, `login`, `logout`, persist a localStorage
- [ ] `frontend/src/pages/Login.tsx` con form (email, password) usando shadcn
- [ ] `frontend/src/pages/Register.tsx` con form (name, email, password, role)
- [ ] `frontend/src/components/ProtectedRoute.tsx` con prop `role?: string`
- [ ] Setup `react-router` con rutas públicas + protegidas
- [ ] Página `/dashboard` placeholder mostrando rol del usuario

### Tests Auth
- [ ] `backend/tests/conftest.py` — fixtures: app cliente, DB en SQLite memory, user factory
- [ ] `backend/tests/test_auth.py`:
  - [ ] `test_register_success`
  - [ ] `test_register_duplicate_email_fails`
  - [ ] `test_register_weak_password_fails`
  - [ ] `test_login_success_returns_token`
  - [ ] `test_login_wrong_password_fails`
  - [ ] `test_token_has_correct_expiration`
  - [ ] `test_rbac_asistente_cannot_access_admin_endpoint`

### Docs
- [ ] `ARCHITECTURE.md` § Decisiones: agregar **JWT vs sesiones server-side**
- [ ] Empezar `docs/AI_USAGE.md` v1 (estructura + 1 ejemplo si aplica)

### ✅ Checkpoint CP1
- [ ] Registrarse desde UI como Organizador → redirect a `/dashboard`
- [ ] JWT visible en `localStorage`
- [ ] `uv run pytest tests/test_auth.py -v` → todos pasan
- [ ] CI verde
- [ ] Commit: `feat(auth): JWT + RBAC con 3 roles`

---

## 📅 SLICE 2 — Events CRUD + State Machine · Lun 25-may (PM) · Task #31

### Backend Events
- [ ] `models/event.py` con `status` enum, `organizer_id` FK
- [ ] Migración Alembic para tabla `event`
- [ ] `schemas/event.py` — EventCreate, EventUpdate, EventOut, EventList
- [ ] `services/event_state.py` — pure state machine: `can_transition(current, target) -> bool`, `valid_next_states(current) -> list`
- [ ] `api/events.py`:
  - [ ] `POST /events` (Organizador/Admin)
  - [ ] `GET /events` con query params `q`, `status`, `date_from`, `date_to`, `page`, `limit`
  - [ ] `GET /events/{id}`
  - [ ] `PATCH /events/{id}` (dueño o Admin)
  - [ ] `DELETE /events/{id}` (solo si borrador)
  - [ ] `POST /events/{id}/publish` (valida ≥1 sesión — pending S3, por ahora solo cambia estado)
  - [ ] `POST /events/{id}/cancel`

### Frontend Events
- [ ] `frontend/src/api/events.ts` — funciones API tipadas
- [ ] `hooks/useEvents.ts` con TanStack Query
- [ ] `pages/EventList.tsx` con paginación + filtros (search input + status dropdown + date range)
- [ ] `pages/EventDetail.tsx`
- [ ] `pages/EventForm.tsx` (crear y editar)
- [ ] `components/EventCard.tsx` reutilizable
- [ ] Toast (shadcn `<Toaster>`) para feedback

### Tests Events
- [ ] `tests/test_event_state.py` con 8 casos de transición:
  - [ ] `borrador → publicado` ✅
  - [ ] `publicado → cancelado` ✅
  - [ ] `publicado → finalizado` ✅
  - [ ] `borrador → finalizado` ❌
  - [ ] `cancelado → publicado` ❌
  - [ ] `finalizado → cualquier cosa` ❌
- [ ] `tests/test_events.py`:
  - [ ] CRUD básico
  - [ ] Búsqueda por nombre parcial
  - [ ] Filtro por estado
  - [ ] Paginación
  - [ ] Asistente no puede crear evento → 403

### Docs
- [ ] `ARCHITECTURE.md` § Decisiones: **state machine como servicio puro vs status libre**

### ✅ Checkpoint CP2
- [ ] Organizador crea evento desde UI, lo publica, lo cancela
- [ ] Asistente lo ve en listado público solo si está `publicado`
- [ ] Búsqueda parcial funciona
- [ ] Paginación funciona (≥ 11 eventos para probar página 2)
- [ ] Tests pasan
- [ ] Commit: `feat(events): CRUD + state machine + búsqueda paginada`

---

## 🎤 SLICE 3 — Sessions + Conflict Validation · Mar 26-may (AM) · Task #32

### Backend Sessions
- [ ] `models/speaker.py`
- [ ] `models/session.py` con FK a Event (cascade) y Speaker (SET NULL)
- [ ] Migraciones para `speaker` y `session`
- [ ] `schemas/session.py`, `schemas/speaker.py`
- [ ] `services/conflict_validator.py` con función `find_conflict(speaker_id, start, end, exclude_session_id=None) -> Optional[Session]`
- [ ] `api/sessions.py`:
  - [ ] `POST /events/{event_id}/sessions` (dueño o Admin)
  - [ ] `GET /events/{event_id}/sessions`
  - [ ] `GET /sessions/{id}`
  - [ ] `PATCH /sessions/{id}` (re-valida conflicto excluyendo la propia)
  - [ ] `DELETE /sessions/{id}`
- [ ] `api/speakers.py` con CRUD
- [ ] Validación: session dentro del rango del event, capacity ≤ event.capacity
- [ ] Actualizar `POST /events/{id}/publish` para validar ≥ 1 sesión

### Frontend Sessions
- [ ] Sub-página "Sesiones" dentro de `/events/:id/edit`
- [ ] Modal/formulario para crear/editar sesión
- [ ] Dropdown/autocomplete de ponentes
- [ ] Manejo del error 409 con mensaje del choque

### Tests Conflicts ⭐ CRÍTICO
- [ ] `tests/test_conflict_validator.py` con AL MENOS estos 6 casos:
  - [ ] `test_no_overlap_passes` — sesiones que no se tocan
  - [ ] `test_consecutive_sessions_pass` — end_time == start_time
  - [ ] `test_total_overlap_fails`
  - [ ] `test_partial_overlap_start_fails`
  - [ ] `test_partial_overlap_end_fails`
  - [ ] `test_new_inside_existing_fails`
  - [ ] `test_existing_inside_new_fails`
  - [ ] `test_same_time_different_speakers_pass`
  - [ ] `test_edit_session_excludes_self` (caso edge)

### Docs
- [ ] `ARCHITECTURE.md` § Decisiones: **validación en servicio vs constraint DB** (la decisión más interesante para defender)
- [ ] `AI_USAGE.md`: si Claude propuso menos casos de test y vos agregaste el "edit_session_excludes_self", anotalo como ejemplo de "bug que IA no detectó"

### ✅ Checkpoint CP3
- [ ] Los 6+ tests de conflictos pasan
- [ ] Crear sesión con choque → 409 + mensaje legible en UI
- [ ] Editar sesión sin cambiar nada → no falla con sí misma
- [ ] Eliminar speaker → sus sesiones quedan con speaker null
- [ ] Commit: `feat(sessions): sesiones con ponente y validación de conflictos`

---

## 🎟️ SLICE 4 — Registrations + My Events · Mar 26-may (PM) · Task #32

### Backend Registrations
- [ ] `models/registration.py` con UNIQUE(event_id, user_id)
- [ ] Migración Alembic
- [ ] `services/capacity.py` con `count_registrations(event_id)`, `available_slots(event_id)`
- [ ] `api/registrations.py`:
  - [ ] `POST /events/{id}/register`
  - [ ] `DELETE /events/{id}/register`
  - [ ] `GET /me/registrations`

### Frontend Registrations
- [ ] Botón "Inscribirme" en `/events/:id` con estado dinámico
- [ ] Página `/me/events`:
  - [ ] Asistente: lista de eventos inscritos
  - [ ] Organizador: lista de eventos organizados (con # inscritos)
- [ ] Cancelar inscripción con confirmación modal

### Tests Registrations
- [ ] `tests/test_registrations.py`:
  - [ ] `test_register_to_published_event`
  - [ ] `test_register_to_draft_fails`
  - [ ] `test_register_duplicate_fails`
  - [ ] `test_register_when_full_fails`
  - [ ] `test_cancel_own_registration`
  - [ ] `test_cannot_cancel_others_registration`

### Docs
- [ ] `ARCHITECTURE.md` § Decisiones: **conteo de cupos vs columna materializada**

### ✅ Checkpoint CP4
- [ ] Inscribirse y aparecer en "mis eventos"
- [ ] Tests pasan
- [ ] Commit: `feat(registrations): inscripción con control de cupo`

---

## 🛡️ SLICE 5 — Backend Hardening · Mié 27-may (AM) · Task #33

### Logging + Observabilidad
- [ ] `core/logging.py` con `structlog` o `python-json-logger`
- [ ] Middleware FastAPI: loggea cada request en JSON
- [ ] Generar `request_id` por request (middleware)
- [ ] Header `X-Request-Id` en respuestas
- [ ] `/health` mejorado con `SELECT 1` y versión

### Seguridad
- [ ] CORS configurado restrictivo (lee `CORS_ORIGINS` de env)
- [ ] Middleware con headers de seguridad
- [ ] Revisión de cada endpoint: validación Pydantic, códigos HTTP correctos
- [ ] Audit: sin `except Exception: pass`, sin TODOs

### Cobertura
- [ ] Agregar tests donde falten para llegar > 50%
- [ ] `uv run pytest --cov=src --cov-fail-under=50 --cov-report=html`
- [ ] Revisar reporte HTML, agregar tests para los módulos con menor cobertura

### Docs
- [ ] `ARCHITECTURE.md` § Observabilidad: formato JSON de logs + request_id flow

### ✅ Checkpoint CP5
- [ ] `pytest --cov-fail-under=50` pasa
- [ ] Logs son JSON parseable
- [ ] `/health` devuelve estructura completa
- [ ] Headers de seguridad presentes (`curl -I localhost:8000`)
- [ ] Commit: `feat(observability): logs JSON + request_id + security headers`

---

## 🎨 SLICE 6 — Frontend Polish + Tests · Mié 27-may (PM) + Jue 28-may (AM) · Tasks #34 y #35

### Polish UI
- [ ] Paginación visual con shadcn `<Pagination>`
- [ ] Loading skeletons en listas
- [ ] Toast consistente en TODAS las acciones (crear, editar, eliminar, registrarse)
- [ ] Modal de confirmación antes de borrar/cancelar
- [ ] Página 404 y 403 (no autorizado)
- [ ] Manejo de error global de Axios (toast con mensaje del backend)

### Responsivo
- [ ] Verificar en 320px (móvil), 768px (tablet), 1440px (desktop)
- [ ] Drawer/hamburguer en móvil si hace falta

### Tests Frontend (Vitest)
- [ ] Setup Vitest + Testing Library + jsdom
- [ ] `tests/EventCard.test.tsx`
- [ ] `tests/EventForm.test.tsx`
- [ ] `tests/LoginForm.test.tsx`
- [ ] `tests/useEvents.test.tsx` (con mock de TanStack Query)
- [ ] `npm test` debe pasar

### ✅ Checkpoint CP6
- [ ] Responsive OK en 3 breakpoints
- [ ] Vitest verde
- [ ] `npm run build` produce dist/ sin errores
- [ ] Commit: `feat(ui): polish + tests Vitest`

---

## 📚 SLICE 7 — Docs + CI verde + Verificación final · Jue 28-may (PM) · Task #36

### ARCHITECTURE.md completo
- [ ] Diagrama Mermaid completo (sistema entero con todos los componentes)
- [ ] Tabla de stack con justificación de cada elección
- [ ] **6 trade-offs documentados** con el formato Decisión/Alternativas/Elegí/Trade-off:
  1. [ ] FastAPI vs Django vs Flask
  2. [ ] SQLModel vs SQLAlchemy puro
  3. [ ] React + Vite vs Next.js
  4. [ ] Zustand + TanStack Query vs Redux Toolkit
  5. [ ] State machine como servicio puro vs status string libre
  6. [ ] Validación de conflictos en servicio vs constraint DB
- [ ] Al menos una decisión "elegí B sobre A y por qué" claramente identificada
- [ ] Sección de lectura del diseño / frase cierre

### AI_USAGE.md completo
- [ ] Herramientas usadas (Claude Code + spec-driven)
- [ ] Metodología spec-driven explicada
- [ ] **Ejemplo 1 — Sugerencia ACEPTADA + por qué**
- [ ] **Ejemplo 2 — Sugerencia RECHAZADA o CORREGIDA + por qué**
- [ ] **Ejemplo 3 — Bug que la IA NO detectó y vos sí**
- [ ] Mención de decisiones que tomaste TÚ (no la IA)

### README.md final (estilo LexAudit — bien explícito + Mermaid)

> Ver template completo en `plan.md` § Slice 7. Debe ser **autosuficiente**: alguien clona el repo y entiende todo sin abrir otro doc.

- [ ] **Header con badges:** CI, cobertura, license
- [ ] **¿Qué hace?** — 2-3 párrafos con problema + solución + valor (igual a LexAudit)
- [ ] **Arquitectura (alto nivel)** con diagrama **Mermaid** completo:
  - [ ] Frontend (React + Vite + TS + Zustand + TanStack + Tailwind)
  - [ ] Backend (FastAPI + SQLModel + Auth + Services + Alembic)
  - [ ] DB (PostgreSQL 16)
  - [ ] Línea HTTP con `/api/v1/*` + JWT
  - [ ] Bonus IA (Groq) con línea punteada
  - [ ] Subgraphs por capa
  - [ ] Colores diferenciados
  - [ ] 2-3 líneas explicando el diagrama después
- [ ] **Quick start** (un comando: `docker compose up`)
- [ ] **Setup local sin Docker** (backend + frontend, paso a paso)
- [ ] **Tests** — comandos + ver reporte HTML de cobertura
- [ ] **Stack técnico** — tabla con tecnología + por qué
- [ ] **Estructura del proyecto** — árbol con descripciones
- [ ] **Documentación** — enlaces a SPEC, ARCHITECTURE, AI_USAGE, plan
- [ ] **Variables de entorno** — tabla con cada var + descripción
- [ ] **Roles del sistema** — tabla con permisos
- [ ] **Estado del proyecto** — checklist de funcionalidades y bonuses
- [ ] **Licencia y crédito**

**Tip de generación:** este README + Mermaid lo puede generar ChatGPT/Claude perfectamente si le pasás `SPEC.md` + el template de `plan.md § Slice 7`. **Te ahorrás 30-40 min de tipeo.**

### CI completo
- [ ] Workflow corre en push y PR
- [ ] Backend: ruff + pytest --cov --cov-fail-under=50
- [ ] Frontend: eslint + vitest
- [ ] Smoke test de Docker build
- [ ] Badge en README

### Verificación final
- [ ] Clonar el repo en una carpeta nueva
- [ ] Copiar `.env.example` a `.env` en backend y frontend
- [ ] `docker compose up --build` en < 5 min
- [ ] Manual: registro → login → crear evento → sesión → publicar → otro usuario se inscribe
- [ ] Todos los URLs y comandos del README funcionan

### ✅ Checkpoint CP7 (ENTREGA LISTA)
- [ ] CI verde en `main`
- [ ] 3 docs completos (SPEC, ARCHITECTURE, AI_USAGE)
- [ ] README pasa el smoke test
- [ ] No hay TODOs, secretos, `any` injustificados
- [ ] Historia de commits sigue Conventional Commits
- [ ] Commit final: `docs: ARCHITECTURE + AI_USAGE + README final`

---

## 🎁 SLICE 8 — BONUS (opcional) · Vie 29-may (buffer) · Task #37

### Bonus IA — Generador de descripciones
- [ ] `backend/src/mis_eventos/llm/provider.py` con `get_llm()` (Groq Llama 3.3)
- [ ] `services/description_generator.py`
- [ ] `POST /ai/generate-description` con manejo de error 503
- [ ] Mock de LLM en tests para no llamar al servicio real en CI
- [ ] Botón "Generar con IA" en EventForm
- [ ] Documentar en ARCHITECTURE.md y AI_USAGE.md

### Bonus Deploy
- [ ] Elegir Fly.io o Railway
- [ ] Configurar `fly.toml` / `railway.json`
- [ ] Postgres managed
- [ ] Variables de entorno en el panel
- [ ] URL pública en el README
- [ ] Smoke test del sistema deployado

### ✅ Checkpoint CP8 (si se hizo)
- [ ] Bonus IA funciona desde la UI
- [ ] Deploy accesible desde URL pública
- [ ] Commit: `feat(bonus): IA generadora + deploy en nube`

---

## 📨 ENTREGA FINAL

- [ ] Push a `main` con CI verde
- [ ] Verificar que el repo es público (o acceso compartido a evaluadores)
- [ ] Enviar email a Talento Serviinformación con:
  - Asunto: vacante "Senior Developer / Tech Lead"
  - Link al repo
  - URL del deploy (si aplica)
  - Mención breve de los entregables clave

---

**Última actualización:** 22-may-2026 · **Versión:** 1.0
