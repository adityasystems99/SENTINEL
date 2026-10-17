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
