import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.infra.models import Base
from app.infra.db import get_db
from app.infra.models.user import User

@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container once for all tests."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture
async def db_session(postgres_container):
    # Convert sync URL to async URL
    sync_url = postgres_container.get_connection_url()
    
    # Async URL convert 
    async_url = sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
    
    # Async engine 
    engine = create_async_engine(async_url)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    #  Session make and yield 
    SessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with SessionLocal() as session:
        yield session
    
    # Cleanup: drop tables
    async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def client(db_session):
    # Override function that yield test db_session 
    async def override_get_db():
        yield db_session
    
    # 2. FastAPI app dependency override 
    app.dependency_overrides[get_db] = override_get_db
    
    # 3. HTTP client 
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # 4. Cleanup - overrides clear 
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(client):
    # 1. Signup
    signup_response = await client.post(
        "/auth/sign-up",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        }
    )

    # 2. Login
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        }
    )    
    # 3. Token
    access_token = login_response.json()["access_token"]
    
    # 4. Client headers set 
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    yield client

@pytest.fixture
async def test_user(db_session):
    """Reusable test user fixture for all tests."""
    user = User(
        name="Test User",
        email=f"test-user-{id(db_session)}@example.com",
        password_hash="not-used-in-tests",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user    