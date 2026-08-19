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