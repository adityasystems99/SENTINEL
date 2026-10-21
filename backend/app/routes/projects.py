"""Project ingestion, metadata, and workspace API routes."""
import os
import logging

logger = logging.getLogger(__name__)
import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from ..config import settings
from ..models.project import (
    CapabilityStatus,
    ProjectInspectionResult,
    ProjectMetadata,
    ProjectStatus,
    ProjectSummary,
)
from ..models.compatibility import CompatibilityReport
from ..models.audit import AuditReport, AuditSubmissionRequest
from ..services.ingestion import extract_archive_safely, validate_archive
from ..services.compatibility_engine import run_compatibility_assessment
from ..services.audit_engine import run_audit_engine
from ..storage.project_store import project_store
from ..auth.security import UserContext, get_current_user, verify_project_ownership
from ..auth.rate_limiter import check_rate_limit
import hmac
import hashlib
import json
import base64
from typing import Tuple
import urllib.parse
import urllib.request
import httpx
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["Projects"])

class UploadSessionRequest(BaseModel):
    filename: str
    file_size: int
    content_type: Optional[str] = "application/zip"
    name: Optional[str] = None

class UploadSessionResponse(BaseModel):
    strategy: str  # "vercel_blob" or "direct"
    project_id: str
    upload_url: str
    client_token: Optional[str] = None
    pathname: Optional[str] = None
    max_size_bytes: int
    access: str = "private"
    store_connected: bool = False
    message: Optional[str] = None

class UploadCompleteRequest(BaseModel):
    project_id: str
    name: Optional[str] = None
    blob_url: str


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


def generate_vercel_blob_client_token(
    blob_token: str,
    pathname: str,
    max_size_bytes: int,
    valid_until_seconds: int = 900,
    access: str = "private",
) -> Tuple[str, str]:
    """Generate scoped short-lived client upload token using HMAC-SHA256 matching Vercel Blob spec."""
    parts = blob_token.split("_")
    if len(parts) < 4:
        raise ValueError("Invalid BLOB_READ_WRITE_TOKEN format. Expected vercel_blob_rw_<store_id>_<secret>")
    store_id = parts[3]
    valid_until_ms = int((time.time() + valid_until_seconds) * 1000)
    payload_dict = {
        "pathname": pathname,
        "validUntil": valid_until_ms,
        "maximumSizeInBytes": max_size_bytes,
        "allowedContentTypes": ["application/zip", "application/x-zip-compressed", "application/octet-stream"],
        "addRandomSuffix": False,
        "access": access,
        "allowOverwrite": True,
    }
    payload_b64 = base64.b64encode(json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")).decode("utf-8")
    signature = hmac.new(blob_token.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    inner = f"{signature}.{payload_b64}"
    inner_b64 = base64.b64encode(inner.encode("utf-8")).decode("utf-8")
    client_token = f"vercel_blob_client_{store_id}_{inner_b64}"
    upload_url = f"https://blob.vercel-storage.com/{pathname}"
    return client_token, upload_url


def ingest_project_archive_bytes(
    project_id: str,
    project_name: str,
    file_bytes: bytes,
    filename: str,
    current_user: UserContext,
) -> ProjectMetadata:
    """Validate archive, extract safely, inspect frameworks, and persist project metadata."""
    if len(file_bytes) > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archive exceeds maximum upload size limit of {max_mb} MB ({settings.max_upload_size_bytes} bytes).",
        )

    metadata = ProjectMetadata(
        project_id=project_id,
        name=project_name,
        status=ProjectStatus.UPLOADED,
        created_at=time.time(),
        updated_at=time.time(),
        archive_size_bytes=len(file_bytes),
        owner_id=current_user.user_id,
    )

    metadata.status = ProjectStatus.VALIDATING
    try:
        validate_archive(file_bytes, filename)
    except ValueError as e:
        metadata.status = ProjectStatus.FAILED
        metadata.error_message = str(e)
        project_store.save_project(metadata)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

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

    metadata.status = ProjectStatus.READY
    metadata.file_count = stats["file_count"]
    metadata.directory_count = stats["directory_count"]
    metadata.extracted_size_bytes = stats["extracted_size_bytes"]
    metadata.excluded_items_count = stats["excluded_items_count"]
    metadata.detected_frameworks = stats["detected_frameworks"]
    metadata.updated_at = time.time()

    project_store.save_project(metadata)
    return metadata


@router.post(
    "/upload/session",
    response_model=UploadSessionResponse,
    dependencies=[Depends(check_rate_limit(max_requests=settings.expensive_rate_limit_per_minute, route_scope="upload"))],
)
async def create_upload_session(
    request: UploadSessionRequest,
    current_user: UserContext = Depends(get_current_user),
):
    """Initialize an authorized upload session. Uses Vercel Blob object storage if configured, or direct upload."""
    if not request.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type: only .zip archives are supported",
        )

    if request.file_size <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size must be greater than 0 bytes.")
    if request.file_size > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archive size exceeds maximum allowed upload size ({max_mb} MB).",
        )

    project_id = f"prj-{uuid.uuid4().hex[:8]}"
    clean_filename = os.path.basename(request.filename).replace(" ", "_")

    # If Vercel Blob storage is configured via BLOB_READ_WRITE_TOKEN, issue client upload token
    blob_token = settings.blob_read_write_token
    if blob_token:
        pathname = f"projects/{project_id}/{clean_filename}"
        try:
            client_token, upload_url = generate_vercel_blob_client_token(
                blob_token=blob_token,
                pathname=pathname,
                max_size_bytes=settings.max_upload_size_bytes,
                access="private",
            )
            return UploadSessionResponse(
                strategy="vercel_blob",
                project_id=project_id,
                upload_url=upload_url,
                client_token=client_token,
                pathname=pathname,
                max_size_bytes=settings.max_upload_size_bytes,
                access="private",
                store_connected=True,
                message="Authorized private Vercel Blob session ready for direct client upload.",
            )
        except Exception:
            pass

    # Fallback to direct multipart upload (works in dev and for <= 4.5 MB in production)
    return UploadSessionResponse(
        strategy="direct",
        project_id=project_id,
        upload_url="/api/projects/upload",
        max_size_bytes=settings.max_upload_size_bytes,
        access="direct",
        store_connected=False,
        message="Direct upload active (Vercel Serverless Functions limit payload to 4.5 MB in production).",
    )


