"""End-to-end API tests for SENTINEL backend."""
import time

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "total_events_stored" in data

def test_telemetry_ingest_and_query_flow(client):
    now = time.time()
    payload = {
        "events": [
            {
                "event_id": "ev-10",
                "timestamp": now,
                "service": "billing",
                "level": "INFO",
                "event_type": "log",
                "message": "Invoice generated"
            },
            {
                "event_id": "ev-11",
                "timestamp": now + 0.5,
                "service": "billing",
                "level": "ERROR",
                "event_type": "log",
                "message": "Payment gateway unreachable"
            }
        ]
    }
    # Ingest batch
    res = client.post("/api/telemetry/ingest", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["accepted"] == 2
    assert res_data["deduplicated"] == 0

    # Query events
    query_res = client.get("/api/telemetry/events?service=billing")
    assert query_res.status_code == 200
    events = query_res.json()
    assert len(events) == 2

def test_incident_analysis_e2e_flow(client):
    now = time.time()
    events = [
        {
            "event_id": "root-err",
            "timestamp": now - 10.0,
            "service": "redis-cache",
            "level": "CRITICAL",
            "event_type": "log",
            "message": "OOM Command killed: maxmemory reached",
            "trace_id": "tr-cascade-1",
            "span_id": "sp-redis"
        },
        {
            "event_id": "downstream-err",
            "timestamp": now - 8.0,
            "service": "user-service",
            "level": "ERROR",
            "event_type": "log",
            "message": "Cache miss fallback timed out",
            "trace_id": "tr-cascade-1",
            "span_id": "sp-user",
            "parent_span_id": "sp-redis"
        }
    ]
    # Ingest events
    client.post("/api/telemetry/ingest", json={"events": events})

    # Trigger incident analysis
    analyze_res = client.post("/api/incidents/analyze", json={"window_seconds": 60.0})
    assert analyze_res.status_code == 200
    incident = analyze_res.json()
    assert incident["status"] == "active"
    assert len(incident["nodes"]) == 2
    assert len(incident["root_cause_ranking"]) >= 1
    # Check top suspect is the redis OOM error
    assert incident["root_cause_ranking"][0]["service"] == "redis-cache"

    # List incidents
    list_res = client.get("/api/incidents")
    assert list_res.status_code == 200
    summaries = list_res.json()
    assert len(summaries) >= 1
    assert summaries[0]["incident_id"] == incident["incident_id"]

    # Get single incident by ID
    get_res = client.get(f"/api/incidents/{incident['incident_id']}")
    assert get_res.status_code == 200
    assert get_res.json()["incident_id"] == incident["incident_id"]

def test_demo_scenario_injection(client):
    res = client.post("/api/demo/scenario/db_pool_exhaustion?count=2")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "injected"

    # Verify telemetry was recorded in store
    events_res = client.get("/api/telemetry/events?level=CRITICAL")
    assert events_res.status_code == 200
    assert len(events_res.json()) >= 1
