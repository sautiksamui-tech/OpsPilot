import pytest
from backend.app.agent.engine import engine
from backend.app.models.schema import DecisionType, PaymentLifecycleState

def test_intent_analysis():
    res = engine.analyze_intent("Handle the Zelar payment.")
    assert res["vendor"] == "Zelar"
    assert res["customer"] == "Thoughtworks"

def test_amount_mismatch_detection():
    # Simulated state where user asks for ₹280,000 but invoice is ₹240,000
    state = {
        "vendor": "Zelar",
        "invoice": "ZELAR-MAR-2026-104",
        "amount": 240000.0,
        "business_context": {"explicit_amount": 280000.0},
        "evidence": [{"id": "ev_1"}, {"id": "ev_2"}],
    }
    decision = engine.synthesize_and_decide(state)
    assert decision.decision == DecisionType.BLOCK_PAYMENT_DISCREPANCY
    assert len(decision.blocked_reasons) > 0
    assert "₹280,000.00" in decision.summary

def test_exception_recovery_timeout_unknown():
    state = {
        "vendor": "Zelar",
        "invoice": "ZELAR-MAR-2026-104",
        "amount": 240000.0,
        "engineering_context": {"jira": {"existing_key": "SCRUM-42"}},
    }
    payment_result = {
        "payment_state": PaymentLifecycleState.UNKNOWN.value,
        "error_code": "gateway_timeout",
        "decline_reason": "network_timeout_during_settlement",
    }
    new_state, actions, explanation = engine.handle_exception_recovery(state, payment_result)
    assert new_state == PaymentLifecycleState.UNKNOWN.value
    assert "Distinguishing UNKNOWN from FAILED" in explanation
    assert len(actions) == 3
