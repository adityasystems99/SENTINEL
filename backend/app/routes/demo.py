"""Demo failure injection routes for interactive demonstration."""
from fastapi import APIRouter, HTTPException
from ..storage.memory_store import store
from demo_app.service import DemoAppService
from demo_app.scenarios import (
    inject_db_pool_exhaustion,
    inject_bad_auth_deployment,
    inject_payment_timeout,
    generate_healthy_traffic,
    recover_all,
)

router = APIRouter(prefix="/demo", tags=["Demo"])

# Singleton demo service connected to in-memory store
demo_svc = DemoAppService(telemetry_sink=lambda events: store.add_events(events))

@router.post("/scenario/{scenario_name}")
async def trigger_scenario(scenario_name: str, count: int = 3):
    """Trigger a failure-injection or traffic scenario."""
    if scenario_name == "db_pool_exhaustion":
        inject_db_pool_exhaustion(demo_svc, count=count)
        return {"status": "injected", "scenario": scenario_name, "message": "Database pool exhaustion triggered on inventory-service"}
    elif scenario_name == "bad_auth_deployment":
        inject_bad_auth_deployment(demo_svc, count=count)
        return {"status": "injected", "scenario": scenario_name, "message": "Bad deployment + NullPointer triggered on auth-service"}
    elif scenario_name == "payment_timeout":
        inject_payment_timeout(demo_svc, count=count)
        return {"status": "injected", "scenario": scenario_name, "message": "Downstream payment timeout triggered on payment-service"}
    elif scenario_name == "healthy_traffic":
        generate_healthy_traffic(demo_svc, count=count)
        return {"status": "generated", "scenario": scenario_name, "message": f"Generated {count} normal checkout transactions"}
    elif scenario_name == "recover":
        recover_all(demo_svc)
        return {"status": "recovered", "scenario": scenario_name, "message": "All failure scenarios cleared; system healthy"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario '{scenario_name}'. Valid: db_pool_exhaustion, bad_auth_deployment, payment_timeout, healthy_traffic, recover")
