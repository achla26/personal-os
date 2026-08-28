## 2026-08-15 - [M1] FastAPI skeleton + /health

Learn : By Using FastAPI type hint OpenAPI schema built itself. same idea will use in tool schemas later.

### Postgres + async SQLAlchemy session

**Issues:**

- While writing `docker-compose.yml`, I wrote this:

  ```yml
  postgres_data : /var/lib/postgresql/data
  ```

  instead of this:

  ```yml
  - postgres_data:/var/lib/postgresql/data
  ```

  Because of that, I got this error:

  ```txt
  service "db" refers to undefined volume postgres_data: invalid compose project
  ```

  or

  ```txt
  services.db.volumes.[0] is missing a mount target
  ```

- In Postgres 18+, this old mount path can cause problems:

  ```yml
  - postgres_data:/var/lib/postgresql/data
  ```

  I saw this message:

  ```txt
  /var/lib/postgresql/data (unused mount/volume)
  suggested container configuration for 18+ is to place a single mount at /var/lib/postgresql
  ```

- So for **Postgres 18+**, the volume path should be changed to:

  ```yml
  - postgres_data:/var/lib/postgresql
  ```

---

**Learn:**

- In Docker Compose, volume syntax must be written correctly:

  ```yml
  - volume_name:container_path
  ```

  Example:

  ```yml
  - postgres_data:/var/lib/postgresql
  ```

- In **Postgres 18+**, use:

  ```yml
  /var/lib/postgresql
  ```

  not:

  ```yml
  /var/lib/postgresql/data
  ```

- If an old wrong volume is already created, I may need a fresh restart:

  ```bash
  docker compose down -v
  docker compose up -d
  ```

- `expire_on_commit=False` is important in async SQLAlchemy.

  Simple meaning:

  - after `commit()`, SQLAlchemy should **not forget** the object data
  - if it forgets the data, then touching attributes later may try to load them again from the database
  - in async code, that can cause lazy-load errors or crashes

- So this is the safer setup for async apps:

  ```python
  SessionLocal = async_sessionmaker(
      bind=engine,
      expire_on_commit=False,
      class_=AsyncSession,
  )
  ```

- `class_=AsyncSession` means:
  - make async database sessions
  - so I can use `await db.execute(...)`, `await db.commit()`, etc.

- `AsyncGenerator[AsyncSession, None]` means:
  - this function will **yield** an `AsyncSession`
  - FastAPI will use it in dependencies like `get_db()`

- `yield` in `get_db()` means:
  - give the session to the route
  - wait while the route uses it
  - then come back and close/clean it properly

  Example:

  ```python
  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      async with SessionLocal() as session:
          yield session
  ```

- Health check route can test the database like this:

  ```python
  @app.get("/health")
  async def health(db: AsyncSession = Depends(get_db)):
      await db.execute(text("SELECT 1"))
      return {"status": "ok", "db": "ok"}
  ```

  This means:
  - app is running
  - database is reachable

### users + items schema + pehli migration
Learned : partial index only matching rows index  — scheduler speed get fast and free from 
table size

---

**`Base.metadata` meaning:**
- `Base.metadata` is SQLAlchemy’s **table register**
- It stores info about all models/tables
- Alembic uses it to compare:
  - models
  - actual database

---

- `Base` is created by us
- `.metadata` is given by SQLAlchemy automatically

---

**Important problem:**
- Importing only `Base` is sometimes **not enough**
- Model classes like `User`, `Item` must also be imported somewhere
- Otherwise `Base.metadata` may stay incomplete/empty



## 2026-08-18 — [M1] items CRUD, 4 endpoints
**built:** the basic backend flow of a multi-user FastAPI app: **models → Alembic migrations → DB session → repository queries → routes → Pydantic request/response schemas**.  
also learned the safety rule that **every item query must include `user_id`**, so each user only sees their own data.

### FastAPI `response_model`

- `response_model` tells FastAPI what shape the response should have.
- It filters extra fields before sending data to the client.
- It helps prevent accidental leaks of internal/sensitive fields.
- It also validates returned data against the schema.
- It improves `/docs` by showing response structure automatically.

