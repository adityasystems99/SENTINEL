"""OpenTelemetry (OTLP) Conversion Adapter for SENTINEL.
Converts standard OpenTelemetry OTLP/HTTP JSON trace payloads (POST /v1/traces)
into native SENTINEL TelemetryEvent models.
Preserves existing zero-dependency FastAPI architecture without heavy external collectors.
"""
import time
from typing import Any, Dict, List, Optional
from ..models.telemetry import TelemetryEvent, LogLevel, EventType


def parse_otlp_attribute_value(val: Any) -> Any:
    """Extract primitive Python value from OpenTelemetry attribute value JSON object."""
    if not isinstance(val, dict):
        return val

    if "stringValue" in val:
        return val["stringValue"]
    elif "intValue" in val:
        try:
            return int(val["intValue"])
        except (ValueError, TypeError):
            return val["intValue"]
    elif "doubleValue" in val:
        try:
            return float(val["doubleValue"])
        except (ValueError, TypeError):
            return val["doubleValue"]
    elif "boolValue" in val:
        return bool(val["boolValue"])
    elif "arrayValue" in val:
        vals = val.get("arrayValue", {}).get("values", [])
        return [parse_otlp_attribute_value(v) for v in vals]
    elif "kvlistValue" in val:
        kvs = val.get("kvlistValue", {}).get("values", [])
        return {item.get("key"): parse_otlp_attribute_value(item.get("value")) for item in kvs}
    return str(val)


def convert_otlp_traces_payload(payload: Dict[str, Any]) -> List[TelemetryEvent]:
    """Convert standard OTLP/HTTP trace JSON payload into SENTINEL TelemetryEvents.
    
    Supports:
    1. Standard OTLP hierarchy: resourceSpans -> scopeSpans -> spans
    2. Flat/simplified OpenTelemetry dictionaries (direct span lists)
    """
    events: List[TelemetryEvent] = []
    now = time.time()

    # 1. Standard OTLP payload with resourceSpans
    if "resourceSpans" in payload:
        for r_span in payload.get("resourceSpans", []):
            resource = r_span.get("resource", {})
            raw_attrs = resource.get("attributes", [])
            resource_metadata: Dict[str, Any] = {}
            service_name = "unknown-service"

            for attr in raw_attrs:
                k = attr.get("key")
                v = parse_otlp_attribute_value(attr.get("value"))
                resource_metadata[k] = v
                if k in ("service.name", "service_name"):
                    service_name = str(v)

            for scope_span in r_span.get("scopeSpans", []):
                for span in scope_span.get("spans", []):
                    # Timing
                    start_nano_raw = span.get("startTimeUnixNano")
                    end_nano_raw = span.get("endTimeUnixNano")
                    
                    try:
                        start_nano = int(start_nano_raw) if start_nano_raw else int(now * 1e9)
                        end_nano = int(end_nano_raw) if end_nano_raw else start_nano
                    except (ValueError, TypeError):
                        start_nano = int(now * 1e9)
                        end_nano = start_nano

                    timestamp = start_nano / 1e9
                    duration_ms = max(0.0, round((end_nano - start_nano) / 1e6, 2))

                    # Trace and Span IDs
                    trace_id = span.get("traceId")
                    span_id = span.get("spanId")
                    parent_span_id = span.get("parentSpanId") or None

                    # Extract Span Attributes
                    span_attrs: Dict[str, Any] = {}
                    http_status_code: Optional[int] = None
                    for attr in span.get("attributes", []):
                        k = attr.get("key")
                        v = parse_otlp_attribute_value(attr.get("value"))
                        span_attrs[k] = v
                        if k in ("http.status_code", "http.response.status_code"):
                            try:
                                http_status_code = int(v)
                            except (ValueError, TypeError):
                                pass

                    # Status classification
                    # OpenTelemetry Status Code: 0 = UNSET, 1 = OK, 2 = ERROR
                    span_status = span.get("status", {})
                    status_code_raw = span_status.get("code")
                    is_error = False
                    if status_code_raw == 2 or (http_status_code and http_status_code >= 400):
                        is_error = True

                    # Message extraction
                    span_name = span.get("name", "span")
                    status_desc = span_status.get("message")
                    exception_message = None

                    # Check span events for exceptions
                    for ev in span.get("events", []):
                        ev_name = ev.get("name", "")
                        ev_attrs = {a.get("key"): parse_otlp_attribute_value(a.get("value")) for a in ev.get("attributes", [])}
                        if ev_name == "exception" or "exception.message" in ev_attrs:
                            is_error = True
                            exception_message = ev_attrs.get("exception.message") or ev_attrs.get("exception.type")

                    if exception_message:
                        message = f"{span_name}: {exception_message}"
                    elif status_desc:
                        message = f"{span_name}: {status_desc}"
                    elif http_status_code:
                        message = f"{span_name} HTTP {http_status_code}"
                    else:
                        message = f"{span_name} executed"

                    # Log Level
                    if is_error:
                        if (http_status_code and http_status_code >= 500) or exception_message:
                            level = LogLevel.CRITICAL
                        else:
                            level = LogLevel.ERROR
                    else:
                        level = LogLevel.INFO

                    metadata = {
                        "otlp_instrumentation_scope": scope_span.get("scope", {}).get("name"),
                        "span_kind": span.get("kind"),
                        "resource_attributes": resource_metadata,
                        "span_attributes": span_attrs,
                    }
                    if "links" in span and span["links"]:
                        metadata["otlp_links"] = span["links"]

                    events.append(TelemetryEvent(
                        timestamp=timestamp,
                        service=service_name,
                        level=level,
                        event_type=EventType.TRACE,
                        message=message,
                        trace_id=trace_id,
                        span_id=span_id,
                        parent_span_id=parent_span_id,
                        status_code=http_status_code,
                        duration_ms=duration_ms,
                        metadata=metadata,
                    ))

    # 2. Simplified flat span list
    elif "spans" in payload:
        for span in payload.get("spans", []):
            service = span.get("service_name") or span.get("service") or "unknown-service"
            trace_id = span.get("trace_id") or span.get("traceId")
            span_id = span.get("span_id") or span.get("spanId")
            parent_span_id = span.get("parent_span_id") or span.get("parentSpanId")
            status_code = span.get("status_code") or span.get("http_status")
            duration_ms = span.get("duration_ms", 0.0)
            is_error = span.get("is_error", False) or (status_code and status_code >= 400)
            
            level = LogLevel.ERROR if is_error else LogLevel.INFO
            events.append(TelemetryEvent(
                timestamp=span.get("timestamp", now),
                service=service,
                level=level,
                event_type=EventType.TRACE,
                message=span.get("message") or span.get("name") or "External span",
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                status_code=status_code,
                duration_ms=duration_ms,
                metadata=span.get("attributes", {})
            ))

    return events
