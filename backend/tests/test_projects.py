"""Tests for secure project ingestion, archive validation, and API contracts."""
import io
import os
import shutil
import tempfile
import zipfile
import pytest
from backend.app.config import settings
from backend.app.storage.project_store import project_store

@pytest.fixture(autouse=True)
def isolated_project_store(tmp_path):
    """Use an isolated temporary directory for project storage during tests."""
    original_base = project_store.base_dir
    test_dir = str(tmp_path / "test_projects")
    project_store.base_dir = test_dir
    project_store.clear()
    yield test_dir
    project_store.clear()
    project_store.base_dir = original_base

def create_in_memory_zip(files_dict: dict[str, str | bytes]) -> io.BytesIO:
    """Helper to create an in-memory ZIP archive from a dict of {path: content}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, content in files_dict.items():
            if isinstance(content, str):
                z.writestr(path, content.encode("utf-8"))
            else:
                z.writestr(path, content)
    buf.seek(0)
    return buf

def test_valid_project_zip_upload(client):
    """Test successful project upload, validation, extraction, and framework detection."""
    files = {
        "src/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "requirements.txt": "fastapi==0.115.0\nuvicorn>=0.30.0",
        "README.md": "# My Sample Service",
    }
    zip_buf = create_in_memory_zip(files)

    response = client.post(
        "/api/projects/upload",
        files={"file": ("sample-service.zip", zip_buf, "application/zip")},
        data={"name": "Sample FastAPI Service"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Sample FastAPI Service"
    assert data["status"] == "ready"
    assert data["file_count"] == 3
    assert "FastAPI" in data["detected_frameworks"]
    assert "Python" in data["detected_frameworks"]
    assert data["project_id"].startswith("prj-")

    # Verify metadata retrieval
    get_res = client.get(f"/api/projects/{data['project_id']}")
    assert get_res.status_code == 200
    assert get_res.json()["project_id"] == data["project_id"]

def test_invalid_file_type_rejected(client):
    """Test that non-zip files are rejected with HTTP 400."""
    fake_txt = io.BytesIO(b"Hello world, not a zip")
    response = client.post(
        "/api/projects/upload",
        files={"file": ("project.txt", fake_txt, "text/plain")},
    )
    assert response.status_code == 400
    assert "only .zip archives are supported" in response.json()["detail"]

def test_corrupt_zip_rejected(client):
    """Test that a file with .zip extension but corrupt content is rejected."""
    corrupt_buf = io.BytesIO(b"PK\x03\x04randomcorruptedbytes123456789")
    response = client.post(
        "/api/projects/upload",
        files={"file": ("corrupt.zip", corrupt_buf, "application/zip")},
    )
    assert response.status_code == 400
    assert "Corrupt or invalid ZIP archive" in response.json()["detail"]

def test_path_traversal_zip_slip_rejected(client):
    """Test that archives attempting path traversal (Zip Slip) are blocked."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        # Create malicious path traversal entry
        z.writestr("../../evil.txt", "pwned")
    buf.seek(0)

    response = client.post(
        "/api/projects/upload",
        files={"file": ("malicious.zip", buf, "application/zip")},
    )
    assert response.status_code == 400
    assert "Path traversal detected" in response.json()["detail"]

def test_prohibited_executable_binary_rejected(client):
    """Test that archives containing suspicious executable binaries are rejected."""
    files = {
        "script.py": "print('ok')",
        "malware.exe": b"MZ\x90\x00executablebinarydata",
    }
    zip_buf = create_in_memory_zip(files)

    response = client.post(
        "/api/projects/upload",
        files={"file": ("unsafe.zip", zip_buf, "application/zip")},
    )
    assert response.status_code == 400
    assert "Prohibited executable binary entry" in response.json()["detail"]

def test_oversized_upload_limit(client, monkeypatch):
    """Test that uploads exceeding the upload size limit are rejected."""
    # Temporarily set upload limit to 500 bytes for test
    monkeypatch.setattr(settings, "max_upload_size_bytes", 500)

    # Use random uncompressible bytes so compressed ZIP exceeds 500 bytes
    files = {"random.dat": os.urandom(1024)}
    zip_buf = create_in_memory_zip(files)

    response = client.post(
        "/api/projects/upload",
        files={"file": ("big.zip", zip_buf, "application/zip")},
    )
    assert response.status_code == 400
    assert "exceeds maximum upload size limit" in response.json()["detail"]

