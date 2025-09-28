import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import os

from src.main import create_app
from src.infrastructure.database.models import Base
from src.infrastructure.database.connection import DatabaseManager
from src.interfaces.api.v1.dependencies import get_database_session
from src.config.settings import Settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Override settings for testing
@pytest.fixture
def test_settings():
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        REDIS_URL="redis://localhost:6379/1",  # Different DB for tests
        SECRET_KEY="test-secret-key",
        DEBUG=True,
        RATE_LIMIT_ENABLED=False,  # Disable rate limiting for tests
        LOG_LEVEL="ERROR"  # Reduce noise in tests
    )

@pytest.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        yield session

@pytest.fixture
def test_app(test_session, test_settings):
    """Create test FastAPI app"""
    app = create_app()
    
    # Override dependencies
    app.dependency_overrides[get_database_session] = lambda: test_session
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create test client"""
    return TestClient(test_app)

@pytest.fixture
def sample_tracking_id():
    """Sample tracking ID for tests"""
    return "TEST_TRACKING_001"

@pytest.fixture
def sample_unit_data():
    """Sample unit data for tests"""
    return {
        "tracking_id": "TEST_TRACKING_001",
        "guide_id": "GUIDE_001",
        "weight": 2.5,
        "dimensions": "20x15x10",
        "origin": "Warehouse A",
        "destination": "Customer B"
    }

@pytest.fixture
def sample_checkpoint_data():
    """Sample checkpoint data for tests"""
    return {
        "tracking_id": "TEST_TRACKING_001",
        "status": "CREATED",
        "location": "Warehouse A",
        "description": "Package created",
        "operator": "system",
        "meta_data": {"source": "test"}
    }