---

### Pydantic `from_attributes=True`

- `model_config = ConfigDict(from_attributes=True)` lets Pydantic read SQLAlchemy objects using attributes like `item.title`.
- Without it, Pydantic expects mostly dict-like input.
- This is Pydantic v2’s replacement for old `orm_mode = True`.

---

### `model_dump(exclude_unset=True)`

- `model_dump()` converts a Pydantic model into a Python dict.
- `exclude_unset=True` keeps only fields the client actually sent.
- This is useful in PATCH/update so missing fields do not become `None`.
- It prevents overwriting existing DB values by mistake.

---

### `setattr(item, key, value)`

- `setattr()` sets an object attribute dynamically.
- `setattr(item, "title", "new")` is like `item.title = "new"`.
- It is useful in loops when updating many fields from a dict.

---

### FastAPI dependency error: `session` treated as query param

- If a dependency function parameter is not wrapped in `Depends(...)`, FastAPI may treat it as request input.
- `session: AsyncSession = Depends(get_db)` tells FastAPI to inject DB session.
- Without that, FastAPI may ask for `session` in query params and raise validation error.

---
   


## 2026-08-19 — [M1] Login flow with hashed passwords

- On login, do not hash the incoming password and query by that hash.
- First fetch user by email only.
- Then verify plain password using `verify_password(payload.password, user.password_hash)`.
- Route `response_model` and actual returned data must match.
- If `response_model=AuthResponse`, do not return `None`, `str`, or raw `User`.
- On invalid login, raise `HTTPException(401)` instead of returning error strings.

## 2026-08-19 — [M1] JWT token decoding in user retrieval and update user registration response model
only need to change get_current_user no need to touch other items endpoints 

## 2026-08-19 — [M1] Refresh token added

- Access token is short-lived, so refresh token is used to get a new access token without logging in again.
- Refresh token is stored in an `httpOnly` cookie so JavaScript cannot read it.
- Refresh token should be long-lived, e.g. 30 days.
- Refresh token is stored in DB so it can be checked, revoked, and rotated.
- DB should store only the hashed refresh secret, not the plain token.
- A practical refresh token format is `token_id.secret`.
- `token_id` is used to find the DB row quickly.
- `secret` is verified against the stored hash using `verify_password(...)`.
- `/auth/refresh` reads the cookie, validates it, and returns a new access token.
- If cookie is missing, revoked, expired, or invalid, return `401`.
- Access token is usually returned in response body, not set as future auth automatically.
- Login flow: create access token + create refresh token row + set refresh cookie.
- Refresh token is often opaque (random string), not JWT, because DB control is easier.
- Opaque token means the token itself has no readable meaning; server/DB knows the meaning.
- Refresh token works more like a session key than a self-contained identity token.

#### Pending

- **Rotation:** when a refresh token is used, revoke the old one immediately and issue a new one.
- **Reuse detection:** if an already revoked refresh token is used again, revoke all refresh tokens for that user.
- **`/auth/logout`:** revoke the current refresh token and clear the refresh cookie.


## What I built in 5 sessions, from zero:

### Done ✅
- **FastAPI app** with a clean layered structure — `api → domain ← infra`
- **Postgres container** running via Docker, with **async SQLAlchemy**
- **Users + Items schema**, including a **partial index** for scheduler performance
- **Alembic migrations** for versioned database changes
- **4 CRUD endpoints**, with every query **tenant-scoped** (always filtered by `user_id`)
- **Custom JWT auth** using **Argon2** password hashing
- **Refresh tokens** stored in DB with `httpOnly` cookies
- **Refresh rotation** — when a refresh token is used, revoke the old one and issue a new one
- **Reuse detection** — if an already revoked refresh token is presented again, revoke all refresh tokens for that user (possible theft)
- **`/auth/logout`** — revoke the current refresh token and clear the cookie


## Testing Setup — Notes

**Packages:**
- `pytest` — test runner
- `pytest-asyncio` — async test support
- `httpx` — HTTP client for testing
- `testcontainers[postgres]` — auto-managed PostgreSQL container