def test_oversized_extracted_limit(client, monkeypatch):
    """Test that archives whose uncompressed extracted size exceeds the limit are rejected."""
    # Set extracted limit to 500 bytes
    monkeypatch.setattr(settings, "max_extracted_size_bytes", 500)

    files = {"file.txt": "A" * 2000}
    zip_buf = create_in_memory_zip(files)

    response = client.post(
        "/api/projects/upload",
        files={"file": ("bomb.zip", zip_buf, "application/zip")},
    )
    assert response.status_code == 400
    assert "exceeds limit" in response.json()["detail"]

def test_excessive_archive_entries_limit(client, monkeypatch):
    """Test that archives with an excessive number of entries are rejected."""
    monkeypatch.setattr(settings, "max_archive_entries", 5)

    # Create archive with 10 files
    files = {f"file_{i}.txt": f"content {i}" for i in range(10)}
    zip_buf = create_in_memory_zip(files)

    response = client.post(
        "/api/projects/upload",
        files={"file": ("many_files.zip", zip_buf, "application/zip")},
    )
    assert response.status_code == 400
    assert "exceeds maximum entries limit" in response.json()["detail"]

def test_secrets_and_dependency_exclusion_policy(client):
    """Test that secrets (.env) and bulky folders (node_modules, .git) are excluded from extraction."""
    files = {
        "src/app.js": "console.log('App running');",
        "package.json": '{"name": "test-app", "dependencies": {"react": "^18.0.0"}}',
        ".env": "SECRET_KEY=supersecretpassword123",
        ".env.local": "API_KEY=abcdef",
        "node_modules/dep/index.js": "module.exports = {};",
        ".git/config": "[core]\nrepositoryformatversion = 0",
        "id_rsa": "-----BEGIN RSA PRIVATE KEY-----",
    }
    zip_buf = create_in_memory_zip(files)

    response = client.post(
        "/api/projects/upload",
        files={"file": ("repo.zip", zip_buf, "application/zip")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_count"] == 2  # Only src/app.js and package.json
    assert data["excluded_items_count"] == 5  # .env, .env.local, node_modules, .git, id_rsa excluded
    assert "React" in data["detected_frameworks"]

    # Verify on filesystem that .env was NOT extracted
    source_dir = project_store.get_source_dir(data["project_id"])
    assert not os.path.exists(os.path.join(source_dir, ".env"))
    assert not os.path.exists(os.path.join(source_dir, "id_rsa"))
    assert not os.path.exists(os.path.join(source_dir, "node_modules"))
    assert os.path.exists(os.path.join(source_dir, "src", "app.js"))

def test_project_lifecycle_inspection_and_capabilities(client):
    """Test the complete inspection and capability matrix retrieval workflow."""
    files = {
        "app.py": "from fastapi import FastAPI\napp = FastAPI()",
        "package.json": '{"dependencies": {"react": "^19.0.0", "vite": "^6.0.0"}}',
    }
    zip_buf = create_in_memory_zip(files)

    # 1. Upload
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("fullstack.zip", zip_buf, "application/zip")},
    )
    assert upload_res.status_code == 201
    proj_id = upload_res.json()["project_id"]

    # 2. Inspect Project
    inspect_res = client.post(f"/api/projects/{proj_id}/inspect")
    assert inspect_res.status_code == 200
    inspect_data = inspect_res.json()
    assert inspect_data["project_id"] == proj_id
    assert len(inspect_data["capabilities"]) == 5
    assert inspect_data["file_count"] == 2

    # 3. Retrieve Capabilities
    caps_res = client.get(f"/api/projects/{proj_id}/capabilities")
    assert caps_res.status_code == 200
    caps = caps_res.json()
    assert len(caps) == 5
    cap_ids = [c["id"] for c in caps]
    assert "compatibility" in cap_ids
    assert "promise_audit" in cap_ids
    assert "live_incident" in cap_ids
    assert "dependency_radar" in cap_ids
    assert "fix_validation" in cap_ids

    # 4. List Projects
    list_res = client.get("/api/projects")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 5. Delete Project
    del_res = client.delete(f"/api/projects/{proj_id}")
    assert del_res.status_code == 200

    # 6. Verify 404 after deletion
    get_res = client.get(f"/api/projects/{proj_id}")
    assert get_res.status_code == 404

def test_invalid_project_id_404(client):
    """Test 404 behavior for non-existent project IDs."""
    res = client.get("/api/projects/prj-nonexistent")
    assert res.status_code == 404

    inspect_res = client.post("/api/projects/prj-nonexistent/inspect")
    assert inspect_res.status_code == 404

    caps_res = client.get("/api/projects/prj-nonexistent/capabilities")
    assert caps_res.status_code == 404


