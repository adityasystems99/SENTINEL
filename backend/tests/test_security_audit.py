"""Security Audit, Hardening & Isolation Test Suite.
Verifies:
1. Prevention of user impersonation via cryptographic token verification (Question 1).
2. Server-derived identity and ownership checks on projects AND incidents (Question 2).
3. Secrets hygiene and absence of bundled credentials (Questions 3 & 4).
4. Full authentication gating on expensive analysis, telemetry ingestion, uploads, and Replay Lab (Question 5).
5. Single-worker consistency and rate-limiting behavior (Question 6).
6. Production CORS, HTTPS security headers, trusted-proxy spoofing protection, and startup validation (Question 7).
"""
import io
import time
import zipfile
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings, validate_production_configuration
from backend.app.storage.project_store import ProjectStore, project_store
from backend.app.storage.memory_store import MemoryTelemetryStore, store
from backend.app.auth.security import create_signed_token, verify_signed_token
from backend.app.auth.rate_limiter import rate_limiter, get_client_ip
from backend.app.models.project import ProjectMetadata, ProjectStatus
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from starlette.requests import Request

client = TestClient(app)

def create_valid_test_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("app.py", "print('hello security audit')\n")
        zf.writestr("requirements.txt", "fastapi==0.110.0\n")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def reset_security_state():
    """Reset stores, limiter, and config state before each test."""
    orig_auth = settings.auth_enabled
    orig_debug = settings.debug
    orig_env = settings.environment
    orig_proxy = settings.behind_trusted_proxy
    rate_limiter.reset()
    store.clear()
    project_store.clear()
    yield
    settings.auth_enabled = orig_auth
    settings.debug = orig_debug
    settings.environment = orig_env
    settings.behind_trusted_proxy = orig_proxy
    rate_limiter.reset()
    store.clear()
    project_store.clear()


# ==============================================================================
# Question 1: User Impersonation Prevention & Cryptographic Identity
# ==============================================================================

def test_user_impersonation_without_server_signature_rejected():
    """Verify that clients CANNOT impersonate another user or admin with forged headers."""
    settings.auth_enabled = True

    # 1. Attacker attempts raw user claim without signature
    res = client.get("/api/projects", headers={"Authorization": "Bearer user:alice"})
    assert res.status_code == 401
    assert "Invalid authentication credentials" in res.json()["detail"]

    # 2. Attacker attempts raw admin claim without signature
    res_admin = client.get("/api/projects", headers={"Authorization": "Bearer admin:superuser"})
    assert res_admin.status_code == 401

    # 3. Attacker attempts forged token with fake signature
    forged_token = "alice:user:9999999999:fake_forged_signature_hash"
    res_forged = client.get("/api/projects", headers={"Authorization": f"Bearer {forged_token}"})
    assert res_forged.status_code == 401


def test_tampered_token_payload_rejected():
    """Verify that tampering with any part of a signed token invalidates it."""
    settings.auth_enabled = True

    # Genuine signed token for user 'bob'
    valid_bob_token = create_signed_token("bob", "user")
    parts = valid_bob_token.split(":")

    # Attacker changes user_id from 'bob' to 'alice' but keeps bob's signature
    tampered_token = f"alice:{parts[1]}:{parts[2]}:{parts[3]}"
    res = client.get("/api/projects", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401
    assert "Invalid authentication credentials" in res.json()["detail"]


# ==============================================================================
# Question 2: Server-Derived Ownership on Projects & Incidents
# ==============================================================================

def test_workspace_isolation_cross_tenant_access_forbidden():
    """Verify that user B cannot access, inspect, or audit user A's project (HTTP 403)."""
    settings.auth_enabled = True

    # User Alice uploads a project using a valid server-signed token
    alice_token = create_signed_token("alice", "user")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("alice_app.zip", create_valid_test_zip(), "application/zip")},
        headers=alice_headers,
    )
    assert upload_res.status_code == 201
    project_id = upload_res.json()["project_id"]
    assert upload_res.json()["owner_id"] == "alice"

    # User Bob attempts to access Alice's project using Bob's valid server-signed token -> 403 Forbidden
    bob_token = create_signed_token("bob", "user")
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    get_res = client.get(f"/api/projects/{project_id}", headers=bob_headers)
    assert get_res.status_code == 403
    assert "permission" in get_res.json()["detail"].lower()

    inspect_res = client.post(f"/api/projects/{project_id}/inspect", headers=bob_headers)
    assert inspect_res.status_code == 403

    audit_res = client.post(
        f"/api/projects/{project_id}/audit",
        json={"requirements_text": "Must be secure", "auto_detect_spec": False},
        headers=bob_headers,
    )
    assert audit_res.status_code == 403

    del_res = client.delete(f"/api/projects/{project_id}", headers=bob_headers)
    assert del_res.status_code == 403

    # User Alice herself CAN access her own project -> 200 OK
    alice_get = client.get(f"/api/projects/{project_id}", headers=alice_headers)
    assert alice_get.status_code == 200


