"""Pytest configuration and fixtures."""
import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture() -> Generator[TestClient, None, None]:
    """Create a test client."""
    from app.main import app

    with TestClient(app) as client:
        yield client