def test_upload_session_validation(client):
    """Test upload session initialization and validation rules."""
    # 1. Invalid file extension rejected
    bad_ext = client.post(
        "/api/projects/upload/session",
        json={"filename": "archive.tar.gz", "file_size": 1024},
    )
    assert bad_ext.status_code == 400
    assert "only .zip archives are supported" in bad_ext.json()["detail"]

    # 2. File size exceeds max upload limit (50 MB)
    too_large = client.post(
        "/api/projects/upload/session",
        json={"filename": "huge.zip", "file_size": 60 * 1024 * 1024},
    )
    assert too_large.status_code == 400
    assert "exceeds maximum allowed upload size" in too_large.json()["detail"]

    # 3. Valid session request
    valid = client.post(
        "/api/projects/upload/session",
        json={"filename": "valid-app.zip", "file_size": 15 * 1024 * 1024, "name": "Large Service"},
    )
    assert valid.status_code == 200
    data = valid.json()
    assert data["project_id"].startswith("prj-")
    assert data["strategy"] in ("direct", "vercel_blob")
    assert data["max_size_bytes"] == settings.max_upload_size_bytes


def test_large_zip_storage_reference_workflow_greater_than_4_5mb(client, tmp_path):
    """Test full ingestion and project-analysis workflow for a ZIP archive > 4.5 MB."""
    # Create a synthetic ZIP archive larger than 4.5 MB (5.2 MB)
    large_zip_path = tmp_path / "large_service_5mb.zip"
    padding = b"x" * (5 * 1024 * 1024)  # 5 MB uncompressed payload
    with zipfile.ZipFile(str(large_zip_path), "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("app/main.py", "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/items')\ndef get_items(): return []\n")
        zf.writestr("requirements.txt", "fastapi==0.115.0\nuvicorn>=0.30.0\npydantic>=2.8.0\n")
        zf.writestr("package.json", '{"name": "large-service", "dependencies": {"react": "^19.0.0"}}')
        zf.writestr("data/large_asset.txt", padding)

    zip_size = os.path.getsize(str(large_zip_path))
    assert zip_size > 4.5 * 1024 * 1024, f"Test archive must be > 4.5 MB, got {zip_size} bytes"

    # Ingest using object-storage reference endpoint
    file_url = f"file:///{large_zip_path.as_posix()}"
    complete_res = client.post(
        "/api/projects/upload/complete",
        json={
            "project_id": "prj-testlarge5mb",
            "name": "5MB Production Service",
            "blob_url": file_url,
        },
    )
    assert complete_res.status_code == 201
    data = complete_res.json()
    assert data["status"] == "ready"
    assert data["name"] == "5MB Production Service"
    assert "FastAPI" in data["detected_frameworks"]
    assert "React" in data["detected_frameworks"]

    # Verify project-analysis workflow starts successfully on the ingested > 4.5 MB project
    proj_id = data["project_id"]

    # 1. Capabilities check
    caps_res = client.get(f"/api/projects/{proj_id}/capabilities")
    assert caps_res.status_code == 200
    caps = caps_res.json()
    assert len(caps) == 5

    # 2. Compatibility assessment workflow (Feature 1)
    compat_res = client.post(f"/api/projects/{proj_id}/compatibility/assess")
    assert compat_res.status_code == 200
    compat_data = compat_res.json()
    assert compat_data["project_id"] == proj_id
    assert compat_data["overall_status"] in ("ready", "partially_ready", "incompatible")

    # 3. Spec audit workflow (Feature 2)
    audit_res = client.post(
        f"/api/projects/{proj_id}/audit",
        json={"requirements_text": "- Must expose GET /items endpoint\n- Must use FastAPI", "auto_detect_spec": False},
    )
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["project_id"] == proj_id
    assert len(audit_data["findings"]) >= 1


def test_cors_allows_production_frontend(client):
    """Verify that OPTIONS preflight allows the production frontend origin."""
    res = client.options(
        "/api/projects/upload",
        headers={
            "Origin": "https://sentinel-7f6f.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://sentinel-7f6f.vercel.app"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_upload_session_private_blob_token_generation(client, monkeypatch):
    """Test HMAC client token generation and private store metadata when Vercel Blob is configured."""
    fake_token = "vercel_blob_rw_teststore123_supersecretkey999"
    monkeypatch.setattr(settings, "blob_read_write_token", fake_token)

    res = client.post(
        "/api/projects/upload/session",
        json={"filename": "my_microservice.zip", "file_size": 12 * 1024 * 1024},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "vercel_blob"
    assert data["access"] == "private"
    assert data["store_connected"] is True
    assert data["client_token"].startswith("vercel_blob_client_teststore123_")
    assert "blob.vercel-storage.com" in data["upload_url"]

    # Decode and verify inner payload
    import base64
    import json
    parts = data["client_token"].split("_")
    encoded_inner = parts[4]
    decoded_inner = base64.b64decode(encoded_inner).decode("utf-8")
    sig, payload_b64 = decoded_inner.split(".")
    payload = json.loads(base64.b64decode(payload_b64).decode("utf-8"))
    assert payload["access"] == "private"
    assert payload["maximumSizeInBytes"] == settings.max_upload_size_bytes
    assert payload["pathname"].startswith("projects/prj-")


def test_upload_session_and_complete_authorization_required(client, monkeypatch):
    """Test that unauthorized requests are rejected when auth is enabled."""
    monkeypatch.setattr(settings, "auth_enabled", True)

    # 1. Session endpoint requires auth
    res_session = client.post(
        "/api/projects/upload/session",
        json={"filename": "test.zip", "file_size": 1024},
    )
    assert res_session.status_code == 401

    # 2. Complete endpoint requires auth
    res_complete = client.post(
        "/api/projects/upload/complete",
        json={"project_id": "prj-123", "blob_url": "file:///dummy.zip"},
    )
    assert res_complete.status_code == 401

    # 3. Direct upload requires auth
    res_upload = client.post(
        "/api/projects/upload",
        files={"file": ("test.zip", b"PK", "application/zip")},
    )
    assert res_upload.status_code == 401


def test_complete_storage_upload_invalid_and_corrupt_files(client, tmp_path):
    """Test that non-zip or corrupt files referenced from storage are rejected safely."""
    # 1. Non-existent file
    missing_res = client.post(
        "/api/projects/upload/complete",
        json={"project_id": "prj-missing", "blob_url": "file:///nonexistent/archive.zip"},
    )
    assert missing_res.status_code == 404

    # 2. Corrupt/plain text file disguised as zip
    bad_file = tmp_path / "not_a_zip.zip"
    bad_file.write_bytes(b"This is plain text, not a zip archive")
    bad_res = client.post(
        "/api/projects/upload/complete",
        json={"project_id": "prj-badzip", "blob_url": f"file:///{bad_file.as_posix()}"},
    )
    assert bad_res.status_code == 400
    assert "invalid" in bad_res.json()["detail"].lower() or "corrupt" in bad_res.json()["detail"].lower()


def test_complete_storage_upload_untrusted_host_ssrf_production(client, monkeypatch):
    """Test SSRF protection rejects untrusted storage domains in production."""
    monkeypatch.setattr(settings, "environment", "production")

    # Untrusted domain
    res = client.post(
        "/api/projects/upload/complete",
        json={"project_id": "prj-ssrf", "blob_url": "https://malicious-domain.com/evil.zip"},
    )
    assert res.status_code == 400
    assert "Untrusted blob storage host" in res.json()["detail"]

    # Invalid scheme
    res_scheme = client.post(
        "/api/projects/upload/complete",
        json={"project_id": "prj-scheme", "blob_url": "ftp://blob.vercel-storage.com/archive.zip"},
    )
    assert res_scheme.status_code == 400
    assert "Invalid blob URL scheme" in res_scheme.json()["detail"]


def test_complete_storage_upload_private_blob_bearer_authorization_header(client, monkeypatch, tmp_path):
    """Test that download requests to private storage include the Bearer authorization header."""
    fake_token = "vercel_blob_rw_teststore123_supersecretkey999"
    monkeypatch.setattr(settings, "blob_read_write_token", fake_token)

    # Create a small valid zip in memory
    files = {"app.py": "print('Hello Sentinel')"}
    zip_bytes = create_in_memory_zip(files).getvalue()

    captured_headers = {}

    class DummyResponse:
        status_code = 200
        content = zip_bytes

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, headers=None):
            if headers:
                captured_headers.update(headers)
            return DummyResponse()

        async def post(self, url, headers=None, json=None):
            return DummyResponse()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    res = client.post(
        "/api/projects/upload/complete",
        json={
            "project_id": "prj-private-test",
            "name": "Private Blob Service",
            "blob_url": "https://teststore123.private.blob.vercel-storage.com/projects/prj-private-test/archive.zip",
        },
    )
    assert res.status_code == 201
    assert res.json()["status"] == "ready"
    assert captured_headers.get("Authorization") == f"Bearer {fake_token}"
