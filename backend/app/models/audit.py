"""Promise vs. Reality Audit schemas for Feature 2."""
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AuditFindingStatus(str, Enum):
    IMPLEMENTED = "implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    MISSING = "missing"
    UNVERIFIED = "unverified"

class CodeLocation(BaseModel):
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    snippet: Optional[str] = None

class AuditFinding(BaseModel):
    requirement_id: str
    title: str
    description: str
    status: AuditFindingStatus
    supporting_files: List[CodeLocation] = Field(default_factory=list)
    reasoning: str
    validation_method: str  # "ast_inspection", "regex_pattern", "test_assertion_scan", "static_heuristic"
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    recommended_next_action: str

class PrioritizedWorkItem(BaseModel):
    priority: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    requirement_id: str
    title: str
    action: str
    estimated_effort: str = "Medium"

class AuditReport(BaseModel):
    project_id: str
    source_spec: str
    total_requirements: int
    implemented_count: int
    partially_implemented_count: int
    missing_count: int
    unverified_count: int
    compliance_score: float  # Percentage 0.0 - 100.0
    findings: List[AuditFinding] = Field(default_factory=list)
    prioritized_roadmap: List[PrioritizedWorkItem] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    audited_at: float = Field(default_factory=time.time)

class AuditSubmissionRequest(BaseModel):
    requirements_text: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    auto_detect_spec: bool = False

