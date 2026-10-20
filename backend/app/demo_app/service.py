"""Instrumented multi-tier demo application.
Simulates realistic distributed service calls (gateway, auth, order, inventory, payment).
Emits telemetry events into SENTINEL.
"""
import time
import uuid
from typing import Callable, List, Optional
try:
    from ..models.telemetry import TelemetryEvent, LogLevel, EventType
except (ImportError, ValueError):
    try:
        from app.models.telemetry import TelemetryEvent, LogLevel, EventType
    except ImportError:
        from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType

class DemoAppService:
    def __init__(self, telemetry_sink: Optional[Callable[[List[TelemetryEvent]], None]] = None):
        self.telemetry_sink = telemetry_sink
        # Failure toggle flags
        self.db_pool_exhausted: bool = False
        self.bad_auth_deployment: bool = False
        self.payment_gateway_down: bool = False

    def emit(self, events: List[TelemetryEvent]):
        if self.telemetry_sink:
            self.telemetry_sink(events)

    def execute_checkout_flow(self, user_id: str = "user-101", amount: float = 89.99) -> dict:
        """Simulate a complete checkout request across microservices."""
        trace_id = f"tr-{uuid.uuid4().hex[:12]}"
        events: List[TelemetryEvent] = []
        now = time.time()

        # 1. Web Gateway receives request
        gw_span = f"sp-gw-{uuid.uuid4().hex[:6]}"
        events.append(TelemetryEvent(
            timestamp=now,
            service="web-gateway",
            level=LogLevel.INFO,
            event_type=EventType.TRACE,
            message="POST /api/v1/checkout received",
            trace_id=trace_id,
            span_id=gw_span,
            status_code=200,
            duration_ms=185.0,
        ))

        # 2. Auth Service verification
        auth_span = f"sp-auth-{uuid.uuid4().hex[:6]}"
        if self.bad_auth_deployment:
            # Bad deployment scenario: Auth service throws NullPointer / AttributeError
            events.append(TelemetryEvent(
                timestamp=now + 0.05,
                service="auth-service",
                level=LogLevel.CRITICAL,
                event_type=EventType.LOG,
                message="NullPointerDereference in TokenValidator.verify(): user_session is None",
                trace_id=trace_id,
                span_id=auth_span,
                parent_span_id=gw_span,
                status_code=500,
                duration_ms=11.2,
                metadata={"exception": "AttributeError", "module": "auth.validator", "line": 42}
            ))
            events.append(TelemetryEvent(
                timestamp=now + 0.08,
                service="web-gateway",
                level=LogLevel.ERROR,
                event_type=EventType.TRACE,
                message="Auth check failed: Upstream 500 from auth-service",
                trace_id=trace_id,
                span_id=gw_span,
                status_code=500,
                duration_ms=85.0,
            ))
            self.emit(events)
            return {"success": False, "error": "Auth service failure", "trace_id": trace_id}

        events.append(TelemetryEvent(
            timestamp=now + 0.02,
            service="auth-service",
            level=LogLevel.INFO,
            event_type=EventType.TRACE,
            message=f"Session verified for user {user_id}",
            trace_id=trace_id,
            span_id=auth_span,
            parent_span_id=gw_span,
            status_code=200,
            duration_ms=22.5,
        ))

        # 3. Order Service creation
        order_span = f"sp-order-{uuid.uuid4().hex[:6]}"
        events.append(TelemetryEvent(
            timestamp=now + 0.04,
            service="order-service",
            level=LogLevel.INFO,
            event_type=EventType.TRACE,
            message=f"Creating order for user {user_id}",
            trace_id=trace_id,
            span_id=order_span,
            parent_span_id=gw_span,
            duration_ms=145.0,
        ))

        # 4. Inventory Service reservation
        inv_span = f"sp-inv-{uuid.uuid4().hex[:6]}"
        if self.db_pool_exhausted:
            # DB exhaustion scenario: inventory query times out
            events.append(TelemetryEvent(
                timestamp=now + 0.10,
                service="inventory-service",
                level=LogLevel.CRITICAL,
                event_type=EventType.LOG,
                message="HikariPool-1 - Connection is not available, request timed out after 3000ms (maxPoolSize=10)",
                trace_id=trace_id,
                span_id=inv_span,
                parent_span_id=order_span,
                status_code=503,
                duration_ms=3002.5,
                metadata={"pool": "inventory_db", "active_connections": 10, "idle": 0}
            ))
            events.append(TelemetryEvent(
                timestamp=now + 0.15,
                service="order-service",
                level=LogLevel.ERROR,
                event_type=EventType.TRACE,
                message="Inventory reservation failed: 503 Service Unavailable from inventory-service",
                trace_id=trace_id,
                span_id=order_span,
                parent_span_id=gw_span,
                status_code=500,
                duration_ms=3080.0,
            ))
            events.append(TelemetryEvent(
                timestamp=now + 0.18,
                service="web-gateway",
                level=LogLevel.ERROR,
                event_type=EventType.TRACE,
                message="HTTP 500: Order creation cascade failure",
                trace_id=trace_id,
                span_id=gw_span,
                status_code=500,
                duration_ms=3180.0,
            ))
            self.emit(events)
            return {"success": False, "error": "Inventory DB pool exhausted", "trace_id": trace_id}

        events.append(TelemetryEvent(
            timestamp=now + 0.06,
            service="inventory-service",
            level=LogLevel.INFO,
            event_type=EventType.TRACE,
            message="Inventory reserved successfully for SKU-8842",
            trace_id=trace_id,
            span_id=inv_span,
            parent_span_id=order_span,
            status_code=200,
            duration_ms=28.0,
        ))

        # 5. Payment Service processing
        pay_span = f"sp-pay-{uuid.uuid4().hex[:6]}"
        if self.payment_gateway_down:
            events.append(TelemetryEvent(
                timestamp=now + 0.20,
                service="payment-service",
                level=LogLevel.ERROR,
                event_type=EventType.LOG,
                message="ConnectTimeout: HTTPSConnectionPool(host='api.stripe-mock.com'): Read timed out (timeout=5.0)",
                trace_id=trace_id,
                span_id=pay_span,
                parent_span_id=order_span,
                status_code=504,
                duration_ms=5001.0,
            ))
            events.append(TelemetryEvent(
                timestamp=now + 0.25,
                service="order-service",
                level=LogLevel.ERROR,
                event_type=EventType.TRACE,
                message="Payment capture timed out",
                trace_id=trace_id,
                span_id=order_span,
                parent_span_id=gw_span,
                status_code=504,
                duration_ms=5110.0,
            ))
            events.append(TelemetryEvent(
                timestamp=now + 0.28,
                service="web-gateway",
                level=LogLevel.ERROR,
                event_type=EventType.TRACE,
                message="HTTP 504: Gateway Timeout downstream",
                trace_id=trace_id,
                span_id=gw_span,
                status_code=504,
                duration_ms=5220.0,
            ))
            self.emit(events)
            return {"success": False, "error": "Payment gateway timeout", "trace_id": trace_id}

        events.append(TelemetryEvent(
            timestamp=now + 0.12,
            service="payment-service",
            level=LogLevel.INFO,
            event_type=EventType.TRACE,
            message=f"Charge of ${amount} captured successfully",
            trace_id=trace_id,
            span_id=pay_span,
            parent_span_id=order_span,
            status_code=200,
            duration_ms=95.0,
        ))

        events.append(TelemetryEvent(
            timestamp=now + 0.15,
            service="web-gateway",
            level=LogLevel.INFO,
            event_type=EventType.TRACE,
            message="HTTP 200: Checkout completed successfully",
            trace_id=trace_id,
            span_id=gw_span,
            status_code=200,
            duration_ms=185.0,
        ))

        self.emit(events)
        return {"success": True, "trace_id": trace_id}