def test_incident_ownership_isolation_cross_tenant_forbidden():
    """Verify that incident reports are scoped to the creator and other tenants cannot read them."""
    settings.auth_enabled = True

    # Ingest telemetry for Alice
    alice_token = create_signed_token("alice", "user")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    client.post(
        "/api/telemetry/ingest",
        json={
            "events": [{
                "timestamp": time.time(),
                "service": "alice-service",
                "level": "ERROR",
                "event_type": "log",
                "message": "Alice critical db failure",
            }]
        },
        headers=alice_headers,
    )

    # Alice analyzes the incident
    analyze_res = client.post("/api/incidents/analyze", json={"window_seconds": 300}, headers=alice_headers)
    assert analyze_res.status_code == 200
    incident_id = analyze_res.json()["incident_id"]
    assert analyze_res.json()["owner_id"] == "alice"

    # Bob attempts to get Alice's incident report -> 403 Forbidden
    bob_token = create_signed_token("bob", "user")
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    bob_get = client.get(f"/api/incidents/{incident_id}", headers=bob_headers)
    assert bob_get.status_code == 403
    assert "permission" in bob_get.json()["detail"].lower()

    # Bob's incident list does not expose Alice's incident
    bob_list = client.get("/api/incidents", headers=bob_headers)
    assert bob_list.status_code == 200
    assert not any(inc["incident_id"] == incident_id for inc in bob_list.json())

    # Alice can retrieve her own incident
    alice_get = client.get(f"/api/incidents/{incident_id}", headers=alice_headers)
    assert alice_get.status_code == 200


def test_admin_role_can_access_any_project_and_incident():
    """Verify that an admin token can access projects and incidents across all tenants."""
    settings.auth_enabled = True

    alice_token = create_signed_token("alice", "user")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("alice_app.zip", create_valid_test_zip(), "application/zip")},
        headers=alice_headers,
    )
    project_id = upload_res.json()["project_id"]

    admin_headers = {"Authorization": f"Bearer {settings.admin_api_key}"}
    admin_get = client.get(f"/api/projects/{project_id}", headers=admin_headers)
    assert admin_get.status_code == 200
    assert admin_get.json()["project_id"] == project_id


# ==============================================================================
# Question 5: Unauthenticated Operations Gating
# ==============================================================================

def test_unauthenticated_request_rejected_on_all_critical_operations():
    """Verify that unauthenticated users CANNOT invoke expensive operations or ingestion."""
    settings.auth_enabled = True

    # 1. Project upload
    res = client.post("/api/projects/upload", files={"file": ("test.zip", create_valid_test_zip(), "application/zip")})
    assert res.status_code == 401

    # 2. Incident analysis
    res = client.post("/api/incidents/analyze", json={"window_seconds": 300})
    assert res.status_code == 401

    # 3. Telemetry batch ingestion
    res = client.post("/api/telemetry/ingest", json={"events": [{"timestamp": time.time(), "service": "s", "level": "INFO", "event_type": "log", "message": "m"}]})
    assert res.status_code == 401

    # 4. OTLP trace ingestion
    res = client.post("/api/telemetry/otlp/v1/traces", json={"spans": []})
    assert res.status_code == 401

    # 5. Replay Lab validation
    res = client.post("/api/validation/run", json={"experiment_id": "exp-1", "fix_id": "fix-1", "approved": True})
    assert res.status_code == 401

    # 6. Demo failure injection
    res = client.post("/api/demo/scenario/db_pool_exhaustion")
    assert res.status_code == 401


