import asyncio
import json
import uuid
import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse

from ..models.schema import (
    RunRequest,
    ApprovalRequest,
    RunSummaryResponse,
    ScenarioDefinition,
    PaymentLifecycleState,
    AgentEvent,
    AgentEventType,
    AuditEvent,
    AuditActor,
)
from ..agent.state import create_initial_state, OpsPilotState
from ..agent.graph import opspilot_app
from ..agent.scenarios import SCENARIOS
from ..tools.registry import get_tool_catalog
from ..db.database import db

router = APIRouter(prefix="/api")

async def run_agent_workflow(initial_state: OpsPilotState):
    """
    Executes the compiled LangGraph workflow asynchronously in the background.
    """
    run_id = initial_state["run_id"]
    current_state = initial_state
    db.save_run_state(current_state)

    try:
        # Run graph steps
        result = opspilot_app.invoke(current_state)
        db.save_run_state(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        current_state["status"] = "FAILED"
        current_state["errors"] = [str(e)]
        db.save_run_state(current_state)
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.RUN_FAILED,
                status="FAILED",
                output_summary=f"Graph execution failed: {e}",
            )
        )

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "app": "OpsPilot - AI Business Operator",
        "version": "1.0.0",
        "swytchcode_mcp": "connected",
        "providers_enabled": ["Notion", "Stripe", "Gmail", "Slack", "Jira"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

@router.get("/tools")
def list_tools():
    return {"tools": get_tool_catalog()}

@router.get("/scenarios", response_model=List[ScenarioDefinition])
def list_scenarios():
    return SCENARIOS

@router.post("/agent/run")
async def start_run(req: RunRequest, background_tasks: BackgroundTasks):
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    init_state = create_initial_state(
        run_id=run_id,
        user_request=req.prompt,
        scenario_id=req.scenario_id,
        demo_mode=req.demo_mode,
        auto_approve=req.auto_approve,
    )
    db.save_run_state(init_state)

    # Launch graph workflow in background
    background_tasks.add_task(run_agent_workflow, init_state)

    return {
        "run_id": run_id,
        "status": "STARTING",
        "user_request": req.prompt,
        "scenario_id": req.scenario_id,
    }

@router.get("/runs")
def list_runs():
    return db.list_runs()

@router.get("/runs/{run_id}")
def get_run(run_id: str):
    state = db.get_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return state

@router.get("/runs/{run_id}/events")
async def stream_events(run_id: str):
    """
    SSE stream endpoint for live real-time event delivery.
    """
    state = db.get_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    async def event_generator():
        queue = db.subscribe(run_id)
        try:
            # Yield any historical events first
            existing = db.get_events_for_run(run_id)
            for ev in existing:
                yield {
                    "event": "agent_event",
                    "data": json.dumps(ev),
                }

            # Then stream new events as they happen
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "agent_event",
                        "data": json.dumps(event),
                    }
                    if event.get("event_type") in (
                        AgentEventType.RUN_COMPLETED.value,
                        AgentEventType.RUN_FAILED.value,
                    ):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield {"event": "ping", "data": "{}"}
        finally:
            db.unsubscribe(run_id, queue)

    return EventSourceResponse(event_generator())

@router.post("/runs/{run_id}/approve")
async def approve_run(run_id: str, req: ApprovalRequest, background_tasks: BackgroundTasks):
    """
    Human Authorization Gate: unpauses and resumes graph execution.
    """
    state = db.get_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    valid_approval_states = (
        PaymentLifecycleState.APPROVAL_REQUIRED.value,
        PaymentLifecycleState.AWAITING_APPROVAL.value,
        "APPROVAL_REQUIRED",
        "AWAITING_APPROVAL",
    )
    if state.get("payment_state") not in valid_approval_states:
        raise HTTPException(
            status_code=400,
            detail=f"Run '{run_id}' is not currently awaiting approval (Current State: {state.get('payment_state')}).",
        )

    # Log approval audit
    audit = AuditEvent(
        id=f"aud_{uuid.uuid4().hex[:8]}",
        actor=AuditActor.HUMAN_APPROVER,
        event_type="VENDOR_SETTLEMENT_AUTHORIZED" if req.approved else "VENDOR_SETTLEMENT_REJECTED",
        details={
            "approver": req.approver_name,
            "approved": req.approved,
            "comment": req.comment,
            "amount": state.get("amount"),
            "vendor": state.get("vendor"),
            "invoice": state.get("invoice"),
            "destination": state.get("verified_payout_destination"),
            "operation_id": state.get("operation_id"),
        },
        reference_ids=[run_id],
    )
    db.log_audit(audit, run_id)

    event = AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        event_type=AgentEventType.APPROVAL_RECEIVED if req.approved else AgentEventType.APPROVAL_REJECTED,
        step_name="HUMAN_APPROVAL_GATE",
        status="APPROVED" if req.approved else "REJECTED",
        output_summary=f"Human Approver ({req.approver_name}): {'Authorized vendor payout' if req.approved else 'Rejected vendor payout'}.",
        decision_effect="Resuming execution towards Stripe payout settlement." if req.approved else "Execution cancelled.",
    )
    db.log_event(event)

    state["approval_status"] = "APPROVED" if req.approved else "REJECTED"
    state["approval_comment"] = req.comment
    state["payment_state"] = PaymentLifecycleState.HUMAN_APPROVED.value if req.approved else PaymentLifecycleState.CANCELLED.value
    state["status"] = "HUMAN_APPROVED" if req.approved else "CANCELLED"
    db.save_run_state(state)

    # Resume graph execution
    background_tasks.add_task(run_agent_workflow, state)

    return {"run_id": run_id, "status": state["status"], "payment_state": state["payment_state"]}

@router.post("/runs/{run_id}/reject")
async def reject_run(run_id: str, req: ApprovalRequest, background_tasks: BackgroundTasks):
    req.approved = False
    return await approve_run(run_id, req, background_tasks)

@router.get("/runs/{run_id}/audit")
def get_audit(run_id: str):
    logs = db.get_audit_logs_for_run(run_id)
    return {"run_id": run_id, "audit_trail": logs}
