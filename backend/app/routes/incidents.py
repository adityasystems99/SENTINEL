"""Incident investigation and graph analysis routes."""
import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.incident import IncidentReport, IncidentSummary
from ..graph.builder import build_incident_graph
from ..graph.ranker import rank_root_causes
from ..storage.memory_store import store
from ..services.rag import synthesize_investigation


router = APIRouter(prefix="/incidents", tags=["Incidents"])

class AnalyzeRequest(BaseModel):
    window_seconds: float = 300.0  # Look back 5 minutes by default
    trace_id: Optional[str] = None
    title: Optional[str] = None

@router.post("/analyze", response_model=IncidentReport)
async def analyze_incident(req: AnalyzeRequest):
    """Trigger incident graph construction and root-cause ranking over recent telemetry."""
    # Gather candidate events
    if req.trace_id:
        events = store.get_events(trace_id=req.trace_id, limit=300)
    else:
        # Fetch events within the specified window
        now = time.time()
        events = store.get_events(since_timestamp=now - req.window_seconds, limit=300)

    if not events:
        raise HTTPException(
            status_code=404,
            detail="No telemetry events found in the requested window to analyze"
        )

    # 1. Build NetworkX incident graph
    G, nodes, edges = build_incident_graph(events)

    # 2. Run Root-Cause Ranking
    ranked_causes = rank_root_causes(G, nodes)

    # 3. Determine incident severity and summary
    error_count = sum(1 for n in nodes if n.is_error)
    severity = "CRITICAL" if error_count >= 5 else "HIGH" if error_count >= 2 else "MEDIUM"
    
    top_suspect = ranked_causes[0] if ranked_causes else None
    top_service = top_suspect.service if top_suspect else "unknown"
    top_reason = top_suspect.reasons[0] if (top_suspect and top_suspect.reasons) else "Cascading error detected"

    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    title = req.title or f"Incident in [{top_service}]: {error_count} error events detected"
    
    summary = (
        f"Detected incident involving {len(nodes)} correlated events across {len(set(n.service for n in nodes))} services. "
        f"Top suspected root cause: [{top_service}] ({top_reason}) with confidence {top_suspect.confidence if top_suspect else 'LOW'}."
    )

    recommended_actions = []
    if top_suspect and top_suspect.event_type == "deployment":
        recommended_actions.append(f"Rollback recent deployment on service [{top_service}]")
    if top_suspect and "exhausted" in top_suspect.message.lower():
        recommended_actions.append(f"Restart connection pool or scale instances for [{top_service}]")

    # 3. Synthesize historical RAG intelligence
    historical_intelligence = synthesize_investigation(
        nodes=nodes,
        ranked_causes=ranked_causes,
        top_k=4
    )


    if not recommended_actions and historical_intelligence.recommended_investigation:
        recommended_actions.extend(historical_intelligence.recommended_investigation[:2])
    elif not recommended_actions:
        recommended_actions.append(f"Inspect recent error stack trace on service [{top_service}]")

    report = IncidentReport(
        incident_id=incident_id,
        title=title,
        status="active",
        severity=severity,
        started_at=nodes[0].timestamp if nodes else time.time(),
        detected_at=time.time(),
        event_count=len(events),
        nodes=nodes,
        edges=edges,
        root_cause_ranking=ranked_causes,
        summary=summary,
        recommended_actions=recommended_actions,
        historical_intelligence=historical_intelligence,
    )

    store.save_incident(report)
    return report


@router.get("", response_model=List[IncidentSummary])
async def list_incidents():
    """List all analyzed incidents."""
    incidents = store.list_incidents()
    summaries = []
    for inc in reversed(incidents):
        top_cand = inc.root_cause_ranking[0] if inc.root_cause_ranking else None
        summaries.append(IncidentSummary(
            incident_id=inc.incident_id,
            title=inc.title,
            status=inc.status,
            severity=inc.severity,
            started_at=inc.started_at,
            detected_at=inc.detected_at,
            event_count=inc.event_count,
            top_suspect=top_cand.message[:60] if top_cand else None,
            top_suspect_service=top_cand.service if top_cand else None,
        ))
    return summaries

@router.get("/{incident_id}", response_model=IncidentReport)
async def get_incident(incident_id: str):
    """Retrieve complete incident report with graph nodes, edges, and root cause ranking."""
    inc = store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return inc
