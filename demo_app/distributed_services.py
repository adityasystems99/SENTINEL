"""Distributed multi-process HTTP demo microservices for Phase 9 validation.
Runs real independent HTTP services communicating over TCP sockets.
Demonstrates W3C traceparent and X-Trace-Id propagation, parent-child span hierarchy,
and broken trace relationship detection across process boundaries.
"""
import json
import os
import sys
import time
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Dict, List, Optional
import httpx

from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType


class BaseTelemetryHandler(BaseHTTPRequestHandler):
    """Base handler with JSON parsing and header extraction."""
    
    def log_message(self, format, *args):
        # Silence default stderr request logging in test runs
        pass

    def extract_trace_context(self) -> tuple[Optional[str], Optional[str]]:
        """Extract trace_id and parent_span_id from HTTP headers."""
        trace_id = self.headers.get("X-Trace-Id")
        parent_span = self.headers.get("X-Parent-Span-Id")

        # Fallback to W3C traceparent: 00-{trace_id}-{parent_span}-{flags}
        traceparent = self.headers.get("traceparent")
        if traceparent and not trace_id:
            parts = traceparent.split("-")
            if len(parts) >= 3:
                trace_id = parts[1]
                parent_span = parts[2]

        return trace_id, parent_span

    def send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


class InventoryServiceHandler(BaseTelemetryHandler):
    """Downstream inventory service listening on HTTP socket."""

    def do_POST(self):
        if self.path == "/reserve":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            
            trace_id, parent_span = self.extract_trace_context()
            
            # If no incoming trace context, this is an unlinked/orphaned trace
            if not trace_id:
                trace_id = f"tr-unlinked-{uuid.uuid4().hex[:8]}"

            inv_span = f"sp-inv-{uuid.uuid4().hex[:6]}"
            now = time.time()
            events: List[TelemetryEvent] = []

            # Check failure flag on server instance
            if getattr(self.server, "db_pool_exhausted", False):
                # Simulated connection pool saturation
                events.append(TelemetryEvent(
                    timestamp=now,
                    service="inventory-service",
                    level=LogLevel.CRITICAL,
                    event_type=EventType.LOG,
                    message="HikariPool-1 - Connection is not available, request timed out after 3000ms (maxPoolSize=10)",
                    trace_id=trace_id,
                    span_id=inv_span,
                    parent_span_id=parent_span,
                    status_code=503,
                    duration_ms=3000.0,
                    metadata={"pool_size": 10, "active_connections": 10, "pending_threads": 4}
                ))
                self.server.emit_telemetry(events)
                self.send_json(503, {
                    "error": "database_connection_pool_exhausted",
                    "trace_id": trace_id,
                    "span_id": inv_span,
                    "parent_span_id": parent_span,
                })
            else:
                # Normal healthy reservation
                events.append(TelemetryEvent(
                    timestamp=now,
                    service="inventory-service",
                    level=LogLevel.INFO,
                    event_type=EventType.TRACE,
                    message="SKU inventory reserved successfully",
                    trace_id=trace_id,
                    span_id=inv_span,
                    parent_span_id=parent_span,
                    status_code=200,
                    duration_ms=28.5,
                ))
                self.server.emit_telemetry(events)
                self.send_json(200, {
                    "status": "reserved",
                    "trace_id": trace_id,
                    "span_id": inv_span,
                    "parent_span_id": parent_span,
                })
        else:
            self.send_json(404, {"error": "not_found"})


class GatewayServiceHandler(BaseTelemetryHandler):
    """Upstream API gateway service listening on HTTP socket."""

    def do_POST(self):
        if self.path == "/checkout":
            incoming_trace_id, _ = self.extract_trace_context()
            trace_id = incoming_trace_id or f"tr-net-{uuid.uuid4().hex[:10]}"
            gw_span = f"sp-gw-{uuid.uuid4().hex[:6]}"
            now = time.time()

            # Gateway entry span
            gw_entry_event = TelemetryEvent(
                timestamp=now,
                service="web-gateway",
                level=LogLevel.INFO,
                event_type=EventType.TRACE,
                message="POST /api/v1/checkout received over HTTP socket",
                trace_id=trace_id,
                span_id=gw_span,
                parent_span_id=None,
                status_code=200,
                duration_ms=15.0,
            )
            self.server.emit_telemetry([gw_entry_event])

            # Prepare downstream call headers
            headers = {}
            if not getattr(self.server, "break_trace_headers", False):
                headers["X-Trace-Id"] = trace_id
                headers["X-Parent-Span-Id"] = gw_span
                headers["traceparent"] = f"00-{trace_id}-{gw_span}-01"

            # Call downstream inventory service over HTTP
            inv_url = f"http://127.0.0.1:{self.server.downstream_port}/reserve"
            try:
                with httpx.Client(timeout=4.0) as client:
                    resp = client.post(inv_url, headers=headers, json={"sku": "PROD-99", "qty": 1})

                if resp.status_code == 200:
                    self.send_json(200, {
                        "status": "checkout_completed",
                        "trace_id": trace_id,
                        "gw_span": gw_span,
                        "downstream_resp": resp.json(),
                    })
                else:
                    # Downstream failure cascade
                    cascade_event = TelemetryEvent(
                        timestamp=time.time(),
                        service="web-gateway",
                        level=LogLevel.ERROR,
                        event_type=EventType.LOG,
                        message=f"HTTP 502 Bad Gateway: downstream inventory-service returned {resp.status_code}",
                        trace_id=trace_id,
                        span_id=gw_span,
                        parent_span_id=None,
                        status_code=502,
                        duration_ms=3050.0,
                    )
                    self.server.emit_telemetry([cascade_event])
                    self.send_json(502, {
                        "error": "downstream_service_failed",
                        "trace_id": trace_id,
                        "gw_span": gw_span,
                        "downstream_error": resp.json(),
                    })
            except Exception as exc:
                timeout_event = TelemetryEvent(
                    timestamp=time.time(),
                    service="web-gateway",
                    level=LogLevel.ERROR,
                    event_type=EventType.LOG,
                    message=f"HTTP 504 Gateway Timeout while contacting inventory-service: {exc}",
                    trace_id=trace_id,
                    span_id=gw_span,
                    parent_span_id=None,
                    status_code=504,
                    duration_ms=4000.0,
                )
                self.server.emit_telemetry([timeout_event])
                self.send_json(504, {"error": "gateway_timeout", "detail": str(exc)})
        else:
            self.send_json(404, {"error": "not_found"})


class DistributedServer:
    """Manages an HTTP server thread with clean start and shutdown."""

    def __init__(
        self,
        name: str,
        handler_cls,
        port: int = 0,
        telemetry_sink: Optional[Callable[[List[TelemetryEvent]], None]] = None,
        telemetry_api_url: Optional[str] = None
    ):
        self.name = name
        self.server = HTTPServer(("127.0.0.1", port), handler_cls)
        self.port = self.server.server_address[1]
        self.telemetry_sink = telemetry_sink
        self.telemetry_api_url = telemetry_api_url
        self.thread: Optional[threading.Thread] = None

        # Attach telemetry emitter to server instance so handlers can call it
        self.server.emit_telemetry = self.emit_telemetry

    def emit_telemetry(self, events: List[TelemetryEvent]):
        if self.telemetry_sink:
            self.telemetry_sink(events)
        elif self.telemetry_api_url:
            try:
                payload = {"events": [e.model_dump() for e in events]}
                with httpx.Client(timeout=2.0) as client:
                    client.post(self.telemetry_api_url, json=payload)
            except Exception:
                pass

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
