"""Failure injection and recovery scenarios for demo service."""
import time
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from .service import DemoAppService

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
