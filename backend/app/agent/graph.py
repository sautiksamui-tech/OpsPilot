from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from .state import OpsPilotState
from .nodes import (
    intent_analysis_node,
    context_planner_node,
    investigate_node,
    evidence_synthesis_node,
    decision_node,
    action_planner_node,
    approval_gate_node,
    execute_node,
    verify_node,
    exception_recovery_node,
    reconciliation_node,
    audit_node,
    final_response_node,
)
from ..models.schema import PaymentLifecycleState

def should_continue_investigating(state: OpsPilotState) -> Literal["context_planner", "evidence_synthesis"]:
    missing = state.get("missing_information", [])
    turns = state.get("investigation_turns", 0)
    max_turns = state.get("max_investigation_turns", 5)

    if missing and turns < max_turns:
        return "context_planner"
    return "evidence_synthesis"

def route_after_approval_gate(state: OpsPilotState) -> Literal["execute", "final_response", END]:
    status = state.get("status")
    p_state = state.get("payment_state")

    if status in ("AWAITING_APPROVAL", "APPROVAL_REQUIRED"):
        # Pauses execution so backend can wait for human authorization API endpoint
        return END

    if p_state == PaymentLifecycleState.CANCELLED.value or status == "CANCELLED":
        return "final_response"

    return "execute"

def route_after_execute(state: OpsPilotState) -> Literal["verify", "audit"]:
    p_state = state.get("payment_state")
    if p_state == PaymentLifecycleState.BLOCKED.value:
        return "audit"
    return "verify"

def route_after_verify(state: OpsPilotState) -> Literal["reconciliation", "exception_recovery"]:
    p_state = state.get("payment_state")
    if p_state in (PaymentLifecycleState.PAID.value, PaymentLifecycleState.SUCCEEDED.value):
        return "reconciliation"
    return "exception_recovery"

def create_opspilot_graph():
    workflow = StateGraph(OpsPilotState)

    # 1. Register Nodes
    workflow.add_node("intent_analysis", intent_analysis_node)
    workflow.add_node("context_planner", context_planner_node)
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("evidence_synthesis", evidence_synthesis_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("action_planner", action_planner_node)
    workflow.add_node("approval_gate", approval_gate_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("exception_recovery", exception_recovery_node)
    workflow.add_node("reconciliation", reconciliation_node)
    workflow.add_node("audit", audit_node)
    workflow.add_node("final_response", final_response_node)

    # 2. Add Edges & Conditional Routing
    workflow.add_edge(START, "intent_analysis")
    workflow.add_edge("intent_analysis", "context_planner")
    workflow.add_edge("context_planner", "investigate")

    workflow.add_conditional_edges(
        "investigate",
        should_continue_investigating,
        {
            "context_planner": "context_planner",
            "evidence_synthesis": "evidence_synthesis",
        },
    )

    workflow.add_edge("evidence_synthesis", "decision")
    workflow.add_edge("decision", "action_planner")
    workflow.add_edge("action_planner", "approval_gate")

    workflow.add_conditional_edges(
        "approval_gate",
        route_after_approval_gate,
        {
            "execute": "execute",
            "final_response": "final_response",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "execute",
        route_after_execute,
        {
            "verify": "verify",
            "audit": "audit",
        },
    )

    workflow.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "reconciliation": "reconciliation",
            "exception_recovery": "exception_recovery",
        },
    )

    workflow.add_edge("exception_recovery", "audit")
    workflow.add_edge("reconciliation", "audit")
    workflow.add_edge("audit", "final_response")
    workflow.add_edge("final_response", END)

    return workflow.compile()

opspilot_app = create_opspilot_graph()
