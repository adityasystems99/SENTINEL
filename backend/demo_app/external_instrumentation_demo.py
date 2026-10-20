"""Reproducible External Telemetry Integration Example for SENTINEL (Phase 10).
Demonstrates an independent third-party service emitting OpenTelemetry-compliant OTLP/HTTP traces
directly into SENTINEL's ingestion receiver at POST /api/telemetry/otlp/v1/traces.
"""
import sys
import time
import uuid
import httpx


def generate_otlp_trace_payload(
    service_name: str = "checkout-frontend",
    endpoint: str = "/api/pay",
    status_code: int = 500,
    error_message: str = "Downstream payment gateway unreachable: DNS NXDOMAIN"
) -> dict:
    """Generate a standard W3C/OTLP JSON trace payload."""
    trace_id = uuid.uuid4().hex
    gw_span_id = uuid.uuid4().hex[:16]
    child_span_id = uuid.uuid4().hex[:16]
    start_time_ns = int(time.time() * 1e9)
    end_time_ns = start_time_ns + int(145 * 1e6)  # 145 ms duration

    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                        {"key": "deployment.environment", "value": {"stringValue": "production"}},
                        {"key": "host.name", "value": {"stringValue": "node-worker-04"}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "io.opentelemetry.demo"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": gw_span_id,
                                "name": f"HTTP POST {endpoint}",
                                "kind": 1,
                                "startTimeUnixNano": str(start_time_ns),
                                "endTimeUnixNano": str(end_time_ns),
                                "attributes": [
                                    {"key": "http.method", "value": {"stringValue": "POST"}},
                                    {"key": "http.status_code", "value": {"intValue": status_code}},
                                ],
                                "status": {"code": 2 if status_code >= 400 else 1},
                            },
                            {
                                "traceId": trace_id,
                                "spanId": child_span_id,
                                "parentSpanId": gw_span_id,
                                "name": "DNS Query payment.internal.svc",
                                "kind": 3,
                                "startTimeUnixNano": str(start_time_ns + int(10 * 1e6)),
                                "endTimeUnixNano": str(end_time_ns - int(5 * 1e6)),
                                "attributes": [
                                    {"key": "dns.question.name", "value": {"stringValue": "payment.internal.svc"}},
                                ],
                                "events": [
                                    {
                                        "timeUnixNano": str(end_time_ns - int(10 * 1e6)),
                                        "name": "exception",
                                        "attributes": [
                                            {"key": "exception.type", "value": {"stringValue": "gaierror"}},
                                            {"key": "exception.message", "value": {"stringValue": error_message}},
                                        ],
                                    }
                                ],
                                "status": {"code": 2, "message": error_message},
                            },
                        ],
                    }
                ],
            }
        ]
    }
    return payload


def send_otlp_telemetry(base_url: str = "http://127.0.0.1:8000"):
    """Send OTLP trace payload to SENTINEL."""
    target_url = f"{base_url}/api/telemetry/otlp/v1/traces"
    payload = generate_otlp_trace_payload()
    print(f"Emitting OpenTelemetry OTLP trace to: {target_url}...")
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(target_url, json=payload)
        print(f"Response [{resp.status_code}]: {resp.json()}")
        return resp.json()
    except Exception as e:
        print(f"Failed to connect to {target_url}: {e}")
        return None


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    send_otlp_telemetry(url)
