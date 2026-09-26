import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.agent.state import create_initial_state
from backend.app.agent.graph import opspilot_app
from backend.app.models.schema import PaymentLifecycleState
from backend.app.tools.stripe import execution_locks
from backend.app.db.database import db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_locks():
    execution_locks.reset()
    yield
    execution_locks.reset()

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "Notion" in data["providers_enabled"]
    assert "Stripe" in data["providers_enabled"]
    assert "Gmail" in data["providers_enabled"]
    assert "Slack" in data["providers_enabled"]
    assert "Jira" in data["providers_enabled"]

def test_tools_endpoint():
    resp = client.get("/api/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tools"]) == 17

def test_scenarios_endpoint():
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    scenarios = resp.json()
    assert len(scenarios) == 4

def test_run_submission_and_approval_gate():
    run_id = "run_api_approval_test"
    # 1. Directly invoke initial state to reach authorization gate
    init_state = create_initial_state(
        run_id=run_id,
        user_request="Handle the Zelar payment.",
        scenario_id="scenario_1_success",
        demo_mode=True,
        auto_approve=False,
    )
    paused_state = opspilot_app.invoke(init_state)
    assert paused_state["status"] == "APPROVAL_REQUIRED"
    assert paused_state["payment_state"] == PaymentLifecycleState.APPROVAL_REQUIRED.value
    db.save_run_state(paused_state)

    # 2. Call API approval endpoint
    appr_resp = client.post(
        f"/api/runs/{run_id}/approve",
        json={
            "approved": True,
            "comment": "Authorized by Finance Director",
            "approver_name": "Finance Director (Human)",
        },
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["payment_state"] == PaymentLifecycleState.HUMAN_APPROVED.value

    # 3. Resume Graph execution with approved state
    approved_state = db.get_run_state(run_id)
    # Reset execution lock for the single test runner pass
    execution_locks.reset()
    final_state = opspilot_app.invoke(approved_state)
    assert final_state["status"] == "COMPLETED"
    assert final_state["payment_state"] == PaymentLifecycleState.PAID.value
    assert final_state["payout_id"] == "po_zelar_mar2026_succ104"
    assert final_state["reconciliation_state"]["systems_aligned"] is True
    db.save_run_state(final_state)

    # 4. Check Audit Trail
    audit_resp = client.get(f"/api/runs/{run_id}/audit")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()["audit_trail"]
    assert len(logs) >= 3
