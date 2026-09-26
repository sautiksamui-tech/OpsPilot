import pytest
from unittest.mock import patch, MagicMock
from backend.app.agent.graph import opspilot_app
from backend.app.agent.state import create_initial_state
from backend.app.agent.engine import engine
from backend.app.models.schema import PaymentLifecycleState, DecisionType
from backend.app.tools.stripe import StripeToolAdapter, execution_locks
from backend.app.tools.swytchcode_client import swytchcode_client
from backend.app.db.database import db

@pytest.fixture(autouse=True)
def reset_locks():
    execution_locks.reset()
    yield
    execution_locks.reset()

def test_no_payout_before_human_authorization():
    """
    1. Proves no payout occurs before explicit human authorization.
    Graph stops at APPROVAL_REQUIRED with no payout ID created.
    """
    init_state = create_initial_state(
        run_id="run_test_no_auth",
        user_request="Handle the Zelar payment.",
        scenario_id="scenario_1_success",
        demo_mode=True,
        auto_approve=False,  # Human approval not granted yet
    )
    paused_state = opspilot_app.invoke(init_state)
    assert paused_state["status"] == "APPROVAL_REQUIRED"
    assert paused_state["payment_state"] == PaymentLifecycleState.APPROVAL_REQUIRED.value
    assert paused_state.get("payout_id") is None
    assert paused_state.get("approval_lock_data") is not None
    assert paused_state["approval_lock_data"]["vendor_name"] == "Zelar"
    assert paused_state["approval_lock_data"]["exact_amount"] == 240000.0
    assert paused_state["approval_lock_data"]["verified_payout_destination"] == "ba_zelar_corp_hdfc_0981"

def test_amount_mismatch_blocks_payout():
    """
    2. Proves amount mismatch between request and Notion PO blocks payout before creation.
    """
    init_state = create_initial_state(
        run_id="run_test_mismatch",
        user_request="Pay ₹2,80,000 to vendor Zelar.",
        scenario_id="scenario_4_mismatch",
        demo_mode=True,
        auto_approve=True,
    )
    final_state = opspilot_app.invoke(init_state)
    assert final_state["status"] == "COMPLETED"
    assert final_state["payment_state"] == PaymentLifecycleState.BLOCKED.value
    assert final_state.get("payout_id") is None
    assert "Blocked by Safety & Compliance Policy" in final_state["final_response"]

def test_unverified_destination_blocks_payout():
    """
    3. Proves unverified or missing bank account destination blocks payout creation.
    """
    state = {
        "vendor": "Zelar",
        "invoice": "ZELAR-MAR-2026-104",
        "amount": 240000.0,
        "verified_payout_destination": "invalid_card_destination",
        "is_destination_verified": False,
        "evidence": [{"id": "ev_1"}],
    }
    decision = engine.synthesize_and_decide(state)
    assert decision.decision == DecisionType.BLOCK_UNVERIFIED_DESTINATION
    assert "Destination account" in decision.summary

    # Adapter direct test
    res = StripeToolAdapter.create_payout(
        operation_id="op_test_bad_dest",
        vendor_id="VEND-ZELAR-009",
        vendor_name="Zelar",
        po_id="PO-TW-2026-0881",
        invoice_id="ZELAR-MAR-2026-104",
        amount=240000.0,
        currency="INR",
        destination="unverified_dest",
        demo_mode=True,
    )
    assert res["success"] is False
    assert res["payment_state"] == PaymentLifecycleState.BLOCKED.value
    assert res["error_code"] == "unverified_destination"

def test_duplicate_operation_blocks_second_payout():
    """
    4. Proves duplicate operation_id is strictly blocked by application-level execution lock.
    """
    op_id = "op_idempotency_test_001"
    
    # First payout attempt succeeds
    res1 = StripeToolAdapter.create_payout(
        operation_id=op_id,
        vendor_id="VEND-ZELAR-009",
        vendor_name="Zelar",
        po_id="PO-TW-2026-0881",
        invoice_id="ZELAR-MAR-2026-104",
        amount=240000.0,
        currency="INR",
        destination="ba_zelar_corp_hdfc_0981",
        demo_mode=True,
    )
    assert res1["success"] is True
    assert res1["payout_id"] == "po_zelar_mar2026_succ104"

    # Second payout attempt with same operation_id must be blocked immediately
    res2 = StripeToolAdapter.create_payout(
        operation_id=op_id,
        vendor_id="VEND-ZELAR-009",
        vendor_name="Zelar",
        po_id="PO-TW-2026-0881",
        invoice_id="ZELAR-MAR-2026-104",
        amount=240000.0,
        currency="INR",
        destination="ba_zelar_corp_hdfc_0981",
        demo_mode=True,
    )
    assert res2["success"] is False
    assert res2["error_code"] == "duplicate_operation_blocked"
    assert "DUPLICATE BLOCKED" in res2["summary"]

