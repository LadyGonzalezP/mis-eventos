# AI_USAGE — Uso de IA durante el desarrollo de Mis Eventos

> Documento honesto y especifico sobre como se uso IA para construir este proyecto.
> El reto evalua **criterio**, no solo uso.

---

## 1. Herramientas usadas

**Claude Code** (Anthropic, CLI de desarrollo asistido por IA) fue el unico asistente de IA usado.
No se uso Copilot, Cursor, ni ChatGPT directamente. Las llamadas a LLMs de produccion (Groq + Llama 3.3) son una funcionalidad opcional del producto, no parte del proceso de desarrollo.

---

## 2. Metodologia aplicada — Spec-driven development

**No fue vibe coding.** El flujo de trabajo siguio un proceso disciplinado:

1. **Producto primero.** Antes de tocar codigo, defini en `docs/SPEC.md` (18 secciones) el objetivo, alcance, modelo de datos, API surface, criterios de aceptacion y boundaries.

2. **Plan por slices verticales.** Cada slice (S0–S8) entrega una funcionalidad **end-to-end** (backend + frontend + tests) verificable con un checkpoint duro. Esta documentado en `tasks/plan.md`.

3. **Acceptance criteria por slice.** Cada checkpoint tiene criterios concretos (ej: "5 tests del conflict validator pasan + UI muestra error legible").

4. **Tests primero (TDD) cuando aplica.** El endpoint `/health` y el algoritmo de conflictos fueron desarrollados con tests primero. Para CRUD repetitivo se aplico TDD en bloque (escribir varios tests + endpoint + iterar).

5. **Commits atomicos.** Cada slice = 1 commit conventional. Total de la historia limpia: 8+ commits.

6. **Verificacion humana.** Cada cambio fue revisado antes de mergear: tipos correctos, sin TODOs, sin secretos, CI verde.

---

## 3. Ejemplos concretos

### 3.1 Sugerencia ACEPTADA — Patron `Annotated[Type, Depends()]`

**Contexto:** la primera version del endpoint `/health` usaba el patron viejo `def f(db: Session = Depends(get_db))`.

**Sugerencia de Claude:** migrar al patron moderno con `Annotated`:
```python
DbDep = Annotated[Session, Depends(get_db)]

@router.get("/health")
def health_check(db: DbDep) -> dict[str, Any]:
    ...
```

**Por que la acepte:**
1. Ruff B008 (no llamar funciones en defaults) lo enforza correctamente.
2. La FastAPI 0.115+ recomienda este patron en su documentacion oficial.
3. Hace los tipos reutilizables (`DbDep`, `CurrentUser`) en multiples endpoints.

**Resultado:** todo el backend usa este patron consistentemente.

---

### 3.2 Sugerencia RECHAZADA — `passlib[bcrypt]`

**Contexto:** al implementar el hashing de passwords, Claude sugirio usar `passlib.context.CryptContext(["bcrypt"])` — el estandar tradicional.

**Por que la rechace:**
Al correr los primeros tests obtuve `AttributeError: module 'bcrypt' has no attribute '__about__'` — `passlib` no esta actualizado para `bcrypt 4.x+`.

**Que hice en su lugar:** elimine `passlib` y use `bcrypt` directo:
```python
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8")[:72], bcrypt.gensalt(rounds=12)).decode("utf-8")
```

**Beneficio adicional:** menos dependencias transitivas + compatibilidad garantizada con futuras versiones de bcrypt.

---

### 3.3 Bug que la IA NO detecto y YO si — El test usaba name="A"

**Contexto:** al escribir `test_my_registrations_returns_user_events`, Claude genero codigo de la forma:
```python
event1 = _create_published_event(client, headers, payload, name="A")
event2 = _create_published_event(client, headers, payload, name="B")
```

**El bug:** El schema `EventCreate` exige `name: str = Field(min_length=2)`. Los nombres "A" y "B" tienen 1 caracter, por lo que el POST devolvia 422, y la respuesta `.json()` no tenia el campo `id`. El error era `KeyError: 'id'` — confuso.

**Lo que hice:** investigue el response real, vi el 422 oculto, y cambie los nombres a `"Evento A"` y `"Evento B"`. La IA no detecto la inconsistencia entre los datos de test y la validacion del schema.

**Leccion:** Los validators de Pydantic no aparecen como "bug" en el codigo del test — solo se ven en runtime. Hay que leer los schemas con cuidado.

---

### 3.4 Sugerencia CORREGIDA — Endpoint `/health` siempre devuelve 200

**Sugerencia inicial:** que `/health` devolviera 503 si la DB esta caida.

**Mi correccion:** que devuelva siempre 200, pero con `db: "error"` y `status: "degraded"` en el body.

**Razon:** un load balancer / orchestrator (Docker, K8s) quiere saber si el **servicio** esta vivo (puede responder HTTP) — eso es responsabilidad del liveness probe. La salud de la DB es informacion **complementaria**, no determina si el container debe ser reiniciado.

**Resultado:** el cliente puede distinguir "servicio caido" (no responde) de "servicio degradado" (responde pero con BD caida). Es una distincion semantica importante.

---

## 4. Decisiones que tome YO (no la IA)

Cosas donde mi criterio prevalecio sobre la sugerencia del asistente:

- **Alcance acotado a 5 funcionalidades obligatorias + 2 bonuses elegidos** (no intentar todos los bonuses).
- **3 roles con RBAC en MVP** (en lugar de dejarlo como bonus opcional).
- **API con prefijo `/api/v1/`** desde dia 1 (no esperar a que sea necesario).
- **Formato estandar de error `{error, detail, context}`** consistente en todos los endpoints.
- **State machine como servicio puro** (en lugar de logica esparcida en endpoints).
- **No usar `passlib`** (decision tomada despues de fallo, ver 3.2).
- **Migraciones reversibles obligatorias** (boundary en SPEC).
- **Tests con SQLite in-memory** (en lugar de testcontainers - mas rapido para CI).

---

## 5. Lo que la IA aporto vs lo que aporte yo

| Lo que aporto la IA | Lo que aporte yo |
|---|---|
| Velocidad para escribir codigo boilerplate | Definicion del producto y modelo de datos |
| Sugerencias de patrones modernos (Annotated, StrEnum) | Eleccion del stack con trade-offs |
| Cobertura de casos edge en tests | Decision de que casos son criticos |
| Generacion de migraciones Alembic | Decisiones de arquitectura |
| Documentacion en formato consistente | Honestidad sobre limites y mejoras futuras |

**La IA acelero la implementacion. Las decisiones fueron mias.**

---

## 6. Conclusion

La IA es una herramienta poderosa **cuando se usa con criterio**. En este proyecto:

- **El proceso fue spec-driven**, no caos de prompts.
- **Cada decision tecnica esta documentada** y defendible (ver `ARCHITECTURE.md`).
- **Los errores que la IA no detecto los encontre yo** corriendo tests y leyendo logs.
- **Los limites del producto estan declarados explicitamente** (no son deuda oculta).

Si maniana hay que mantener este proyecto sin IA, **se puede**: el codigo esta organizado, testeado, y documentado para humanos.

---

**Version:** 1.0 final · **Fecha:** 2026-05-23 · **Autora:** Lady Katherine Gonzalez
