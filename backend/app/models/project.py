"""Project models and lifecycle schemas."""
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ProjectStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    READY = "ready"
    FAILED = "failed"
    INSPECTING = "inspecting"

class CapabilityStatus(BaseModel):
    id: str  # "compatibility", "promise_audit", "live_incident", "dependency_radar", "fix_validation"
    title: str
    status: str  # "available", "ready_for_analysis", "unsupported", "pending"
    description: str
    readiness_notes: Optional[str] = None

class ProjectMetadata(BaseModel):
    project_id: str
    name: str
    status: ProjectStatus = ProjectStatus.UPLOADED
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    archive_size_bytes: int = 0
    extracted_size_bytes: int = 0
    file_count: int = 0
    directory_count: int = 0
    excluded_items_count: int = 0
    detected_frameworks: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None

class ProjectSummary(BaseModel):
    project_id: str
    name: str
    status: ProjectStatus
    created_at: float
    file_count: int
    detected_frameworks: List[str]

class ProjectInspectionResult(BaseModel):
    project_id: str
    status: ProjectStatus
    inspected_at: float = Field(default_factory=time.time)
    summary: str
    file_count: int
    detected_frameworks: List[str]
    sample_files: List[str] = Field(default_factory=list)
    capabilities: List[CapabilityStatus] = Field(default_factory=list)
