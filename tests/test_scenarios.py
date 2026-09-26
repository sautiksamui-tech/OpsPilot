import pytest
from backend.app.agent.graph import opspilot_app
from backend.app.agent.state import create_initial_state
from backend.app.models.schema import PaymentLifecycleState

def test_scenario_1_success_workflow():
    init_state = create_initial_state(
        run_id="run_test_scen1",
        user_request="Handle the Zelar payment.",
        scenario_id="scenario_1_success",
        demo_mode=True,
        auto_approve=True,  # Simulate immediate approval
    )
    final_state = opspilot_app.invoke(init_state)
    assert final_state["status"] == "COMPLETED"
    assert final_state["payment_state"] == PaymentLifecycleState.PAID.value
    assert len(final_state["evidence"]) >= 4
    assert final_state["payout_id"] == "po_zelar_mar2026_succ104"
    assert final_state["reconciliation_state"]["systems_aligned"] is True
    assert "Vendor Settlement Completed & Reconciled" in final_state["final_response"]

def test_scenario_2_failure_workflow():
    init_state = create_initial_state(
        run_id="run_test_scen2",
        user_request="Handle the Zelar payment.",
        scenario_id="scenario_2_failure",
        demo_mode=True,
        auto_approve=True,
    )
    final_state = opspilot_app.invoke(init_state)
    assert final_state["status"] == "COMPLETED"
    assert final_state["payment_state"] == PaymentLifecycleState.FAILED.value
    assert "Vendor Settlement Exception Handled" in final_state["final_response"]

def test_scenario_3_unknown_timeout_workflow():
    init_state = create_initial_state(
        run_id="run_test_scen3",
        user_request="Handle the Zelar payment.",
        scenario_id="scenario_3_unknown_timeout",
        demo_mode=True,
        auto_approve=True,
    )
    final_state = opspilot_app.invoke(init_state)
    assert final_state["status"] == "COMPLETED"
    assert final_state["payout_id"] == "po_zelar_mar2026_timeout_recon"
    assert "Gateway Timeout Reconciled" in final_state["final_response"]

def test_scenario_4_mismatch_workflow():
    init_state = create_initial_state(
        run_id="run_test_scen4",
        user_request="Pay ₹2,80,000 to vendor Zelar for March services.",
        scenario_id="scenario_4_mismatch",
        demo_mode=True,
        auto_approve=True,
    )
    final_state = opspilot_app.invoke(init_state)
    assert final_state["status"] == "COMPLETED"
    assert final_state["payment_state"] == PaymentLifecycleState.BLOCKED.value
    assert "Vendor Settlement Blocked by Safety & Compliance Policy" in final_state["final_response"]
