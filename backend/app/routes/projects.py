"""Project ingestion, metadata, and workspace API routes."""
import os
import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from ..models.project import (
    CapabilityStatus,
    ProjectInspectionResult,
    ProjectMetadata,
    ProjectStatus,
    ProjectSummary,
)
from ..services.ingestion import extract_archive_safely, validate_archive
from ..storage.project_store import project_store

router = APIRouter(prefix="/projects", tags=["Projects"])

def get_default_capabilities(detected_frameworks: List[str]) -> List[CapabilityStatus]:
    """Derive initial capability status for the 5 SENTINEL workspaces."""
    has_stack = len(detected_frameworks) > 0
    return [
        CapabilityStatus(
            id="compatibility",
            title="Feature 1 — Can I use it? (Integration Readiness)",
            status="available" if has_stack else "pending",
            description="Inspects project technologies, dependencies, and telemetry instrumentation readiness.",
            readiness_notes=f"Detected: {', '.join(detected_frameworks) if has_stack else 'Awaiting analysis'}",
        ),
        CapabilityStatus(
            id="promise_audit",
            title="Feature 2 — Have I built what I promised? (Spec vs Reality Audit)",
            status="available",
            description="Compares specification/requirements with actual implemented source code.",
            readiness_notes="Source code workspace indexed and available for AST inspection.",
        ),
        CapabilityStatus(
            id="live_incident",
            title="Feature 3 — Why is my application failing? (Live Incident RCA)",
            status="available",
            description="Correlates runtime errors, trace spans, and deployments to rank root causes.",
            readiness_notes="NetworkX incident graph engine ready for telemetry stream.",
        ),
        CapabilityStatus(
            id="dependency_radar",
            title="Feature 4 — What else could break? (Dependency & Impact Radar)",
            status="available",
            description="Maps service call topologies and computes cascading blast radius.",
            readiness_notes="Service topology extraction available from manifests.",
        ),
        CapabilityStatus(
            id="fix_validation",
            title="Feature 5 — Does my fix actually work? (Controlled Fix Validation)",
            status="available",
            description="Replays test scenarios and verifies before/after telemetry deltas.",
            readiness_notes="Regression test runner available.",
        ),
    ]

@router.post("/upload", response_model=ProjectMetadata, status_code=status.HTTP_201_CREATED)
async def upload_project_archive(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
):
    """Securely upload, validate, and isolate a project ZIP archive."""
    # 1. Read file bytes
    file_bytes = await file.read()
    project_name = name or (file.filename.rsplit(".", 1)[0] if file.filename else "untitled-project")
    project_id = f"prj-{uuid.uuid4().hex[:8]}"

    # Initial metadata record (state: uploaded)
    metadata = ProjectMetadata(
        project_id=project_id,
        name=project_name,
        status=ProjectStatus.UPLOADED,
        created_at=time.time(),
        updated_at=time.time(),
        archive_size_bytes=len(file_bytes),
    )

    # 2. State transition: validating
    metadata.status = ProjectStatus.VALIDATING
    try:
        validate_archive(file_bytes, file.filename or "archive.zip")
    except ValueError as e:
        metadata.status = ProjectStatus.FAILED
        metadata.error_message = str(e)
        project_store.save_project(metadata)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 3. State transition: extracting into isolated workspace
    source_dir = project_store.get_source_dir(project_id)
    try:
        stats = extract_archive_safely(file_bytes, source_dir)
    except ValueError as e:
        metadata.status = ProjectStatus.FAILED
        metadata.error_message = str(e)
        project_store.save_project(metadata)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        metadata.status = ProjectStatus.FAILED
        metadata.error_message = f"Extraction failure: {str(e)}"
        project_store.save_project(metadata)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to extract archive: {str(e)}")

    # 4. State transition: ready
    metadata.status = ProjectStatus.READY
    metadata.file_count = stats["file_count"]
    metadata.directory_count = stats["directory_count"]
    metadata.extracted_size_bytes = stats["extracted_size_bytes"]
    metadata.excluded_items_count = stats["excluded_items_count"]
    metadata.detected_frameworks = stats["detected_frameworks"]
    metadata.updated_at = time.time()

    project_store.save_project(metadata)
    return metadata

@router.get("", response_model=List[ProjectSummary])
async def list_projects():
    """List all ingested projects."""
    projects = project_store.list_projects()
    summaries = []
    for p in reversed(projects):
        summaries.append(ProjectSummary(
            project_id=p.project_id,
            name=p.name,
            status=p.status,
            created_at=p.created_at,
            file_count=p.file_count,
            detected_frameworks=p.detected_frameworks,
        ))
    return summaries

@router.get("/{project_id}", response_model=ProjectMetadata)
async def get_project(project_id: str):
    """Retrieve metadata and lifecycle state for a specific project."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return proj

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project workspace and associated metadata."""
    success = project_store.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return {"status": "deleted", "project_id": project_id}

@router.post("/{project_id}/inspect", response_model=ProjectInspectionResult)
async def inspect_project(project_id: str):
    """Start inspection of an ingested project workspace and generate capability availability."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")

    if proj.status != ProjectStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot inspect project in status '{proj.status.value}'. Project must be 'ready'."
        )

    # Gather file sample
    source_dir = project_store.get_source_dir(project_id)
    sample_files = []
    if os.path.exists(source_dir):
        for root, _, files in os.walk(source_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), source_dir).replace("\\", "/")
                sample_files.append(rel)
                if len(sample_files) >= 30:
                    break
            if len(sample_files) >= 30:
                break

    capabilities = get_default_capabilities(proj.detected_frameworks)

    summary = (
        f"Project '{proj.name}' inspected successfully. Contains {proj.file_count} source files "
        f"({proj.extracted_size_bytes} bytes). Detected stack: {', '.join(proj.detected_frameworks) or 'Generic'}. "
        f"{proj.excluded_items_count} items safely excluded."
    )

    return ProjectInspectionResult(
        project_id=project_id,
        status=proj.status,
        inspected_at=time.time(),
        summary=summary,
        file_count=proj.file_count,
        detected_frameworks=proj.detected_frameworks,
        sample_files=sample_files,
        capabilities=capabilities,
    )

@router.get("/{project_id}/inspect", response_model=ProjectInspectionResult)
async def get_project_inspection(project_id: str):
    """Retrieve inspection status and workspace capabilities for a project."""
    return await inspect_project(project_id)

@router.get("/{project_id}/capabilities", response_model=List[CapabilityStatus])
async def get_project_capabilities(project_id: str):
    """Retrieve available SENTINEL capabilities and their readiness for this project."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return get_default_capabilities(proj.detected_frameworks)
