"""Expanded Phase 9 Evaluation Dataset & Scenario Catalog.
Separates development fixtures from held-out evaluation variations.
Strictly isolates ground-truth labels from telemetry inputs.
"""
import time
import uuid
from typing import Dict, List, Tuple
try:
    from app.models.telemetry import TelemetryEvent, LogLevel, EventType
except ImportError:
    from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType

# Ground-truth evaluation catalog (kept isolated so ranker cannot inspect answers)
PHASE9_EVALUATION_DATASET: Dict[str, dict] = {
    # -------------------------------------------------------------------------
    # Development Fixtures
    # -------------------------------------------------------------------------
    "db_pool_exhaustion_saturation": {
        "title": "Database Connection Pool Saturation (HikariCP maxPoolSize=10)",
        "ground_truth_root_cause": "inventory-service",
        "held_out": False,
        "is_inconclusive": False,
        "expected_confidence": "HIGH",
        "historical_incident_id": "INC-2025-0812",
        "historical_runbook_id": "RUNBOOK-INV-001",
        "description": "Inventory DB pool limit reached; query timeouts trigger cascading 503 errors to gateway.",
    },
    "downstream_timeout_gateway_cutoff": {
        "title": "Downstream Gateway Cutoff Timeout (Stripe 5000ms freeze)",
        "ground_truth_root_cause": "payment-service",
        "held_out": False,
        "is_inconclusive": False,
        "expected_confidence": "HIGH",
        "historical_incident_id": "INC-2026-0115",
        "historical_runbook_id": None,
        "description": "Payment service blocks on Stripe read socket; upstream gateway hits 2000ms timeout cutoff.",
    },
    "bad_auth_deployment_nullpointer": {
        "title": "Faulty Auth Service Release Deployment (v2.4.1-rc1)",
        "ground_truth_root_cause": "auth-service",
        "held_out": False,
        "is_inconclusive": False,
        "expected_confidence": "HIGH",
        "historical_incident_id": "INC-2025-1104",
        "historical_runbook_id": "RUNBOOK-AUTH-002",
        "description": "Production deploy event precedes immediate NullPointerDereference exceptions in TokenValidator.",
    },
    "misleading_gateway_flood": {
        "title": "Downstream Symptom Flood vs Single Upstream Trigger",
        "ground_truth_root_cause": "order-service",
        "held_out": False,
        "is_inconclusive": False,
        "expected_confidence": "HIGH",
        "historical_incident_id": None,
        "historical_runbook_id": None,
        "description": "Order service encounters single DB deadlock; noisy gateway floods 20 consecutive HTTP 502 errors.",
    },

    # -------------------------------------------------------------------------
    # Held-Out Evaluation Cases (Never used during algorithm tuning)
    # -------------------------------------------------------------------------
    "db_pool_leak_unreleased": {
        "title": "Database Connection Leak via Unclosed Transaction",
        "ground_truth_root_cause": "order-service",
        "held_out": True,
        "is_inconclusive": False,
        "expected_confidence": "HIGH",
        "historical_incident_id": None,
        "historical_runbook_id": None,
        "description": "Order service acquires PostgreSQL connection but fails to release connection in exception handler.",
    },
    "downstream_timeout_intermittent_3rdparty": {
        "title": "Intermittent Socket Timeout on External Payment Provider",
        "ground_truth_root_cause": "payment-service",
        "held_out": True,
        "is_inconclusive": False,
        "expected_confidence": "HIGH",
        "historical_incident_id": "INC-2026-0115",
        "historical_runbook_id": None,
        "description": "External payment gateway socket drops intermittently; payment service returns 504 to order-service.",
    },
    "config_drift_bad_port": {
        "title": "Configuration Drift (Invalid DB Port 5433 after config push)",
        "ground_truth_root_cause": "inventory-service",
        "held_out": True,
        "is_inconclusive": False,
        "expected_confidence": "HIGH",
        "historical_incident_id": None,
        "historical_runbook_id": "RUNBOOK-INV-001",
        "description": "Configuration deployment pushes wrong database port, causing immediate connection refused on inventory-service.",
    },
    "inconclusive_disconnected_signals": {
        "title": "Ambiguous Incident with Insufficient Evidence & Disconnected Logs",
        "ground_truth_root_cause": None,  # Ground truth is genuinely ambiguous
        "held_out": True,
        "is_inconclusive": True,
        "expected_confidence": "LOW",
        "historical_incident_id": None,
        "historical_runbook_id": None,
        "description": "Disconnected error logs from auth and inventory without trace links, parent spans, or temporal ordering.",
    },
}


