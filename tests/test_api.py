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
    # 1. Start run via API endpoint
    start_resp = client.post(
        "/api/agent/run",
        json={
            "prompt": "Settle Zelar's approved March invoice for ₹2,40,000.",
            "scenario_id": "scenario_1_success",
            "demo_mode": True,
            "auto_approve": False,
        },
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    run_id = start_data["run_id"]
    assert start_data["status"] == "APPROVAL_REQUIRED"
    assert start_data["payment_state"] == PaymentLifecycleState.APPROVAL_REQUIRED.value

    # Verify state saved in DB
    paused_state = db.get_run_state(run_id)
    assert paused_state is not None
    assert paused_state["status"] == "APPROVAL_REQUIRED"

    # Verify events list endpoint
    events_resp = client.get(f"/api/runs/{run_id}/events/list")
    assert events_resp.status_code == 200
    assert len(events_resp.json()["events"]) >= 3

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
    assert appr_resp.json()["status"] == "COMPLETED"
    assert appr_resp.json()["payment_state"] == PaymentLifecycleState.PAID.value

    # 3. Verify final state in DB
    final_state = db.get_run_state(run_id)
    assert final_state["status"] == "COMPLETED"
    assert final_state["payment_state"] == PaymentLifecycleState.PAID.value
    assert final_state["payout_id"] == "po_zelar_mar2026_succ104"
    assert final_state["reconciliation_state"]["systems_aligned"] is True

    # 4. Check Audit Trail
    audit_resp = client.get(f"/api/runs/{run_id}/audit")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()["audit_trail"]
    assert len(logs) >= 3
