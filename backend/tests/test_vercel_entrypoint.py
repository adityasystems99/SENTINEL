"""Focused tests for Vercel entrypoint, routing, and demo_app module resolution."""
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
    """Verify that api.index exports a valid FastAPI application with attributes."""
    try:
        from api.index import app
    except ImportError:
        from backend.api.index import app
    assert app is not None
    assert "SENTINEL" in app.title


def test_vercel_routes_root_and_health():
    """Verify core Vercel endpoints /, /api, /api/health, /health, /docs, and /openapi.json."""
    try:
        from api.index import app
    except ImportError:
        from backend.api.index import app
    client = TestClient(app)

    # Root / and /api
    for p in ("/", "/api", "/api/"):
        resp = client.get(p)
        assert resp.status_code == 200, f"{p} failed with {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "platform" in data
        assert data.get("status") == "operational"

    # Health checks: /api/health and /health (and slash variants)
    for hp in ("/api/health", "/api/health/", "/health", "/health/"):
        h_resp = client.get(hp)
        assert h_resp.status_code == 200, f"{hp} failed: {h_resp.text}"
        assert h_resp.json().get("status") == "healthy"
        assert h_resp.json().get("service") == "SENTINEL Backend"

    # Docs & OpenAPI
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert "paths" in schema
    assert "/api/health" in schema["paths"]
    assert "/health" in schema["paths"]
    assert "/api/demo/scenario/{scenario_name}" in schema["paths"]


def test_vercel_rewrite_simulation():
    """Simulate Vercel edge rewrite behaviors with x-matched-path header."""
    try:
        from api.index import app
    except ImportError:
        from backend.api.index import app
    client = TestClient(app)

    # Simulation 1: Vercel rewrote incoming /api/health to /api/index with x-matched-path
    r1 = client.get("/api/index", headers={"x-matched-path": "/api/health"})
    assert r1.status_code == 200
    assert r1.json().get("status") == "healthy"

    # Simulation 2: Vercel rewrote incoming /health to /api/index with x-matched-path
    r2 = client.get("/api/index", headers={"x-matched-path": "/health"})
    assert r2.status_code == 200
    assert r2.json().get("status") == "healthy"

    # Simulation 3: Vercel rewrote incoming / to /api/index with x-matched-path
    r3 = client.get("/api/index", headers={"x-matched-path": "/"})
    assert r3.status_code == 200
    assert r3.json().get("status") == "operational"

    # Simulation 4: Legacy /api/index.py destination with x-matched-path
    r4 = client.get("/api/index.py", headers={"x-matched-path": "/api/health"})
    assert r4.status_code == 200
    assert r4.json().get("status") == "healthy"

    # Simulation 5: Direct call to /api/index without header (fallback to operational root)
    r5 = client.get("/api/index")
    assert r5.status_code == 200
    assert r5.json().get("status") == "operational"


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