def generate_scenario_telemetry(scenario_id: str) -> List[TelemetryEvent]:
    """Generates synthetic/emitted telemetry events for each scenario.
    The output contains ONLY raw TelemetryEvent objects without ground truth metadata.
    """
    now = time.time()
    events: List[TelemetryEvent] = []

    if scenario_id == "db_pool_exhaustion_saturation":
        # Inventory DB saturation with gateway cascade
        for i in range(3):
            tr = f"tr-sat-{i}"
            sp_gw = f"sp-gw-{i}"
            sp_ord = f"sp-ord-{i}"
            sp_inv = f"sp-inv-{i}"
            events.extend([
                TelemetryEvent(
                    timestamp=now + (i * 0.1),
                    service="web-gateway",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="POST /checkout received",
                    trace_id=tr,
                    span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.02,
                    service="order-service",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="Creating order reservation",
                    trace_id=tr,
                    span_id=sp_ord,
                    parent_span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.05,
                    service="inventory-service",
                    level=LogLevel.CRITICAL,
                    event_type=EventType.LOG,
                    message="HikariPool-1 - Connection is not available, request timed out after 3000ms (maxPoolSize=10)",
                    trace_id=tr,
                    span_id=sp_inv,
                    parent_span_id=sp_ord,
                    status_code=503,
                    duration_ms=3000.0,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 3.06,
                    service="order-service",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message="Order creation failed: inventory-service returned 503",
                    trace_id=tr,
                    span_id=sp_ord,
                    parent_span_id=sp_gw,
                    status_code=503,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 3.07,
                    service="web-gateway",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message="HTTP 502 Bad Gateway while completing checkout",
                    trace_id=tr,
                    span_id=sp_gw,
                    status_code=502,
                )
            ])

    elif scenario_id == "downstream_timeout_gateway_cutoff":
        for i in range(3):
            tr = f"tr-timeout-{i}"
            sp_gw = f"sp-gw-{i}"
            sp_ord = f"sp-ord-{i}"
            sp_pay = f"sp-pay-{i}"
            events.extend([
                TelemetryEvent(
                    timestamp=now + (i * 0.1),
                    service="web-gateway",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="POST /checkout received",
                    trace_id=tr,
                    span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.02,
                    service="order-service",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="Dispatching payment authorization",
                    trace_id=tr,
                    span_id=sp_ord,
                    parent_span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.05,
                    service="payment-service",
                    level=LogLevel.CRITICAL,
                    event_type=EventType.LOG,
                    message="ConnectTimeout HTTPSConnectionPool(host='api.stripe-mock.com'): Read timed out after 5000ms",
                    trace_id=tr,
                    span_id=sp_pay,
                    parent_span_id=sp_ord,
                    status_code=504,
                    duration_ms=5000.0,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 2.05,
                    service="web-gateway",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message="HTTP 504 Gateway Timeout: client timeout threshold exceeded",
                    trace_id=tr,
                    span_id=sp_gw,
                    status_code=504,
                )
            ])

    elif scenario_id == "bad_auth_deployment_nullpointer":
        # 1. Deployment event precedes failure
        events.append(TelemetryEvent(
            timestamp=now - 5.0,
            service="auth-service",
            level=LogLevel.INFO,
            event_type=EventType.DEPLOYMENT,
            message="Deployed release v2.4.1-rc1 (commit #a8f9c21) to production",
            metadata={"version": "v2.4.1-rc1"}
        ))
        for i in range(3):
            tr = f"tr-auth-{i}"
            sp_gw = f"sp-gw-{i}"
            sp_auth = f"sp-auth-{i}"
            events.extend([
                TelemetryEvent(
                    timestamp=now + (i * 0.05),
                    service="web-gateway",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="POST /checkout received",
                    trace_id=tr,
                    span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.05) + 0.01,
                    service="auth-service",
                    level=LogLevel.CRITICAL,
                    event_type=EventType.LOG,
                    message="NullPointerDereference in TokenValidator.verify(): user_session is None",
                    trace_id=tr,
                    span_id=sp_auth,
                    parent_span_id=sp_gw,
                    status_code=500,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.05) + 0.02,
                    service="web-gateway",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message="HTTP 500 Internal Server Error: auth validation failed",
                    trace_id=tr,
                    span_id=sp_gw,
                    status_code=500,
                )
            ])

    elif scenario_id == "misleading_gateway_flood":
        # 1 single deadlock on order-service
        events.append(TelemetryEvent(
            timestamp=now,
            service="order-service",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="Deadlock detected while waiting for lock on relation orders_pkey",
            trace_id="tr-flood-0",
            span_id="sp-ord-0",
            parent_span_id="sp-gw-0",
        ))
        # 20 downstream error events from web-gateway
        for i in range(20):
            events.append(TelemetryEvent(
                timestamp=now + 0.02 + (i * 0.01),
                service="web-gateway",
                level=LogLevel.ERROR,
                event_type=EventType.LOG,
                message=f"HTTP 502 Bad Gateway: downstream order-service connection failure #{i}",
                trace_id=f"tr-flood-{i}",
                span_id=f"sp-gw-{i}",
                status_code=502,
            ))

    elif scenario_id == "db_pool_leak_unreleased":
        # Held-out variation: order-service connection leak
        for i in range(3):
            tr = f"tr-leak-{i}"
            sp_gw = f"sp-gw-{i}"
            sp_ord = f"sp-ord-{i}"
            events.extend([
                TelemetryEvent(
                    timestamp=now + (i * 0.1),
                    service="web-gateway",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="POST /orders/checkout",
                    trace_id=tr,
                    span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.02,
                    service="order-service",
                    level=LogLevel.CRITICAL,
                    event_type=EventType.LOG,
                    message="ConnectionPoolTimeoutException: Timeout waiting for idle object in pool [maxTotal=8, active=8]",
                    trace_id=tr,
                    span_id=sp_ord,
                    parent_span_id=sp_gw,
                    status_code=500,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.04,
                    service="web-gateway",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message="HTTP 500 Internal Server Error from order-service",
                    trace_id=tr,
                    span_id=sp_gw,
                    status_code=500,
                )
            ])

    elif scenario_id == "downstream_timeout_intermittent_3rdparty":
        # Held-out variation: payment-service socket drops
        for i in range(3):
            tr = f"tr-drop-{i}"
            sp_gw = f"sp-gw-{i}"
            sp_pay = f"sp-pay-{i}"
            events.extend([
                TelemetryEvent(
                    timestamp=now + (i * 0.1),
                    service="web-gateway",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="POST /checkout/pay",
                    trace_id=tr,
                    span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.05,
                    service="payment-service",
                    level=LogLevel.CRITICAL,
                    event_type=EventType.LOG,
                    message="SocketTimeoutException: SSL handshake timeout communicating with payment acquirer",
                    trace_id=tr,
                    span_id=sp_pay,
                    parent_span_id=sp_gw,
                    status_code=504,
                    duration_ms=4800.0,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.10,
                    service="web-gateway",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message="HTTP 504 Gateway Timeout returned to user",
                    trace_id=tr,
                    span_id=sp_gw,
                    status_code=504,
                )
            ])

    elif scenario_id == "config_drift_bad_port":
        # Held-out variation: configuration event + connection refused
        events.append(TelemetryEvent(
            timestamp=now - 2.0,
            service="inventory-service",
            level=LogLevel.INFO,
            event_type=EventType.DEPLOYMENT,
            message="ConfigMap update applied: DB_HOST=db.internal.net, DB_PORT=5433",
            metadata={"config_version": "v1.0.4"}
        ))
        for i in range(3):
            tr = f"tr-cfg-{i}"
            sp_gw = f"sp-gw-{i}"
            sp_inv = f"sp-inv-{i}"
            events.extend([
                TelemetryEvent(
                    timestamp=now + (i * 0.1),
                    service="web-gateway",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="POST /inventory/reserve",
                    trace_id=tr,
                    span_id=sp_gw,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.01,
                    service="inventory-service",
                    level=LogLevel.CRITICAL,
                    event_type=EventType.LOG,
                    message="PSQLException: Connection to db.internal.net:5433 refused. Check that hostname and port are correct",
                    trace_id=tr,
                    span_id=sp_inv,
                    parent_span_id=sp_gw,
                    status_code=503,
                ),
                TelemetryEvent(
                    timestamp=now + (i * 0.1) + 0.02,
                    service="web-gateway",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message="HTTP 502 Bad Gateway: downstream inventory connection refused",
                    trace_id=tr,
                    span_id=sp_gw,
                    status_code=502,
                )
            ])

    elif scenario_id == "inconclusive_disconnected_signals":
        # Disconnected events without traces, without parent spans, without deployment markers
        events.extend([
            TelemetryEvent(
                timestamp=now + 0.01,
                service="auth-service",
                level=LogLevel.ERROR,
                event_type=EventType.LOG,
                message="Unknown transient warning: session check took longer than normal",
                trace_id="tr-orphan-1",
                span_id="sp-auth-orphan-1",
            ),
            TelemetryEvent(
                timestamp=now + 0.02,
                service="inventory-service",
                level=LogLevel.ERROR,
                event_type=EventType.LOG,
                message="Unknown transient warning: inventory cache miss spike",
                trace_id="tr-orphan-2",
                span_id="sp-inv-orphan-1",
            ),
        ])

    return events
