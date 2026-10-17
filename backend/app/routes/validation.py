"""API routes for Feature 5: Controlled Fix Validation (Replay Lab)."""
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from ..models.validation import (
    BaselineExperimentResult,
    BaselineRequest,
    FailureScenarioDefinition,
    FixValidationReport,
    FixValidationRequest,
)
from ..services.validation_engine import validation_engine

router = APIRouter(prefix="/validation", tags=["Fix Validation"])

@router.get("/scenarios", response_model=List[FailureScenarioDefinition])
async def list_scenarios():
    """List available failure scenarios and candidate fixes for controlled experiment validation."""
    return validation_engine.get_scenarios()

@router.post("/baseline", response_model=BaselineExperimentResult)
async def run_baseline_experiment(request: BaselineRequest):
    """Inject failure scenario in local sandbox and record baseline performance and error metrics."""
    try:
        return validation_engine.run_baseline_experiment(
            scenario_id=request.scenario_id,
            workload_count=request.workload_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/run", response_model=FixValidationReport)
async def run_fix_validation(request: FixValidationRequest):
    """Apply approved candidate fix in sandbox, replay scenario, and produce before/after verdict."""
    if not request.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Safety constraint: Explicit user approval is mandatory before applying fixes."
        )

    try:
        return validation_engine.run_fix_validation(
            experiment_id=request.experiment_id,
            fix_id=request.fix_id,
            approved=request.approved,
            workload_count=request.workload_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[FixValidationReport])
async def get_validation_history():
    """Retrieve history of previous fix validation experiments."""
    return validation_engine.history