@router.post(
    "/upload/complete",
    response_model=ProjectMetadata,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_rate_limit(max_requests=settings.expensive_rate_limit_per_minute, route_scope="upload"))],
)
async def complete_storage_upload(
    request: UploadCompleteRequest,
    response: Response,
    current_user: UserContext = Depends(get_current_user),
):
    """Complete project ingestion from an authorized object-storage reference (e.g. Vercel Blob)."""
    parsed = urllib.parse.urlparse(request.blob_url)
    if parsed.scheme not in ("https", "http", "file"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid blob URL scheme. Must be HTTPS.")

    # In production, enforce trusted storage domains to prevent SSRF
    if settings.environment == "production" and parsed.scheme == "https":
        if not (parsed.netloc.endswith(".blob.vercel-storage.com") or parsed.netloc == "blob.vercel-storage.com"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Untrusted blob storage host.")

    # Retrieve file bytes from storage reference
    try:
        if parsed.scheme == "file":
            # Support file:// for local integration testing
            file_path = urllib.request.url2pathname(parsed.path)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Referenced local file does not exist: {file_path}")
            with open(file_path, "rb") as f:
                file_bytes = f.read()
        else:
            headers = {}
            blob_token = settings.blob_read_write_token
            if blob_token:
                headers["Authorization"] = f"Bearer {blob_token}"
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.get(request.blob_url, headers=headers)
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to fetch uploaded file from storage reference: HTTP {resp.status_code}"
                    )
                file_bytes = resp.content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error retrieving file from object storage: {str(e)}"
        )

    project_name = request.name or "uploaded-project"
    filename = os.path.basename(parsed.path) or "archive.zip"

    metadata = None
    ingestion_error = None
    storage_cleanup_status = "skipped"

    try:
        metadata = ingest_project_archive_bytes(
            project_id=request.project_id,
            project_name=project_name,
            file_bytes=file_bytes,
            filename=filename,
            current_user=current_user,
        )
    except Exception as e:
        ingestion_error = e
        raise
    finally:
        # Best-effort cleanup of temporary object storage after both successful and failed inspections
        blob_token = settings.blob_read_write_token
        if blob_token and parsed.scheme == "https":
            logger.info("Attempting temporary blob cleanup for project %s", request.project_id)
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    del_resp = await client.post(
                        "https://blob.vercel-storage.com/delete",
                        headers={
                            "Authorization": f"Bearer {blob_token}",
                            "x-api-version": "7",
                        },
                        json={"urls": [request.blob_url]},
                    )
                    if del_resp.status_code in (200, 204):
                        storage_cleanup_status = "confirmed"
                        logger.info(
                            "Temporary blob cleanup confirmed for project %s (HTTP %d)",
                            request.project_id,
                            del_resp.status_code,
                        )
                    else:
                        storage_cleanup_status = "failed"
                        logger.warning(
                            "Temporary blob cleanup failed for project %s: HTTP %d",
                            request.project_id,
                            del_resp.status_code,
                        )
            except Exception as e:
                storage_cleanup_status = "error"
                logger.warning(
                    "Temporary blob cleanup status unknown for project %s: network error (%s)",
                    request.project_id,
                    type(e).__name__,
                )
        else:
            logger.info("Temporary blob cleanup skipped for project %s: storage credentials not configured", request.project_id)

        # Set safe, non-sensitive header indicating cleanup outcome
        response.headers["x-storage-cleanup"] = storage_cleanup_status

        # If ingestion had raised an HTTPException, attach header to that exception as well
        if ingestion_error and isinstance(ingestion_error, HTTPException):
            if ingestion_error.headers is None:
                ingestion_error.headers = {}
            ingestion_error.headers["x-storage-cleanup"] = storage_cleanup_status

    if metadata:
        metadata.storage_cleanup = storage_cleanup_status
        project_store.save_project(metadata)
        return metadata


