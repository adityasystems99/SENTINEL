"""Unit and integration tests for Phase 4: Compatibility Engine and Promise vs Reality Audit."""
import io
import os
import zipfile
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.compatibility import CompatibilityStatus
from backend.app.models.audit import AuditFindingStatus
from backend.app.storage.project_store import project_store

client = TestClient(app)

def create_in_memory_zip(file_map: dict) -> bytes:
    """Helper to create a ZIP archive in memory from a dict of relative paths -> contents."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, content in file_map.items():
            zf.writestr(filepath, content)
    buffer.seek(0)
    return buffer.getvalue()

@pytest.fixture(autouse=True)
def clean_project_store():
    """Ensure project store is reset between tests."""
    project_store.clear()
    yield
    project_store.clear()

def test_compatibility_assessment_comprehensive():
    """Test compatibility engine detects frameworks, entry points, routes, telemetry, and prerequisites."""
    zip_bytes = create_in_memory_zip({
        "main.py": (
            "from fastapi import FastAPI\n"
            "import logging\n"
            "app = FastAPI()\n"
            "logger = logging.getLogger('test')\n"
            "@app.get('/health')\n"
            "def health():\n"
            "    logger.info('health check')\n"
            "    return {'status': 'ok'}\n"
            "@app.post('/api/users')\n"
            "def create_user():\n"
            "    return {'id': 1}\n"
        ),
        "requirements.txt": "fastapi==0.110.0\nuvicorn==0.28.0\nopentelemetry-api==1.24.0\npytest==8.1.0\n",
        "tests/test_main.py": (
            "def test_health():\n"
            "    assert True\n"
        ),
        "Dockerfile": "FROM python:3.11\nCMD ['uvicorn', 'main:app']\n"
    })

    # Upload project
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("compat_test.zip", zip_bytes, "application/zip")},
        data={"name": "Compatibility Demo"}
    )
    assert upload_res.status_code == 201
    proj_id = upload_res.json()["project_id"]

    # Run compatibility assessment
    assess_res = client.post(f"/api/projects/{proj_id}/compatibility/assess")
    assert assess_res.status_code == 200
    report = assess_res.json()

    assert report["project_id"] == proj_id
    assert report["overall_status"] in [CompatibilityStatus.COMPATIBLE.value, CompatibilityStatus.PARTIALLY_READY.value]
    
    # Check detected technologies
    tech_names = [t["name"] for t in report["detected_technologies"]]
    assert "Python" in tech_names
    assert "FastAPI" in tech_names

    # Check entry point & routes
    assert "main.py" in report["entry_points"]
    assert any("/health" in r for r in report["detected_routes"])
    assert any("/api/users" in r for r in report["detected_routes"])

    # Check telemetry readiness
    telemetry = report["telemetry_readiness"]
    assert telemetry["has_structured_logging"] is True
    assert telemetry["has_health_endpoint"] is True
    assert telemetry["has_opentelemetry"] is True
    assert telemetry["status"] == "ready"

    # Check retrieval endpoint
    get_res = client.get(f"/api/projects/{proj_id}/compatibility")
    assert get_res.status_code == 200
    assert get_res.json()["project_id"] == proj_id

def test_compatibility_invalid_project_or_missing_source():
    """Test compatibility endpoints return 404 for unknown projects."""
    res = client.post("/api/projects/prj-nonexistent/compatibility/assess")
    assert res.status_code == 404

    get_res = client.get("/api/projects/prj-nonexistent/compatibility")
    assert get_res.status_code == 404

def test_audit_engine_four_classifications():
    """Verify Feature 2 classifies implemented, partially implemented, missing, and unverifiable requirements."""
    # Create fixture project with all 4 requirement types:
    # 1. Implemented: User Authentication and Password Hashing (concrete logic + test)
    # 2. Partially Implemented: Stripe Payment Processing (stub with pass / NotImplementedError)
    # 3. Missing: Biometric Voice Recognition (no code exists)
    # 4. Unverifiable: 99.99% Cloud Infrastructure High Availability SLA (infrastructure/cloud trait)
    zip_bytes = create_in_memory_zip({
        "auth.py": (
            "import hashlib\n\n"
            "def hash_user_password(password: str) -> str:\n"
            "    '''Secure user authentication and password hashing.'''\n"
            "    salt = 'sentinel_salt'\n"
            "    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()\n"
        ),
        "payment.py": (
            "def process_stripe_payment(amount: float, currency: str):\n"
            "    '''Stripe payment processing gateway.'''\n"
            "    # TODO: implement real stripe gateway charge\n"
            "    raise NotImplementedError('Stripe checkout integration not finished')\n"
        ),
        "tests/test_auth.py": (
            "from auth import hash_user_password\n\n"
            "def test_auth_hash():\n"
            "    hashed = hash_user_password('supersecret')\n"
            "    assert hashed is not None\n"
        )
    })

    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("audit_fixture.zip", zip_bytes, "application/zip")},
        data={"name": "Audit Fixture Project"}
    )
    assert upload_res.status_code == 201
    proj_id = upload_res.json()["project_id"]

    spec_doc = (
        "# Project Requirements\n\n"
        "## Feature 1: User Authentication and Password Hashing\n"
        "Must securely hash user credentials using cryptographic sha256 algorithms.\n\n"
        "## Feature 2: Stripe Payment Processing\n"
        "Must process payments and credit card checkout charges via Stripe API.\n\n"
        "## Feature 3: SMS Two-Factor Phone Verification\n"
        "Must send one-time passcodes over cellular telecom SMS gateways.\n\n"
        "## Feature 4: 99.99% Cloud Infrastructure High Availability SLA\n"
        "System must maintain high availability cloud deployment uptime of 99.99% SLA.\n"
    )

    # Run audit via JSON POST
    audit_res = client.post(
        f"/api/projects/{proj_id}/audit",
        json={
            "requirements_text": spec_doc,
            "acceptance_criteria": "All endpoints must return structured JSON."
        }
    )
    assert audit_res.status_code == 200
    report = audit_res.json()

    assert report["project_id"] == proj_id
    assert report["total_requirements"] >= 4

    findings = {f["title"]: f for f in report["findings"]}
    
    # 1. Check Implemented
    impl_key = next((k for k in findings if "Authentication" in k), None)
    assert impl_key is not None
    impl_finding = findings[impl_key]
    assert impl_finding["status"] == AuditFindingStatus.IMPLEMENTED.value
    assert len(impl_finding["supporting_files"]) > 0
    assert "auth.py" in impl_finding["supporting_files"][0]["file_path"]

    # 2. Check Partially Implemented
    part_key = next((k for k in findings if "Stripe" in k), None)
    assert part_key is not None
    part_finding = findings[part_key]
    assert part_finding["status"] == AuditFindingStatus.PARTIALLY_IMPLEMENTED.value
    assert len(part_finding["supporting_files"]) > 0
    assert "payment.py" in part_finding["supporting_files"][0]["file_path"]

    # 3. Check Missing
    miss_key = next((k for k in findings if "SMS" in k or "Phone" in k), None)
    assert miss_key is not None
    miss_finding = findings[miss_key]
    assert miss_finding["status"] == AuditFindingStatus.MISSING.value

    assert len(miss_finding["supporting_files"]) == 0

    # 4. Check Unverified
    unver_key = next((k for k in findings if "99.99%" in k or "SLA" in k), None)
    assert unver_key is not None
    unver_finding = findings[unver_key]
    assert unver_finding["status"] == AuditFindingStatus.UNVERIFIED.value

    # Prioritized roadmap checks
    roadmap = report["prioritized_roadmap"]
    assert len(roadmap) >= 3  # Implemented item shouldn't need urgent action
    roadmap_priorities = [item["priority"] for item in roadmap]
    # Check that CRITICAL or HIGH priorities come first
    if "CRITICAL" in roadmap_priorities and "LOW" in roadmap_priorities:
        assert roadmap_priorities.index("CRITICAL") < roadmap_priorities.index("LOW")

    # Get cached audit report
    get_res = client.get(f"/api/projects/{proj_id}/audit")
    assert get_res.status_code == 200
    assert get_res.json()["compliance_score"] == report["compliance_score"]

def test_audit_file_upload_and_format_validation():
    """Test submitting requirements via file upload, verifying format validation."""
    zip_bytes = create_in_memory_zip({
        "app.py": "def test_app(): return True\n",
    })
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("file_spec_test.zip", zip_bytes, "application/zip")},
    )
    proj_id = upload_res.json()["project_id"]

    # 1. Valid markdown spec file upload
    md_content = b"# Requirements\n- Must provide secure health status checks\n"
    res = client.post(
        f"/api/projects/{proj_id}/audit/file",
        files={"file": ("spec.md", md_content, "text/markdown")},
        data={"acceptance_criteria": "Return 200 OK"}
    )
    assert res.status_code == 200
    assert res.json()["total_requirements"] >= 1

    # 2. Unsupported file type rejected (.pdf)
    res_bad = client.post(
        f"/api/projects/{proj_id}/audit/file",
        files={"file": ("spec.pdf", b"%PDF-1.4 dummy binary content", "application/pdf")},
    )
    assert res_bad.status_code == 400
    assert "Unsupported document format" in res_bad.json()["detail"]

def test_audit_malformed_input_rejections():
    """Test submitting malformed or empty requirements rejects gracefully."""
    zip_bytes = create_in_memory_zip({"empty.py": "# empty\n"})
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("empty_proj.zip", zip_bytes, "application/zip")},
    )
    proj_id = upload_res.json()["project_id"]

    # Missing both requirements_text and auto_detect_spec
    res = client.post(
        f"/api/projects/{proj_id}/audit",
        json={"requirements_text": ""}
    )
    assert res.status_code == 400
    assert "Requirements document is required" in res.json()["detail"]

def test_audit_unknown_project_404():
    """Verify 404 for unknown project IDs in audit endpoints."""
    res = client.post(
        "/api/projects/prj-fake123/audit",
        json={"requirements_text": "# Req\n- Does something"}
    )
    assert res.status_code == 404

    get_res = client.get("/api/projects/prj-fake123/audit")
    assert get_res.status_code == 404
