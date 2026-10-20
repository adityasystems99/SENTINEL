"""Focused tests for Vercel entrypoint and demo_app module resolution."""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path (matching Vercel's execution context where backend is root)
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)


def test_demo_app_importability():
    """Verify DemoAppService and scenarios can be imported without ModuleNotFoundError."""
    try:
        from demo_app.service import DemoAppService
        from demo_app.scenarios import recover_all, inject_bad_auth_deployment
    except ImportError:
        try:
            from app.demo_app.service import DemoAppService
            from app.demo_app.scenarios import recover_all, inject_bad_auth_deployment
        except ImportError:
            from backend.demo_app.service import DemoAppService
            from backend.demo_app.scenarios import recover_all, inject_bad_auth_deployment

    svc = DemoAppService()
    assert svc is not None
    inject_bad_auth_deployment(svc, count=1)
    assert svc.bad_auth_deployment is True
    recover_all(svc)
    assert svc.bad_auth_deployment is False
    assert svc.db_pool_exhausted is False
    assert svc.payment_gateway_down is False


def test_vercel_entrypoint_app():
    """Verify that api.index exports a valid FastAPI application."""
    try:
        from api.index import app
    except ImportError:
        from backend.api.index import app
    assert app is not None
    assert "SENTINEL" in app.title


def test_vercel_routes_root_and_health():
    """Verify core Vercel endpoints /, /docs, /openapi.json, and /api/health."""
    try:
        from api.index import app
    except ImportError:
        from backend.api.index import app
    client = TestClient(app)

    # Root /
    root_resp = client.get("/")
    assert root_resp.status_code == 200, f"Root / failed with {root_resp.status_code}: {root_resp.text}"
    assert "platform" in root_resp.json()
    assert root_resp.json().get("status") == "operational"

    # Health
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"/api/health failed: {health_resp.text}"
    assert health_resp.json().get("status") == "healthy"

    # Docs & OpenAPI
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert "paths" in schema
    assert "/api/health" in schema["paths"]
    assert "/api/demo/scenario/{scenario_name}" in schema["paths"]


def test_vercel_demo_scenario_endpoints():
    """Verify that demo endpoints run and do not crash on demo_app dependencies."""
    try:
        from api.index import app
    except ImportError:
        from backend.api.index import app
    client = TestClient(app)

    # Recover scenario
    rec_resp = client.post("/api/demo/scenario/recover")
    assert rec_resp.status_code == 200, f"Recover scenario failed: {rec_resp.text}"
    assert rec_resp.json().get("status") == "recovered"

    # Bad-auth scenario
    auth_resp = client.post("/api/demo/scenario/bad_auth_deployment?count=1")
    assert auth_resp.status_code == 200, f"Bad-auth scenario failed: {auth_resp.text}"
    assert auth_resp.json().get("scenario") == "bad_auth_deployment"
    assert auth_resp.json().get("status") == "injected"

    # Clean up with recover
    rec_resp2 = client.post("/api/demo/scenario/recover")
    assert rec_resp2.status_code == 200