@router.post(
    "/upload",
    response_model=ProjectMetadata,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_rate_limit(max_requests=settings.expensive_rate_limit_per_minute, route_scope="upload"))],
)
async def upload_project_archive(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    current_user: UserContext = Depends(get_current_user),
):
    """Securely upload, validate, and isolate a project ZIP archive scoped to the authenticated user."""
    file_bytes = await file.read()
    filename = file.filename or "archive.zip"
    project_name = name or (filename.rsplit(".", 1)[0] if filename else "untitled-project")
    project_id = f"prj-{uuid.uuid4().hex[:8]}"
    return ingest_project_archive_bytes(project_id, project_name, file_bytes, filename, current_user)


@router.get("", response_model=List[ProjectSummary])
async def list_projects(current_user: UserContext = Depends(get_current_user)):
    """List ingested projects scoped to the authenticated user or workspace."""
    projects = project_store.list_projects()
    summaries = []
    for p in reversed(projects):
        # Admins can see all projects; regular users can only see projects they own
        if current_user.role != "admin" and p.owner_id != current_user.user_id:
            continue
        summaries.append(ProjectSummary(
            project_id=p.project_id,
            name=p.name,
            status=p.status,
            created_at=p.created_at,
            file_count=p.file_count,
            detected_frameworks=p.detected_frameworks,
            owner_id=p.owner_id,
        ))
    return summaries

