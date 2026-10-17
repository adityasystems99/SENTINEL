"""Compatibility and integration readiness schemas for Feature 1."""
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CompatibilityStatus(str, Enum):
    COMPATIBLE = "compatible"
    PARTIALLY_READY = "partially_ready"
    NEEDS_CONFIGURATION = "needs_configuration"
    UNVERIFIED = "unverified"

class DetectedTechnology(BaseModel):
    name: str
    category: str  # "language", "framework", "telemetry", "testing", "deployment", "database"
    version: Optional[str] = None
    evidence_file: str
    notes: Optional[str] = None

class TelemetryReadiness(BaseModel):
    status: str  # "ready", "partial", "not_configured"
    has_opentelemetry: bool = False
    has_structured_logging: bool = False
    has_health_endpoint: bool = False
    evidence: List[str] = Field(default_factory=list)

class CompatibilityReport(BaseModel):
    project_id: str
    overall_status: CompatibilityStatus
    detected_technologies: List[DetectedTechnology] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    detected_routes: List[str] = Field(default_factory=list)
    telemetry_readiness: TelemetryReadiness
    integration_requirements: List[str] = Field(default_factory=list)
    missing_prerequisites: List[str] = Field(default_factory=list)
    recommended_setup_steps: List[str] = Field(default_factory=list)
    confidence: float = 0.85
    limitations: List[str] = Field(default_factory=list)
    inspected_at: float = Field(default_factory=time.time)