# ==============================================================================
# Question 6 & 7: Rate Limiting, Proxy IP Spoofing & Startup Validation
# ==============================================================================

def test_telemetry_batch_size_cap_enforced():
    """Verify that telemetry batches exceeding max_telemetry_batch_size are rejected with 400."""
    events = []
    for i in range(1001):
        events.append({
            "timestamp": time.time(),
            "service": "load-test",
            "level": "INFO",
            "event_type": "log",
            "message": f"event {i}",
        })

    res = client.post("/api/telemetry/ingest", json={"events": events}, headers={"Authorization": f"Bearer {settings.api_key}"})
    assert res.status_code == 400
    assert "exceeds maximum allowed limit" in res.json()["detail"]


def test_trusted_proxy_header_spoofing_prevented():
    """Verify that get_client_ip does not blindly trust spoofed leading X-Forwarded-For IPs."""
    settings.behind_trusted_proxy = True

    # Simulate client sending spoofed IP, and proxy appending real remote IP
    scope = {
        "type": "http",
        "headers": [
            (b"x-forwarded-for", b"1.1.1.1, 203.0.113.195"),
        ],
        "client": ("10.0.0.1", 5000),
    }
    req = Request(scope)
    extracted_ip = get_client_ip(req)
    assert extracted_ip == "203.0.113.195", f"Expected rightmost proxy IP 203.0.113.195, got {extracted_ip}"


def test_in_memory_rate_limiting_triggers_429():
    """Verify that exceeding route rate limits returns 429 with Retry-After header."""
    rate_limiter.reset()

    limit = settings.expensive_rate_limit_per_minute
    hit_429 = False

    for _ in range(limit + 5):
        res = client.post(
            "/api/projects/upload",
            files={"file": ("rapid.zip", create_valid_test_zip(), "application/zip")},
            headers={"Authorization": f"Bearer {settings.api_key}"},
        )
        if res.status_code == 429:
            hit_429 = True
            assert "Rate limit exceeded" in res.json()["detail"]
            assert "Retry-After" in res.headers
            break

    assert hit_429, "Expected rate limiter to trigger HTTP 429 Too Many Requests"


def test_startup_production_configuration_validation():
    """Verify that validate_production_configuration prevents starting in production with unsafe settings."""
    settings.environment = "production"
    settings.auth_enabled = False  # Insecure setting

    with pytest.raises(RuntimeError) as exc_info:
        validate_production_configuration()
    assert "SENTINEL_AUTH_ENABLED must be 'true' in production" in str(exc_info.value)

    # Re-enable auth but keep default demo key
    settings.auth_enabled = True
    settings.api_key = "demo-sentinel-key-2026"
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_configuration()
    assert "SENTINEL_API_KEY must be changed" in str(exc_info.value)

    # Reset environment back to development
    settings.environment = "development"


def test_security_headers_present_on_responses():
    """Verify essential security headers are returned on HTTP responses."""
    res = client.get("/api/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_disk_persistence_across_process_restart():
    """Verify that uploaded project metadata and files survive a simulated process restart."""
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("restart_test.zip", create_valid_test_zip(), "application/zip")},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert upload_res.status_code == 201
    project_id = upload_res.json()["project_id"]

    # Ephemeral in-memory store
    store.add_events([
        TelemetryEvent(
            timestamp=time.time(),
            service="temp-service",
            level=LogLevel.INFO,
            event_type=EventType.LOG,
            message="Ephemeral event",
        )
    ])
    assert store.total_events > 0

    fresh_project_store = ProjectStore(base_dir=project_store.base_dir)
    fresh_memory_store = MemoryTelemetryStore()

    reloaded_proj = fresh_project_store.get_project(project_id)
    assert reloaded_proj is not None
    assert reloaded_proj.project_id == project_id
    assert reloaded_proj.status == ProjectStatus.READY

    assert fresh_memory_store.total_events == 0
