"""Data models for Feature 4: Dependency and Impact Radar."""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ComponentHealthStatus(str, Enum):
    FAILING = "failing"
    AT_RISK = "at_risk"
    HEALTHY = "healthy"
    UNKNOWN = "unknown"

class DependencyRelationship(str, Enum):
    TARGET = "target_suspect"
    DIRECT_DEPENDENT = "direct_dependent"
    TRANSITIVE_DEPENDENT = "transitive_dependent"
    UPSTREAM_CALLER = "upstream_caller"
    DOWNSTREAM_DEPENDENCY = "downstream_dependency"
    SIBLING = "sibling"

class ImpactedComponent(BaseModel):
    service: str
    status: ComponentHealthStatus
    relationship: DependencyRelationship
    distance: int = Field(..., description="Graph distance in hops from suspected component")
    error_count: int = 0
    observed_failure: bool = Field(..., description="True if actual error logs were observed in active window")
    reason: str
    priority: int = Field(..., description="Investigation priority ranking (1 = highest)")
    recommended_action: str

class ServiceTopologyEdge(BaseModel):
    source: str
    target: str
    relation: str = "calls"
    call_count: int = 1
    error_count: int = 0
    evidence_source: str = "telemetry_trace_spans"
    sample_traces: List[str] = Field(default_factory=list)

class ServiceTopologyNode(BaseModel):
    id: str
    service: str
    status: ComponentHealthStatus = ComponentHealthStatus.HEALTHY
    tier: str = "service"
    error_count: int = 0
    total_requests: int = 0

class ImpactAnalysisRequest(BaseModel):
    suspected_component: str
    window_seconds: int = 600

class ImpactReport(BaseModel):
    suspected_component: str
    impacted_components: List[ImpactedComponent]
    dependency_paths: List[List[str]] = Field(default_factory=list)
    nodes: List[ServiceTopologyNode] = Field(default_factory=list)
    edges: List[ServiceTopologyEdge] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.95
    limitations: List[str] = Field(default_factory=list)
    suggested_investigation_steps: List[str] = Field(default_factory=list)
    analyzed_at: float
