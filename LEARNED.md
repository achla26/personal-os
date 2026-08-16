## 2026-08-15 - [M1] FastAPI skeleton + /health

Learn : By Using FastAPI type hint OpenAPI schema built itself. same idea will use in tool schemas later.

## 2026-08-16 — [M1] Postgres + async SQLAlchemy session

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

## 2026-08-16 — [M1] users + items schema + pehli migration
Learnt : partial index only matching rows index  — scheduler speed get fast and free from 
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

  