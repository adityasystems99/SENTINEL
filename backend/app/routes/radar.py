"""API routes for Feature 4: Dependency and Impact Radar."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from ..models.impact import (
    ImpactAnalysisRequest,
    ImpactReport,
    ServiceTopologyEdge,
    ServiceTopologyNode,
)
from ..services.impact_engine import analyze_service_impact, build_service_topology
from ..auth.security import UserContext, get_current_user

router = APIRouter(prefix="/radar", tags=["Impact Radar"])

@router.get("/topology")
async def get_topology(
    window_seconds: int = Query(600, ge=30, le=86400),
    current_user: UserContext = Depends(get_current_user),
):
    """Retrieve full service dependency topology, edges, and current node health."""
    G, nodes, edges = build_service_topology(window_seconds=window_seconds)
    return {
        "nodes": nodes,
        "edges": edges,
        "total_services": len(nodes),
        "total_dependencies": len(edges),
    }

@router.post("/analyze", response_model=ImpactReport)
async def analyze_impact(
    request: ImpactAnalysisRequest,
    current_user: UserContext = Depends(get_current_user),
):
    """Analyze the blast radius, cascading dependents, and investigation priority for a suspected component."""
    if not request.suspected_component or not request.suspected_component.strip():
        raise HTTPException(status_code=400, detail="Suspected component name must be provided")

    report = analyze_service_impact(
        suspected_component=request.suspected_component.strip(),
        window_seconds=request.window_seconds,
    )
    return report

@router.get("/analyze/{service_name}", response_model=ImpactReport)
async def analyze_service_get(
    service_name: str,
    window_seconds: int = Query(600, ge=30, le=86400),
    current_user: UserContext = Depends(get_current_user),
):
    """GET shortcut to analyze impact for a specific service."""
    return analyze_service_impact(suspected_component=service_name, window_seconds=window_seconds)
