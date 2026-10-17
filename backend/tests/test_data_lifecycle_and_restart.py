"""Tests verifying and documenting data lifecycle and restart behavior for SENTINEL.
Step 6: Document and verify what data survives a backend restart vs what is ephemeral in memory.
Architecture: Preserves zero-infrastructure FastAPI design (no SQLite, no message broker, no external DB).
"""
import os
import shutil
import tempfile
import time
import pytest
from backend.app.storage.project_store import ProjectStore
from backend.app.storage.memory_store import MemoryTelemetryStore
from backend.app.models.project import ProjectMetadata, ProjectStatus
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from backend.app.services.rag.vector_store import LocalVectorStore
from backend.app.services.rag.loader import load_knowledge_directory


def test_project_data_survives_restart():
    """Verify that uploaded project source files and metadata survive backend restarts.
    
    ProjectStore persists data to disk at data/projects/{project_id}/.
    A new instance of ProjectStore (simulating backend reboot) reloads all existing projects.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Instance 1: Create project and write metadata & file
        store1 = ProjectStore(base_dir=tmp_dir)
        proj_id = "test-restart-proj"
        meta = ProjectMetadata(
            project_id=proj_id,
            name="Restart Test Project",
            source_zip_name="demo.zip",
            file_count=3,
            total_bytes=1024,
            status=ProjectStatus.READY,
            created_at=time.time(),
        )
        store1.save_project(meta)
        
        # Write dummy project file to source directory
        source_dir = store1.get_source_dir(proj_id)
        os.makedirs(source_dir, exist_ok=True)
        with open(os.path.join(source_dir, "app.py"), "w", encoding="utf-8") as f:
            f.write("print('hello restart')")
            
        assert store1.get_project(proj_id) is not None
        assert store1.get_project(proj_id).name == "Restart Test Project"

        # 2. Instance 2: Simulate Backend Restart (instantiating fresh store from disk)
        store2 = ProjectStore(base_dir=tmp_dir)
        reloaded_proj = store2.get_project(proj_id)
        
        # Verification: Project metadata and files survive!
        assert reloaded_proj is not None, "Project metadata must survive backend restart via disk persistence"
        assert reloaded_proj.name == "Restart Test Project"
        assert reloaded_proj.file_count == 3
        
        # Verify physical file on disk
        persisted_file = os.path.join(source_dir, "app.py")
        assert os.path.exists(persisted_file)
        with open(persisted_file, "r", encoding="utf-8") as f:
            assert f.read() == "print('hello restart')"


def test_telemetry_events_are_ephemeral_in_memory():
    """Document and verify that raw telemetry events and active incident reports DO NOT survive restart.
    
    SENTINEL uses MemoryTelemetryStore (pure in-memory storage).
    When backend process restarts, telemetry events and active incident reports are reset.
    """
    store1 = MemoryTelemetryStore()
    store1.add_events([
        TelemetryEvent(
            service="web-gateway",
            level=LogLevel.INFO,
            event_type=EventType.LOG,
            message="Request processed"
        )
    ])
    assert len(store1.get_events()) == 1

    # Simulate reboot: Fresh MemoryTelemetryStore
    store2 = MemoryTelemetryStore()
    assert len(store2.get_events()) == 0, (
        "MemoryTelemetryStore is ephemeral in-memory; events do NOT survive backend restart."
    )
    assert len(store2.list_incidents()) == 0, (
        "Incident reports are held in-memory and do NOT survive backend restart."
    )


def test_historical_knowledge_survives_and_rebuilds_index_on_startup():
    """Verify that historical incident records survive restarts and index is automatically rebuilt.
    
    Knowledge markdown records are version-controlled on the filesystem in backend/knowledge/.
    While the LocalVectorStore index is in-memory, the lifespan handler re-indexes
    all markdown documents on every startup without loss of intelligence.
    """
    # 1. Verify markdown records exist on disk
    knowledge_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge"))
    assert os.path.exists(knowledge_dir), "Knowledge directory must exist on disk"
    
    docs, chunks = load_knowledge_directory(knowledge_dir)
    assert len(docs) >= 5, "At least 5 version-controlled knowledge documents must exist"
    assert len(chunks) >= 15, "Documents must be parsed into indexed chunks"

    # 2. Simulate fresh in-memory vector store on reboot
    fresh_vector_store = LocalVectorStore()
    assert fresh_vector_store.total_chunks == 0

    # 3. Lifespan startup handler re-indexes from disk
    indexed = fresh_vector_store.add_chunks(chunks)
    assert indexed > 0
    assert fresh_vector_store.total_chunks == len(chunks)

    # 4. Search query works immediately after reboot
    results = fresh_vector_store.search("HikariPool connection pool saturation", top_k=2)
    assert len(results) > 0
    assert results[0].doc_id in ("INC-2025-0812", "RUNBOOK-INV-001")
