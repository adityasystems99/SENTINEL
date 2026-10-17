"""Pytest fixtures for SENTINEL backend tests."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.storage.memory_store import store

@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    store.clear()
    with TestClient(app) as test_client:
        yield test_client
    store.clear()

@pytest.fixture(autouse=True)
def clean_store():
    """Ensure in-memory store is reset before and after every test."""
    store.clear()
    yield
    store.clear()
