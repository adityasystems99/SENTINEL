"""Data models for Feature 5: Controlled Fix Validation (Replay Lab)."""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ValidationVerdict(str, Enum):
    SUPPORTED_BY_EVIDENCE = "supported_by_evidence"
    NOT_SUPPORTED_BY_EVIDENCE = "not_supported_by_evidence"
    INCONCLUSIVE = "inconclusive"

class ExperimentRunMetrics(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    latencies_ms: List[float] = Field(default_factory=list)
    latency_p50_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    latency_p99_ms: Optional[float] = None
    error_messages: List[str] = Field(default_factory=list)
    executed_at: float

class CandidateFix(BaseModel):
    id: str
    title: str
    description: str
    risk_level: str = "LOW"
    configuration_diff: str

class FailureScenarioDefinition(BaseModel):
    id: str
    name: str
    target_service: str
    description: str
    expected_failure: str
    available_fixes: List[CandidateFix]

class BaselineRequest(BaseModel):
    scenario_id: str
    workload_count: int = 5

class BaselineExperimentResult(BaseModel):
    experiment_id: str
    scenario_id: str
    scenario_name: str
    target_service: str
    workload_count: int
    metrics: ExperimentRunMetrics
    status: str = "baseline_recorded"
    available_fixes: List[CandidateFix]
    approved_for_fix: bool = False

class FixValidationRequest(BaseModel):
    experiment_id: str
    fix_id: str
    approved: bool = Field(..., description="Explicit user approval required before running validation experiment")
    workload_count: int = 5

class FixValidationReport(BaseModel):
    experiment_id: str
    scenario_id: str
    scenario_name: str
    target_service: str
    fix_id: str
    fix_description: str
    baseline_metrics: ExperimentRunMetrics
    post_fix_metrics: ExperimentRunMetrics
    error_rate_delta: float
    recovery_behavior: str
    verdict: ValidationVerdict
    explanation: str
    measurements_summary: str
    confidence: float
    safety_notes: List[str] = Field(default_factory=list)
    completed_at: float
