"""Phase 10 Evaluation Scenarios: Unfamiliar Failure & Missing Span Telemetry.
Isolates ground-truth definitions from telemetry inputs so the ranker cannot inspect answers.
"""
import time
from typing import Dict, List
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType

PHASE10_SCENARIO_CATALOG: Dict[str, dict] = {
    "dns_nxdomain_resolution_failure": {
        "title": "Internal Service Discovery DNS Resolution Failure (CoreDNS Partition)",
        "ground_truth_root_cause": "order-service",
        "failure_mechanism": "Socket resolution gaierror: [Errno -2] Name or service not known for payment.internal:8443",
        "is_unfamiliar": True,
        "is_incomplete": False,
        "expected_confidence": "HIGH",
        "expected_symptom_cascade": ["order-service", "web-gateway"],
    },
    "incomplete_telemetry_missing_spans": {
        "title": "Unfamiliar Incident with Incomplete / Dropped Telemetry Spans",
        "ground_truth_root_cause": "billing-worker",
        "failure_mechanism": "Worker crash occurred but network drops resulted in missing intermediate spans",
        "is_unfamiliar": True,
        "is_incomplete": True,
        "expected_confidence": "LOW",
        "expected_symptom_cascade": ["billing-worker", "web-gateway"],
    },
}


def generate_phase10_scenario_telemetry(scenario_id: str) -> List[TelemetryEvent]:
    """Emit raw telemetry events for Phase 10 unfamiliar evaluation scenarios."""
    now = time.time()
    events: List[TelemetryEvent] = []

    if scenario_id == "dns_nxdomain_resolution_failure":
        # 1 single DNS lookup error on order-service
        events.append(TelemetryEvent(
            timestamp=now,
            service="order-service",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="socket.gaierror: [Errno -2] Name or service not known: payment.internal:8443 (CoreDNS partition)",
            trace_id="tr-dns-001",
            span_id="sp-ord-dns",
            parent_span_id="sp-gw-dns-0",
            duration_ms=250.0,
        ))
        # Downstream cascade: web-gateway floods 15 503 Bad Gateway errors
        for i in range(15):
            events.append(TelemetryEvent(
                timestamp=now + 0.02 + (i * 0.01),
                service="web-gateway",
                level=LogLevel.ERROR,
                event_type=EventType.LOG,
                message=f"HTTP 503 Service Unavailable: upstream order processing failed (attempt #{i+1})",
                trace_id=f"tr-dns-gw-{i}",
                span_id=f"sp-gw-dns-{i}",
                status_code=503,
                duration_ms=260.0,
            ))

    elif scenario_id == "incomplete_telemetry_missing_spans":
        # Incomplete spans: Worker has an unlinked critical error with no trace or parent link
        events.append(TelemetryEvent(
            timestamp=now,
            service="billing-worker",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="FatalWorkerError: Segfault in c-extension payment_tokenizer.so (unlinked span, packet dropped)",
            trace_id="tr-orphan-worker",
            span_id="sp-worker-orphan",
            parent_span_id=None,
        ))
        # Gateway has isolated timeouts with no direct connection to the worker
        events.append(TelemetryEvent(
            timestamp=now + 0.05,
            service="web-gateway",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="HTTP 504 Gateway Timeout on async job check",
            trace_id="tr-orphan-gw",
            span_id="sp-gw-orphan",
            parent_span_id=None,
            status_code=504,
        ))

    return events