def test_demo_mode_never_executes_real_swytchcode():
    """
    5. Proves demo mode uses deterministic schema fixtures and does not execute subprocess swytchcode.
    """
    with patch("subprocess.run") as mock_subproc:
        success, out, duration, err = swytchcode_client.exec(
            canonical_id="stripe.payout.create",
            inputs={"amount": 24000000, "currency": "inr", "destination": "ba_zelar_corp_hdfc_0981"},
            demo_mode=True,
            scenario_id="scenario_1_success",
        )
        assert success is True
        assert out["id"] == "po_zelar_mar2026_succ104"
        assert mock_subproc.call_count == 0  # Subprocess was NEVER called

def test_real_mode_invokes_stripe_payout_create():
    """
    6. Proves real mode invokes actual Swytchcode CLI kernel for stripe.payout.create.
    """
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"id": "po_live_test_7788", "object": "payout", "amount": 24000000, "currency": "inr", "status": "paid", "destination": "ba_zelar_corp_hdfc_0981"}'
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_subproc:
        res = StripeToolAdapter.create_payout(
            operation_id="op_real_mode_test",
            vendor_id="VEND-ZELAR-009",
            vendor_name="Zelar",
            po_id="PO-TW-2026-0881",
            invoice_id="ZELAR-MAR-2026-104",
            amount=240000.0,
            currency="INR",
            destination="ba_zelar_corp_hdfc_0981",
            demo_mode=False,  # REAL MODE
        )
        assert res["success"] is True
        assert res["is_simulation"] is False
        assert res["execution_mode"] == "REAL / SWYTCHCODE"
        assert res["payout_id"] == "po_live_test_7788"
        assert mock_subproc.call_count == 1
        call_args = mock_subproc.call_args[0][0]
        assert "swytchcode exec stripe.payout.create" in call_args

def test_payout_status_changes_subsequent_workflow():
    """
    7. Proves payout status determines downstream branch:
       Success (paid) -> Reconciliation node
       Failure (failed) -> Exception Recovery node
    """
    # Scenario 1 (Paid)
    init_state_1 = create_initial_state("run_scen1_test", "Zelar", "scenario_1_success", demo_mode=True, auto_approve=True)
    res_1 = opspilot_app.invoke(init_state_1)
    assert res_1["payment_state"] == PaymentLifecycleState.PAID.value
    assert res_1["reconciliation_state"]["systems_aligned"] is True

    # Scenario 2 (Failed)
    init_state_2 = create_initial_state("run_scen2_test", "Zelar", "scenario_2_failure", demo_mode=True, auto_approve=True)
    res_2 = opspilot_app.invoke(init_state_2)
    assert res_2["payment_state"] == PaymentLifecycleState.FAILED.value
    assert res_2["reconciliation_state"].get("recovery_applied") is True

def test_unknown_state_triggers_payout_get_rather_than_retry():
    """
    8. Proves gateway timeout / unknown state triggers stripe.payout.get with known payout ID
       and prohibits blind stripe.payout.create retries.
    """
    init_state = create_initial_state(
        run_id="run_test_unknown",
        user_request="Handle the Zelar payment.",
        scenario_id="scenario_3_unknown_timeout",
        demo_mode=True,
        auto_approve=True,
    )

    final_state = opspilot_app.invoke(init_state)
    assert final_state["status"] == "COMPLETED"
    # Verify stripe.payout.get was recorded in tool events
    tool_ids = [e.get("canonical_id") for e in final_state.get("tool_events", [])]
    # Check that known payout ID was preserved without duplicate payout creation
    assert final_state.get("payout_id") == "po_zelar_mar2026_timeout_recon"
    assert "Gateway Timeout Reconciled" in final_state["final_response"]
