"""Thread-safe in-memory store for telemetry events and incident reports.
Strictly adheres to engineering constraints: NO SQLite, NO external DBs, NO message queues.
"""
import hashlib
import threading
from typing import Dict, List, Optional, Set
from ..models.telemetry import TelemetryEvent, LogLevel
from ..models.incident import IncidentReport

class MemoryTelemetryStore:
    def __init__(self, max_dedup_cache: int = 10000):
        self._lock = threading.RLock()
        self._events: List[TelemetryEvent] = []
        self._events_by_id: Dict[str, TelemetryEvent] = {}
        self._events_by_trace: Dict[str, List[TelemetryEvent]] = {}
        self._events_by_service: Dict[str, List[TelemetryEvent]] = {}
        self._dedup_hashes: Set[str] = set()
        self._max_dedup_cache = max_dedup_cache
        self._incidents: Dict[str, IncidentReport] = {}

    def _generate_fingerprint(self, event: TelemetryEvent) -> str:
        """Create a deterministic hash for deduplicating identical events."""
        # If event_id is uniquely specified or auto-generated, we fingerprint the content:
        # service + timestamp (within 100ms bucket) + message + trace_id + span_id
        time_bucket = int(event.timestamp * 10)  # 100ms window
        raw = f"{event.service}:{time_bucket}:{event.event_type}:{event.level}:{event.message}:{event.trace_id}:{event.span_id}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def add_events(self, events: List[TelemetryEvent]) -> tuple[int, int]:
        """Add events with deduplication. Returns (accepted_count, deduplicated_count)."""
        accepted = 0
        deduplicated = 0

        with self._lock:
            for event in events:
                fingerprint = self._generate_fingerprint(event)
                
                # Check if event_id is already seen or content fingerprint seen
                if event.event_id in self._events_by_id or fingerprint in self._dedup_hashes:
                    deduplicated += 1
                    continue

                # Add to deduplication cache
                if len(self._dedup_hashes) >= self._max_dedup_cache:
                    # Prune older half of dedup cache to maintain bounds
                    self._dedup_hashes = set(list(self._dedup_hashes)[len(self._dedup_hashes) // 2:])
                
                self._dedup_hashes.add(fingerprint)
                self._events.append(event)
                self._events_by_id[event.event_id] = event

                if event.trace_id:
                    self._events_by_trace.setdefault(event.trace_id, []).append(event)

                self._events_by_service.setdefault(event.service, []).append(event)
                accepted += 1

        return accepted, deduplicated

    def get_events(
        self,
        service: Optional[str] = None,
        level: Optional[LogLevel] = None,
        trace_id: Optional[str] = None,
        since_timestamp: Optional[float] = None,
        limit: int = 200,
    ) -> List[TelemetryEvent]:
        """Query events with optional filters."""
        with self._lock:
            if trace_id and trace_id in self._events_by_trace:
                candidates = self._events_by_trace[trace_id]
            elif service and service in self._events_by_service:
                candidates = self._events_by_service[service]
            else:
                candidates = self._events

            filtered = []
            for ev in reversed(candidates):
                if service and ev.service != service:
                    continue
                if level and ev.level != level:
                    continue
                if since_timestamp and ev.timestamp < since_timestamp:
                    continue
                filtered.append(ev)
                if len(filtered) >= limit:
                    break

            return list(reversed(filtered))

    def get_recent_errors(self, window_seconds: float = 300.0) -> List[TelemetryEvent]:
        """Fetch error and critical events within the last `window_seconds`."""
        with self._lock:
            if not self._events:
                return []
            latest_time = self._events[-1].timestamp
            cutoff = latest_time - window_seconds
            return [
                ev for ev in self._events
                if ev.timestamp >= cutoff and ev.level in (LogLevel.ERROR, LogLevel.CRITICAL)
            ]

    def save_incident(self, incident: IncidentReport) -> None:
        with self._lock:
            self._incidents[incident.incident_id] = incident

    def get_incident(self, incident_id: str) -> Optional[IncidentReport]:
        with self._lock:
            return self._incidents.get(incident_id)

    def list_incidents(self) -> List[IncidentReport]:
        with self._lock:
            return list(self._incidents.values())

    def clear(self) -> None:
        """Clear all events and incidents (useful for test resets)."""
        with self._lock:
            self._events.clear()
            self._events_by_id.clear()
            self._events_by_trace.clear()
            self._events_by_service.clear()
            self._dedup_hashes.clear()
            self._incidents.clear()

    @property
    def total_events(self) -> int:
        with self._lock:
            return len(self._events)

# Global singleton store
store = MemoryTelemetryStore()
