"""Failure injection and recovery scenarios for demo service."""
import time
try:
    from ..models.telemetry import TelemetryEvent, LogLevel, EventType
except (ImportError, ValueError):
    try:
        from app.models.telemetry import TelemetryEvent, LogLevel, EventType
    except ImportError:
        from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from .service import DemoAppService

# Ground truth catalog for evaluation and validation
SCENARIO_CATALOG = {
    "db_pool_exhaustion": {
        "scenario_id": "db_pool_exhaustion",
        "title": "Database Connection Pool Saturation",
        "ground_truth_root_cause": "inventory-service",
        "failure_mechanism": "HikariCP pool limit reached (maxPoolSize=10), causing 3000ms query timeouts and 503 cascades.",
        "expected_symptom_cascade": ["inventory-service", "order-service", "web-gateway"],
        "historical_incident_id": "INC-2025-0812",
        "historical_runbook_id": "RUNBOOK-INV-001",
        "category": "infrastructure_saturation",
    },
    "bad_auth_deployment": {
        "scenario_id": "bad_auth_deployment",
        "title": "Faulty Auth Service Release Deployment",
        "ground_truth_root_cause": "auth-service",
        "failure_mechanism": "NullPointerDereference in TokenValidator.verify() following deployment v2.4.1-rc1.",
        "expected_symptom_cascade": ["auth-service", "web-gateway"],
        "historical_incident_id": "INC-2025-1104",
        "historical_runbook_id": "RUNBOOK-AUTH-002",
        "category": "deployment_regression",
    },
    "payment_timeout": {
        "scenario_id": "payment_timeout",
        "title": "Downstream Payment Provider Read Timeout",
        "ground_truth_root_cause": "payment-service",
        "failure_mechanism": "ConnectTimeout on api.stripe-mock.com after 5000ms read timeout, returning HTTP 504.",
        "expected_symptom_cascade": ["payment-service", "order-service", "web-gateway"],
        "historical_incident_id": "INC-2026-0115",
        "historical_runbook_id": None,
        "category": "downstream_timeout",
    },
}

def inject_db_pool_exhaustion(service: DemoAppService, count: int = 3):
    """Scenario 1: Database connection pool exhaustion on inventory-service."""
    service.db_pool_exhausted = True
    for _ in range(count):
        service.execute_checkout_flow()

def inject_bad_auth_deployment(service: DemoAppService, count: int = 3):
    """Scenario 2: Regressed deployment on auth-service causing NullPointer."""
    now = time.time()
    # 1. Emit deployment event
    deploy_event = TelemetryEvent(
        timestamp=now - 5.0,
        service="auth-service",
        level=LogLevel.INFO,
        event_type=EventType.DEPLOYMENT,
        message="Deployed release v2.4.1-rc1 (commit #a8f9c21) to production",
        metadata={"git_commit": "a8f9c21", "author": "dev-ops", "version": "v2.4.1-rc1"}
    )
    service.emit([deploy_event])
    service.bad_auth_deployment = True
    for _ in range(count):
        service.execute_checkout_flow()

def inject_payment_timeout(service: DemoAppService, count: int = 3):
    """Scenario 3: Upstream payment gateway timeout."""
    service.payment_gateway_down = True
    for _ in range(count):
        service.execute_checkout_flow()

def generate_healthy_traffic(service: DemoAppService, count: int = 5):
    """Scenario 4: Normal operation."""
    for _ in range(count):
        service.execute_checkout_flow()

def recover_all(service: DemoAppService):
    """Reset all failure states and emit recovery confirmation."""
    service.db_pool_exhausted = False
    service.bad_auth_deployment = False
    service.payment_gateway_down = False
    recovery_event = TelemetryEvent(
        timestamp=time.time(),
        service="web-gateway",
        level=LogLevel.INFO,
        event_type=EventType.HEALTH,
        message="System fully recovered: all simulated failure toggles disabled",
        metadata={"recovered_services": ["inventory-service", "auth-service", "payment-service"]}
    )
    service.emit([recovery_event])
