"""Incident and graph schemas."""
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .telemetry import LogLevel, TelemetryEvent

class GraphNode(BaseModel):
    id: str
    label: str
    service: str
    event_type: str
    level: LogLevel
    timestamp: float
    is_error: bool = False
    message: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # "calls", "causes", "precedes", "deployed_before"
    weight: float = 1.0

class RootCauseCandidate(BaseModel):
    node_id: str
    service: str
    score: float  # 0.0 to 1.0
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    event_type: str
    message: str
    timestamp: float
    reasons: List[str] = Field(default_factory=list)

class IncidentReport(BaseModel):
    incident_id: str
    title: str
    status: str = "active"  # "active", "mitigated", "resolved"
    severity: str = "HIGH"   # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    started_at: float
    detected_at: float = Field(default_factory=time.time)
    event_count: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    root_cause_ranking: List[RootCauseCandidate]
    summary: str
    recommended_actions: List[str] = Field(default_factory=list)
    historical_intelligence: Optional[Any] = None
    owner_id: str = "demo_user"


class IncidentSummary(BaseModel):
    incident_id: str
    title: str
    status: str
    severity: str
    started_at: float
    detected_at: float
    event_count: int
    top_suspect: Optional[str] = None
    top_suspect_service: Optional[str] = None
    owner_id: str = "demo_user"
