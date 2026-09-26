import pytest
from backend.app.agent.state import create_initial_state, OpsPilotState
from backend.app.models.schema import PaymentLifecycleState

def test_initial_state_creation():
    state = create_initial_state(
        run_id="run_test_01",
        user_request="Handle the Zelar payment.",
        scenario_id="scenario_1_success",
        demo_mode=True,
    )
    assert state["run_id"] == "run_test_01"
    assert state["user_request"] == "Handle the Zelar payment."
    assert state["status"] == "REQUESTED"
    assert state["payment_state"] == PaymentLifecycleState.REQUESTED.value
    assert state["operation_type"] == "VENDOR_PAYOUT"
    assert len(state["missing_information"]) == 4
    assert state["investigation_turns"] == 0