@router.get("/{project_id}", response_model=ProjectMetadata)
async def get_project(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Retrieve metadata and lifecycle state for a specific project with ownership verification."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)
    return proj

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Delete a project workspace and associated metadata with ownership verification."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)

    success = project_store.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return {"status": "deleted", "project_id": project_id}

@router.post("/{project_id}/inspect", response_model=ProjectInspectionResult)
async def inspect_project(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Start inspection of an ingested project workspace and generate capability availability."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)

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
async def get_project_inspection(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Retrieve inspection status and workspace capabilities for a project."""
    return await inspect_project(project_id, current_user=current_user)

@router.get("/{project_id}/capabilities", response_model=List[CapabilityStatus])
async def get_project_capabilities(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Retrieve available SENTINEL capabilities and their readiness for this project."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)
    return get_default_capabilities(proj.detected_frameworks)


# ==========================================
# Feature 1: Compatibility Engine Endpoints
# ==========================================

@router.post(
    "/{project_id}/compatibility/assess",
    response_model=CompatibilityReport,
    dependencies=[Depends(check_rate_limit(max_requests=settings.expensive_rate_limit_per_minute, route_scope="compatibility"))],
)
async def assess_project_compatibility(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Run safe static analysis on the project to determine compatibility and integration readiness."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)

    if proj.status != ProjectStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assess project in status '{proj.status.value}'. Project must be 'ready'."
        )

    source_dir = project_store.get_source_dir(project_id)
    if not os.path.exists(source_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source directory for project '{project_id}' does not exist on disk."
        )

    report = run_compatibility_assessment(project_id, source_dir)
    project_store.save_compatibility_report(project_id, report.model_dump())
    return report


@router.get("/{project_id}/compatibility", response_model=CompatibilityReport)
async def get_compatibility_report(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Retrieve the latest compatibility assessment report for a project."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)

    report_dict = project_store.get_compatibility_report(project_id)
    if not report_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No compatibility report found for project '{project_id}'. Run an assessment first."
        )
    return CompatibilityReport(**report_dict)


# ==========================================
# Feature 2: Promise vs Reality Audit Endpoints
# ==========================================

SUPPORTED_SPEC_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".rst", ".csv"}

@router.post(
    "/{project_id}/audit",
    response_model=AuditReport,
    dependencies=[Depends(check_rate_limit(max_requests=settings.expensive_rate_limit_per_minute, route_scope="audit"))],
)
async def run_audit(
    project_id: str,
    request: AuditSubmissionRequest,
    current_user: UserContext = Depends(get_current_user),
):
    """Run source-code audit engine comparing provided requirements with actual implementation."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)

    if proj.status != ProjectStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot audit project in status '{proj.status.value}'. Project must be 'ready'."
        )

    source_dir = project_store.get_source_dir(project_id)
    if not os.path.exists(source_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source directory for project '{project_id}' does not exist on disk."
        )

    if not request.requirements_text and not request.auto_detect_spec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requirements document is required. Provide 'requirements_text' or enable 'auto_detect_spec'."
        )

    report = run_audit_engine(
        project_id=project_id,
        source_dir=source_dir,
        requirements_text=request.requirements_text,
        acceptance_criteria=request.acceptance_criteria,
        auto_detect_spec=request.auto_detect_spec,
    )
    project_store.save_audit_report(project_id, report.model_dump())
    return report


@router.post(
    "/{project_id}/audit/file",
    response_model=AuditReport,
    dependencies=[Depends(check_rate_limit(max_requests=settings.expensive_rate_limit_per_minute, route_scope="audit"))],
)
async def run_audit_with_file(
    project_id: str,
    file: UploadFile = File(...),
    acceptance_criteria: Optional[str] = Form(None),
    current_user: UserContext = Depends(get_current_user),
):
    """Run source-code audit engine by uploading a requirements document (.md, .txt, .json, .yaml, .rst)."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)

    if proj.status != ProjectStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot audit project in status '{proj.status.value}'. Project must be 'ready'."
        )

    source_dir = project_store.get_source_dir(project_id)
    if not os.path.exists(source_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source directory for project '{project_id}' does not exist on disk."
        )

    # Validate file format and size
    filename = file.filename or "unknown"
    _, ext = os.path.splitext(filename)
    ext_lower = ext.lower()
    if ext_lower not in SUPPORTED_SPEC_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document format '{ext}'. Only text-based requirements documents ({', '.join(sorted(SUPPORTED_SPEC_EXTENSIONS))}) are supported."
        )

    content_bytes = await file.read()
    if len(content_bytes) > 10 * 1024 * 1024:  # 10 MB limit for spec documents
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Requirements document exceeds maximum allowed size (10 MB).",
        )

    try:
        requirements_text = content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read requirements file: {str(e)}"
        )

    report = run_audit_engine(
        project_id=project_id,
        source_dir=source_dir,
        requirements_text=requirements_text,
        acceptance_criteria=acceptance_criteria,
        spec_filename=filename,
    )
    project_store.save_audit_report(project_id, report.model_dump())
    return report


@router.get("/{project_id}/audit", response_model=AuditReport)
async def get_audit_report(project_id: str, current_user: UserContext = Depends(get_current_user)):
    """Retrieve the latest promise vs. reality audit report for a project."""
    proj = project_store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    verify_project_ownership(proj, current_user)

    report_dict = project_store.get_audit_report(project_id)
    if not report_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit report found for project '{project_id}'. Run an audit first."
        )
    return AuditReport(**report_dict)
