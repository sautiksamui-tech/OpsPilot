from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import datetime

class PaymentLifecycleState(str, Enum):
    REQUESTED = "REQUESTED"
    CONTEXT_VERIFIED = "CONTEXT_VERIFIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    EXECUTION_LOCKED = "EXECUTION_LOCKED"
    PAYOUT_CREATING = "PAYOUT_CREATING"
    PAYOUT_CREATED = "PAYOUT_CREATED"
    RECONCILING = "RECONCILING"
    PAID = "PAID"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    
    # Backward compatibility aliases
    SUCCEEDED = "PAID"
    AWAITING_APPROVAL = "APPROVAL_REQUIRED"
    APPROVED = "HUMAN_APPROVED"
    VALIDATING = "CONTEXT_VERIFIED"
    INITIATING = "PAYOUT_CREATING"
    PROCESSING = "PAYOUT_CREATING"
    REQUIRES_ACTION = "APPROVAL_REQUIRED"
    RECONCILIATION_REQUIRED = "RECONCILING"

SettlementLifecycleState = PaymentLifecycleState

class OperationType(str, Enum):
    VENDOR_PAYOUT = "VENDOR_PAYOUT"

class PayoutStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"
    UNKNOWN = "unknown"

class ApprovalLockPayload(BaseModel):
    operation_id: str
    vendor_id: str
    vendor_name: str
    po_id: str
    invoice_id: str
    exact_amount: float
    currency: str = "INR"
    verified_payout_destination: str
    approver: str
    approval_timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

class EvidenceItem(BaseModel):
    id: str
    provider: str  # "Notion", "Stripe", "Gmail", "Slack", "Jira"
    canonical_tool_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    identifier: str
    title: str
    normalized_content: Dict[str, Any]
    raw_output: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    impact_on_decision: str = ""

class DecisionType(str, Enum):
    PROCEED_TO_APPROVAL = "PROCEED_TO_APPROVAL"
    REQUEST_MORE_INFO = "REQUEST_MORE_INFO"
    BLOCK_PAYMENT_DISCREPANCY = "BLOCK_PAYMENT_DISCREPANCY"
    BLOCK_UNVERIFIED_DESTINATION = "BLOCK_UNVERIFIED_DESTINATION"
    RECOVER_PAYMENT_FAILURE = "RECOVER_PAYMENT_FAILURE"
    RECONCILE_UNKNOWN_STATE = "RECONCILE_UNKNOWN_STATE"
    COMPLETE_SUCCESS = "COMPLETE_SUCCESS"
    CANCELLED_BY_APPROVER = "CANCELLED_BY_APPROVER"

class DecisionObject(BaseModel):
    decision: DecisionType
    summary: str
    rationale: str
    confidence: float = 1.0
    evidence_ids: List[str] = Field(default_factory=list)
    next_action: str
    blocked_reasons: List[str] = Field(default_factory=list)

class ActionType(str, Enum):
    CREATE_PAYOUT = "CREATE_PAYOUT"
    GET_PAYOUT = "GET_PAYOUT"
    INITIATE_PAYMENT = "INITIATE_PAYMENT"
    VERIFY_PAYMENT = "VERIFY_PAYMENT"
    CREATE_JIRA_TASK = "CREATE_JIRA_TASK"
    UPDATE_JIRA_TASK = "UPDATE_JIRA_TASK"
    ADD_JIRA_COMMENT = "ADD_JIRA_COMMENT"
    CREATE_GMAIL_DRAFT = "CREATE_GMAIL_DRAFT"
    SEND_GMAIL_NOTIFICATION = "SEND_GMAIL_NOTIFICATION"
    POST_SLACK_UPDATE = "POST_SLACK_UPDATE"
    UPDATE_NOTION_RECORD = "UPDATE_NOTION_RECORD"
    CREATE_NOTION_RECORD = "CREATE_NOTION_RECORD"
    ESCALATE_EXCEPTION = "ESCALATE_EXCEPTION"

class ActionStatus(str, Enum):
    PLANNED = "PLANNED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class ActionItem(BaseModel):
    id: str
    action_type: ActionType
    provider: str
    canonical_tool_id: str
    payload: Dict[str, Any]
    status: ActionStatus = ActionStatus.PLANNED
    result_summary: str = ""
    error_message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

class AuditActor(str, Enum):
    AGENT = "AGENT"
    HUMAN_APPROVER = "HUMAN_APPROVER"
    SYSTEM = "SYSTEM"

class AuditEvent(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    actor: AuditActor
    event_type: str
    details: Dict[str, Any]
    reference_ids: List[str] = Field(default_factory=list)

class AgentEventType(str, Enum):
    RUN_STARTED = "run.started"
    AGENT_STEP = "agent.step"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    EVIDENCE_ADDED = "evidence.added"
    DECISION_CREATED = "decision.created"
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_RECEIVED = "approval.received"
    APPROVAL_REJECTED = "approval.rejected"
    EXECUTION_LOCKED = "execution.locked"
    ACTION_STARTED = "action.started"
    ACTION_COMPLETED = "action.completed"
    VERIFICATION_STARTED = "verification.started"
    EXCEPTION_DETECTED = "exception.detected"
    RECOVERY_STARTED = "recovery.started"
    RECONCILIATION_COMPLETED = "reconciliation.completed"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"

class AgentEvent(BaseModel):
    event_id: str
    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    event_type: AgentEventType
    step_name: Optional[str] = None
    provider: Optional[str] = None
    canonical_tool_id: Optional[str] = None
    status: Optional[str] = None
    duration_ms: Optional[int] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    decision_effect: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class RunRequest(BaseModel):
    prompt: str = "Handle the Zelar payment."
    scenario_id: Optional[str] = "scenario_1_success"
    demo_mode: bool = True
    auto_approve: bool = False

class ApprovalRequest(BaseModel):
    approved: bool = True
    comment: Optional[str] = None
    approver_name: str = "Finance Director (Human)"

class ScenarioDefinition(BaseModel):
    id: str
    title: str
    description: str
    prompt: str
    expected_outcome: str
    difficulty: str
    tags: List[str] = Field(default_factory=list)

class RunSummaryResponse(BaseModel):
    run_id: str
    user_request: str
    scenario_id: Optional[str]
    status: str
    payment_state: PaymentLifecycleState
    customer: str
    vendor: str
    invoice: str
    amount: float
    currency: str
    decision_summary: str
    created_at: str
    updated_at: str
