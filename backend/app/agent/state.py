from typing import Any, Dict, List, Optional, TypedDict
import datetime
import uuid
from ..models.schema import (
    PaymentLifecycleState,
    EvidenceItem,
    DecisionObject,
    ActionItem,
    AuditEvent,
    AgentEvent,
    ApprovalLockPayload,
    OperationType,
)

class OpsPilotState(TypedDict):
    run_id: str
    operation_id: str
    operation_type: str  # "VENDOR_PAYOUT"
    user_request: str
    scenario_id: Optional[str]
    demo_mode: bool
    auto_approve: bool
    status: str
    
    # Normalized business entity context
    customer: str
    vendor: str
    vendor_id: str
    invoice: str
    po_id: str
    amount: float
    currency: str
    purpose: str
    verified_payout_destination: Optional[str]
    is_destination_verified: bool
    
    # Layered Contexts
    business_context: Dict[str, Any]
    financial_context: Dict[str, Any]
    communication_context: Dict[str, Any]
    engineering_context: Dict[str, Any]
    
    # Evidence & Sources
    evidence: List[Dict[str, Any]]
    evidence_sources: List[str]
    
    # Decisions & Planning
    current_decision: Optional[Dict[str, Any]]
    decision_summary: str
    confidence: float
    planned_actions: List[Dict[str, Any]]
    executed_actions: List[Dict[str, Any]]
    
    # Human Authorization & Execution Lock
    approval_required: bool
    approval_status: str  # "NOT_REQUIRED", "PENDING", "APPROVED", "REJECTED"
    approval_comment: Optional[str]
    approval_lock_data: Optional[Dict[str, Any]]
    is_execution_locked: bool
    
    # Lifecycle & Operational States
    payment_state: str  # PaymentLifecycleState value
    payout_id: Optional[str]
    payout_status: Optional[str]  # "pending", "in_transit", "paid", "failed", "canceled"
    payment_details: Dict[str, Any]
    communication_state: Dict[str, Any]
    reconciliation_state: Dict[str, Any]
    
    # Investigation Loop Tracking
    investigation_turns: int
    max_investigation_turns: int
    missing_information: List[str]
    next_tool_to_call: Optional[Dict[str, Any]]
    
    # Observability & Audit
    tool_events: List[Dict[str, Any]]
    audit_events: List[Dict[str, Any]]
    errors: List[str]
    timestamps: Dict[str, str]
    final_response: Optional[str]

def create_initial_state(
    run_id: str,
    user_request: str,
    scenario_id: Optional[str] = "scenario_1_success",
    demo_mode: bool = True,
    auto_approve: bool = False,
) -> OpsPilotState:
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    op_suffix = run_id.replace("run_", "")
    operation_id = f"op_zelar_{op_suffix}" if "zelar" in user_request.lower() else f"op_{op_suffix}"
    
    return {
        "run_id": run_id,
        "operation_id": operation_id,
        "operation_type": OperationType.VENDOR_PAYOUT.value,
        "user_request": user_request,
        "scenario_id": scenario_id,
        "demo_mode": demo_mode,
        "auto_approve": auto_approve,
        "status": "REQUESTED",
        "customer": "Thoughtworks",
        "vendor": "",
        "vendor_id": "",
        "invoice": "",
        "po_id": "",
        "amount": 0.0,
        "currency": "INR",
        "purpose": "",
        "verified_payout_destination": None,
        "is_destination_verified": False,
        "business_context": {},
        "financial_context": {},
        "communication_context": {},
        "engineering_context": {},
        "evidence": [],
        "evidence_sources": [],
        "current_decision": None,
        "decision_summary": "",
        "confidence": 1.0,
        "planned_actions": [],
        "executed_actions": [],
        "approval_required": True,
        "approval_status": "NOT_REQUIRED",
        "approval_comment": None,
        "approval_lock_data": None,
        "is_execution_locked": False,
        "payment_state": PaymentLifecycleState.REQUESTED.value,
        "payout_id": None,
        "payout_status": None,
        "payment_details": {},
        "communication_state": {"gmail_status": "PENDING", "slack_status": "PENDING"},
        "reconciliation_state": {"systems_aligned": False, "discrepancies": []},
        "investigation_turns": 0,
        "max_investigation_turns": 5,
        "missing_information": [
            "vendor_invoice_record",
            "stripe_financial_state",
            "internal_finance_chatter",
            "jira_operational_issue",
        ],
        "next_tool_to_call": None,
        "tool_events": [],
        "audit_events": [],
        "errors": [],
        "timestamps": {"started_at": now_iso},
        "final_response": None,
    }
