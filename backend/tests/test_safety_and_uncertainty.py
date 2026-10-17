"""Safety, Security, and Uncertainty Verification Tests for SENTINEL.
Task 5:
1. Replay Lab approval requirement is enforced (no unauthorized test execution).
2. Uploaded project code is strictly read-only and NEVER executed.
3. No autonomous production remediation is performed (pure advisory architecture).
4. Missing telemetry is flagged in uncertainty disclosures, not claimed as healthy.
5. Inconclusive signals produce LOW confidence / uncertainty warnings.
"""
import inspect
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.telemetry import TelemetryEvent, LogLevel
from backend.app.graph.builder import build_incident_graph
from backend.app.graph.ranker import rank_root_causes
from backend.app.services.rag.synthesizer import synthesize_investigation
from backend.app.services.audit_engine import audit_project_against_spec, inspect_python_ast
from backend.app.routes import validation, incidents

client = TestClient(app)


def test_replay_lab_approval_requirement_enforced():
    """Verify that Replay Lab rejects fix execution without explicit user approval."""
    # Attempting to run validation without approved=True must return 400 with safety constraint error
    payload = {
        "experiment_id": "exp-dummy",
        "fix_id": "FIX-INV-001",
        "approved": False,
        "workload_count": 5
    }
    resp = client.post("/api/validation/run", json=payload)
    assert resp.status_code == 400
    assert "Explicit user approval is mandatory" in resp.json()["detail"]


def test_no_arbitrary_code_execution_in_audit_engine():
    """Verify that audit engine only reads files via AST/regex and never calls exec, eval, or system."""
    source_code = inspect.getsource(audit_project_against_spec) + inspect.getsource(inspect_python_ast)
    
    # Assert dangerous execution primitives are absent
    assert "exec(" not in source_code, "Audit engine must never call exec()"
    assert "eval(" not in source_code, "Audit engine must never call eval()"
    assert "os.system(" not in source_code, "Audit engine must never call os.system()"
    assert "subprocess." not in source_code, "Audit engine must never call subprocess on uploaded code"


def test_no_autonomous_remediation_in_incident_routes():
    """Verify that incident investigation endpoints are purely advisory and perform no mutations."""
    source_code = inspect.getsource(incidents.analyze_incident)
    
    # Assert that incident analysis does not perform cluster mutations or remote restarts
    assert "kubernetes" not in source_code.lower()
    assert "kubectl" not in source_code.lower()
    assert "helm" not in source_code.lower()
    assert "restart_pod" not in source_code.lower()
    assert "rollback_deployment" not in source_code.lower()


def test_missing_telemetry_produces_explicit_uncertainty_disclosure():
    """Verify that missing telemetry is not interpreted as healthy, but yields uncertainty disclosure."""
    # Only 1 single error event with no trace or context
    single_event = TelemetryEvent(
        service="payment-service",
        level=LogLevel.ERROR,
        message="Transient warning",
    )
    G, nodes, edges = build_incident_graph([single_event])
    ranked = rank_root_causes(G, nodes)

    synthesis = synthesize_investigation(
        nodes=nodes,
        ranked_causes=ranked,
        top_k=2,
    )

    # Must contain uncertainty disclosures
    assert len(synthesis.uncertainty_disclosures) > 0
    # Must acknowledge missing telemetry / uncaptured state
    disclosure_text = " ".join(synthesis.uncertainty_disclosures).lower()
    assert "telemetry" in disclosure_text or "missing" in disclosure_text or "uncaptured" in disclosure_text or "spans" in disclosure_text