**Config in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## Key Concepts

- **ASGITransport** — httpx can test FastAPI app without running a real server (direct memory access, fast)
- **testcontainers** — Docker container is automatically started/stopped for tests (real Postgres, no mocks)
- **Dependency override** — In FastAPI, replace production `get_db` with test DB
- **Fixtures** — pytest's reusable setup mechanism (`@pytest.fixture`)

---

## Fixtures Written (`conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `postgres_container` | session | Container starts once (all tests reuse it) |
| `db_session` | function | Fresh DB session per test |
| `client` | function | HTTP client with test DB injected |
| `auth_client` | function | Client with valid JWT token (signed in) |

**Rules:**
- `session` scope = once per test run
- `function` scope = new for each test
- `yield` after setup, cleanup after `yield`

---

## Sync URL → Async URL

`testcontainers` gives a sync URL. For async, replace it:
```python
async_url = sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
```

---

## Test Rules

- **File name** must start with `test_`
- **Function name** must start with `test_`
- Helper functions should **NOT** have `test_` prefix
- `async` helpers need `await` when called
- Return a **tuple**, not a set: `return a, b` not `{a, b}`

---

## Test Structure (AAA)

```python
async def test_something(client):
    # ARRANGE - setup data
    # ACT - make API call
    # ASSERT - verify result
    assert response.status_code == 200
```

---

## 5 Tests Written

| Test | What it checks |
|---|---|
| `test_user_cannot_access_others_item` | **Tenancy** — User B cannot see User A's item (404) |
| `test_create_item` | POST → 201, response has all fields |
| `test_auth_required` | No token → 401 |
| `test_mark_done` | PATCH `status=done` → `completed_at` filled, `next_nag_at=None` |
| `test_login_wrong_password` | Wrong password AND unknown email → same 401 (prevents email enumeration) |

---

## Security Learnings

- **404 vs 403** — return 404 for another user's item (403 leaks that the ID exists)
- **Same error message** for wrong password AND unknown email (prevents email enumeration attack)
- **Multi-tenancy** — every DB query must filter by `user_id`

---
## Debug Trick

```bash
uv run pytest -v -s
```
- `-v` = verbose output
- `-s` = show print statements

---

## 2026-08-19 — [M1] AI Entry + Structured JSON output via Groq

- Created clean `LLMProvider` Protocol boundary. No vendor lock-in; app doesn't know we use Groq.
- Built `FakeProvider` for instant unit tests with 0 cost.
- Handled Windows timezone lack issue by installing `tzdata` to resolve `zoneinfo` database.
- Implemented New Zealand (Pacific/Auckland) timezone awareness in prompts. Relative dates like "tomorrow" resolve based on user's current clock, not UTC server clock.
- Tuned Groq system prompts to strictly prevent JSON validation failure (`json_validate_failed` 400 error) caused by Qwen's thinking tags or leading whitespaces.

## 2026-08-22 — [M1] Session 8: Eval Harness & 90% Accuracy

- **Eval vs Test:** Learned that LLMs need fuzzy evals (scoring), not strict binary tests, because titles can vary.
- **YAML Pitfall:** YAML parses `off` as boolean `False` unless quoted as `"off"`.
- **Groq Rate Limits (429):** Batching 20 parallel requests to Groq free tier hits the 8000 TPM limit. Solved by executing sequentially with a 1.5s delay and writing a regex-based auto-backoff that parses the retry seconds from the 429 error message.
- **Prompt Iteration Loop:** Iterated prompt from 60% -> 80% -> 90% score. Added strict rules for "done" states (returns empty array), note prefixes overriding verbs, and priority rule for groceries over "ASAP" triggers.

## 2026-08-22 — [M1] Session 9: Orchestrating LLM with Postgres (`/chat`)

