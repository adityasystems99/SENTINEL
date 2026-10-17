"""Telemetry data schemas and validation models."""
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EventType(str, Enum):
    LOG = "log"
    TRACE = "trace"
    METRIC = "metric"
    DEPLOYMENT = "deployment"
    HEALTH = "health"

class TelemetryEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    service: str
    level: LogLevel = LogLevel.INFO
    event_type: EventType = EventType.LOG
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestBatchRequest(BaseModel):
    events: List[TelemetryEvent]

class IngestResponse(BaseModel):
    status: str = "success"
    received: int
    accepted: int
    deduplicated: int
    timestamp: float = Field(default_factory=time.time)