- **Layered Orchestration:** Built `domain/inbox.py` (`handle_message`) as the central orchestrator. Kept LLM calls separate from HTTP routes and DB sessions.
- **Eval Dataset Capture:** Every raw chat input is saved in the `messages` table before classification. This builds an organic eval dataset for future prompt tuning.
- **Single Atomic Transaction:** Handled `Message` insertion and multi-item `Item` insertions in a single `await session.commit()`, ensuring no orphaned items if classification or DB write partially fails.
- **Dependency Inversion in Tests:** Overrode `get_llm_provider` dependency with `FakeProvider` in FastAPI tests, executing full integration tests in milliseconds with zero API costs.
- **Swagger Auth Fix:** Switched `OAuth2PasswordBearer` to `HTTPBearer` in `deps.py` for cleaner token pasting in Swagger UI.

## 2026-08-22 — [M1] Session 10: Production LLM Infra & Integration Evals

- **Smart Retry vs Blind Retry:** Implemented exponential backoff (`1s -> 2s -> 4s`) filtering by error types (`is_retryable_error`). Never retried 401/403 auth errors.
- **Request Tracing via ContextVar:** Used Python `contextvars` (`request_id_ctx`) and FastAPI Middleware to attach a unique `X-Request-ID` to every HTTP request lifecycle without polluting function signatures.
- **Structured LLM Logging:** Formatted LLM logs as key-value pairs containing `req_id`, `latency_ms`, `tokens_in`, `tokens_out`, and estimated `cost_est` per call for future log querying.
- **Integration Evals:** Built `test_chat_eval.py` to test the entire `POST /chat` pipeline (Auth -> Context -> Domain -> LLM -> DB) achieving 90% score (18/20).

## 2026-08-28 — [M1] Frontend Auth, Next.js Setup & Secure Token Architecture

- **Token Architecture (XSS Safe):** Refresh token stored in `HttpOnly`, `SameSite`, `Secure` cookie (immune to JavaScript/XSS). Access token stored exclusively in React memory (`let accessToken: string | null`), never in `localStorage`.
- **Silent Refresh & Locking:** Built `apiFetch` seam with single-flight locking (`refreshPromise`). If multiple API calls fail simultaneously with `401`, they share a single `/auth/refresh` call rather than hammering the backend.
- **Automatic Request Retrying:** Seamlessly catches 401s, silently fetches a new access token, reattaches `Authorization: Bearer <token>`, and replays the original failed request.
- **Tailwind v4 Theming:** Configured CSS-first design tokens (`@theme`) directly in `globals.css` with semantic color palettes (`surface-0/1/2/3`, `border-subtle`, `type-*`).
- **Client Auth Context:** Implemented `AuthContext` to run silent token checks on initial page load, preventing unwanted logouts during full page refreshes.
- **Defensive Layout:** Frontend checks act strictly as side-effect UX routing; true authorization remains strictly enforced on the backend at the endpoint level (defense against Next.js middleware bypass CVE-2025-29927).

## 2026-08-23 — [M1] Chat UI, Optimistic Updates & Item Cards

- **Optimistic UI Pattern:** Rendered user message and assistant placeholder instantly before backend `/chat` completed, achieving near-zero perceived latency.
- **Dynamic Tailwind Class Safety:** Learned that dynamic template strings (`bg-${color}`) get purged by Tailwind's static analyzer. Resolved by mapping static utility class strings (`bg-orange-500/15`, `text-orange-400`) directly.
- **Single Component Architecture:** Built a single, data-driven `<ItemCard>` component driven by type maps, avoiding redundant multi-component creation for 6 item types.
- **Optimistic State Mutating:** Handled `PATCH /items/{id}` status changes dynamically with rollback fallback if network error occurs.

## 2026-08-23 — 🎉 M1 COMPLETE: Capture Loop

13 sessions. Built: auth (JWT + HttpOnly refresh), items CRUD, tenancy,
LLM classification + evals, chat endpoint, Next.js PWA, Chat/Now/Library tabs,
timezone-aware Now grouping, optimistic UI, XSS-safe token architecture.

**Mobile:** LAN bind (`0.0.0.0`), dynamic API host, CORS + allowedDevOrigins,
PWA manifest, Add to Home Screen.
 