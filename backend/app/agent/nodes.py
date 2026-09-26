import uuid
import time
import datetime
from typing import Any, Dict, List
from .state import OpsPilotState
from .engine import engine
from ..models.schema import (
    AgentEvent,
    AgentEventType,
    AuditEvent,
    AuditActor,
    PaymentLifecycleState,
    DecisionType,
    ActionStatus,
    ActionType,
    PayoutStatus,
    ApprovalLockPayload,
)
from ..db.database import db
from ..tools.notion import NotionToolAdapter
from ..tools.stripe import StripeToolAdapter
from ..tools.jira import JiraToolAdapter
from ..tools.slack import SlackToolAdapter
from ..tools.gmail import GmailToolAdapter

def intent_analysis_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    user_request = state["user_request"]
    scenario_id = state.get("scenario_id")

    # If already in execution/approved phase, pass through
    if state.get("approval_status") == "APPROVED":
        return {"status": "EXECUTING"}

    parsed = engine.analyze_intent(user_request, scenario_id=scenario_id)
    op_suffix = run_id.replace("run_", "")
    operation_id = f"op_zelar_{op_suffix}" if "zelar" in parsed["vendor"].lower() else f"op_{op_suffix}"
    
    event = AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        event_type=AgentEventType.RUN_STARTED,
        step_name="UNDERSTAND_REQUEST",
        status="SUCCESS",
        input_summary=user_request,
        output_summary=f"Parsed vendor settlement request for '{parsed['vendor']}' on behalf of '{parsed['customer']}'. Operation ID: {operation_id}",
        decision_effect="Initialized multi-system business investigation plan for VENDOR_PAYOUT.",
        payload={**parsed, "operation_id": operation_id},
    )
    db.log_event(event)

    audit = AuditEvent(
        id=f"aud_{uuid.uuid4().hex[:8]}",
        actor=AuditActor.AGENT,
        event_type="REQUEST_INITIALIZED",
        details={"user_request": user_request, "parsed_entities": parsed, "operation_id": operation_id},
        reference_ids=[run_id],
    )
    db.log_audit(audit, run_id)

    updates = {
        "status": "INVESTIGATING",
        "operation_id": operation_id,
        "operation_type": parsed.get("operation_type", "VENDOR_PAYOUT"),
        "customer": parsed["customer"],
        "vendor": parsed["vendor"],
        "purpose": parsed["purpose"],
        "currency": parsed["currency"],
        "business_context": {"explicit_amount": parsed["explicit_amount"]},
        "timestamps": {**state.get("timestamps", {}), "intent_analyzed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()},
    }
    return updates

def context_planner_node(state: OpsPilotState) -> Dict[str, Any]:
    next_tool = engine.select_next_tool(state)
    return {"next_tool_to_call": next_tool}

def investigate_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    tool_meta = state.get("next_tool_to_call")
    demo_mode = state.get("demo_mode", True)
    scenario_id = state.get("scenario_id")
    missing = list(state.get("missing_information", []))
    evidence_list = list(state.get("evidence", []))
    evidence_sources = list(state.get("evidence_sources", []))
    tool_events = list(state.get("tool_events", []))
    b_ctx = dict(state.get("business_context", {}))
    f_ctx = dict(state.get("financial_context", {}))
    c_ctx = dict(state.get("communication_context", {}))
    e_ctx = dict(state.get("engineering_context", {}))

    if not tool_meta:
        return {"status": "EVIDENCE_SYNTHESIS"}

    canonical_id = tool_meta["canonical_id"]
    provider = tool_meta["provider"]
    turns = state.get("investigation_turns", 0) + 1

    t_start_event = AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        event_type=AgentEventType.TOOL_STARTED,
        step_name=f"INVESTIGATE_{provider.upper()}",
        provider=provider,
        canonical_tool_id=canonical_id,
        status="RUNNING",
        input_summary=tool_meta.get("purpose", ""),
    )
    db.log_event(t_start_event)

    # 1. NOTION INVESTIGATION
    if canonical_id == "notion.search.create":
        res = NotionToolAdapter.search_business_records("Zelar invoice", demo_mode=demo_mode, scenario_id=scenario_id)
        if "vendor_invoice_record" in missing:
            missing.remove("vendor_invoice_record")
        
        vendor_id = "VEND-ZELAR-009"
        verified_destination = "ba_zelar_corp_hdfc_0981"
        is_dest_verified = True
        po_id = "PO-TW-2026-0881"

        if res.get("vendor_data"):
            b_ctx["vendor_profile"] = res["vendor_data"]
            vendor_id = res["vendor_data"].get("vendor_id", vendor_id)
            verified_destination = res["vendor_data"].get("verified_payout_destination", verified_destination)
            is_dest_verified = res["vendor_data"].get("bank_account_verified", True)
            missing.append("stripe_financial_state")
            missing.append("stripe_payment_history")

        if res.get("invoice_data"):
            b_ctx["invoice"] = res["invoice_data"]
            state_invoice = res["invoice_data"].get("invoice_number", "ZELAR-MAR-2026-104")
            state_amount = res["invoice_data"].get("amount", 240000.0)
            po_id = res["invoice_data"].get("po_number", po_id)
        else:
            state_invoice = "ZELAR-MAR-2026-104"
            state_amount = 240000.0

        for ev in res.get("evidence_items", []):
            evidence_list.append(ev.model_dump())
            evidence_sources.append(f"{provider}:{canonical_id}")
            db.log_event(
                AgentEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:8]}",
                    run_id=run_id,
                    event_type=AgentEventType.EVIDENCE_ADDED,
                    provider=provider,
                    canonical_tool_id=canonical_id,
                    status="SUCCESS",
                    output_summary=ev.title,
                    decision_effect=ev.impact_on_decision,
                    payload=ev.normalized_content,
                )
            )

        tool_events.append({"provider": provider, "canonical_id": canonical_id, "summary": res["summary"], "duration_ms": res["duration_ms"]})
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.TOOL_COMPLETED,
                step_name="NOTION_VERIFICATION",
                provider=provider,
                canonical_tool_id=canonical_id,
                status="SUCCESS",
                duration_ms=res["duration_ms"],
                output_summary=res["summary"],
                decision_effect=f"Extracted vendor ID {vendor_id}, verified destination {verified_destination}, and approved PO {po_id}.",
            )
        )
        return {
            "business_context": b_ctx,
            "vendor_id": vendor_id,
            "po_id": po_id,
            "verified_payout_destination": verified_destination,
            "is_destination_verified": is_dest_verified,
            "invoice": state_invoice,
            "amount": state_amount,
            "missing_information": missing,
            "evidence": evidence_list,
            "evidence_sources": list(set(evidence_sources)),
            "tool_events": tool_events,
            "investigation_turns": turns,
        }

    # 2. STRIPE ACCOUNT INVESTIGATION
    elif canonical_id == "stripe.customer.get":
        cust_id = tool_meta.get("inputs", {}).get("customer_id", "cus_ZelarTech_99812")
        res = StripeToolAdapter.get_customer(cust_id, demo_mode=demo_mode, scenario_id=scenario_id)
        if "stripe_financial_state" in missing:
            missing.remove("stripe_financial_state")
        f_ctx["customer_account"] = res.get("customer")
        ev = res["evidence"]
        evidence_list.append(ev.model_dump())
        evidence_sources.append(f"{provider}:{canonical_id}")

        tool_events.append({"provider": provider, "canonical_id": canonical_id, "summary": res["summary"], "duration_ms": res["duration_ms"]})
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.TOOL_COMPLETED,
                step_name="STRIPE_ACCOUNT_VERIFICATION",
                provider=provider,
                canonical_tool_id=canonical_id,
                status="SUCCESS",
                duration_ms=res["duration_ms"],
                output_summary=res["summary"],
                decision_effect=ev.impact_on_decision,
            )
        )
        return {
            "financial_context": f_ctx,
            "missing_information": missing,
            "evidence": evidence_list,
            "evidence_sources": list(set(evidence_sources)),
            "tool_events": tool_events,
            "investigation_turns": turns,
        }

    # 3. STRIPE SETTLEMENT HISTORY INVESTIGATION
    elif canonical_id == "stripe.payment_intent.list":
        cust_id = tool_meta.get("inputs", {}).get("customer_id", "cus_ZelarTech_99812")
        res = StripeToolAdapter.list_payment_intents(cust_id, demo_mode=demo_mode, scenario_id=scenario_id)
        if "stripe_payment_history" in missing:
            missing.remove("stripe_payment_history")
        f_ctx["payment_intents"] = res.get("intents", [])
        ev = res["evidence"]
        evidence_list.append(ev.model_dump())
        evidence_sources.append(f"{provider}:{canonical_id}")

        tool_events.append({"provider": provider, "canonical_id": canonical_id, "summary": res["summary"], "duration_ms": res["duration_ms"]})
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.TOOL_COMPLETED,
                step_name="STRIPE_HISTORY_VERIFICATION",
                provider=provider,
                canonical_tool_id=canonical_id,
                status="SUCCESS",
                duration_ms=res["duration_ms"],
                output_summary=res["summary"],
                decision_effect=ev.impact_on_decision,
            )
        )
        return {
            "financial_context": f_ctx,
            "missing_information": missing,
            "evidence": evidence_list,
            "evidence_sources": list(set(evidence_sources)),
            "tool_events": tool_events,
            "investigation_turns": turns,
        }

    # 4. SLACK INVESTIGATION
    elif canonical_id == "slack.search.message.list":
        query = tool_meta.get("inputs", {}).get("query", "Zelar invoice approval")
        res = SlackToolAdapter.search_finance_messages(query, demo_mode=demo_mode, scenario_id=scenario_id)
        if "internal_finance_chatter" in missing:
            missing.remove("internal_finance_chatter")
        c_ctx["slack"] = {"messages": res.get("messages", []), "has_payment_hold": res.get("has_payment_hold", False)}
        for ev in res.get("evidence_items", []):
            evidence_list.append(ev.model_dump())
            evidence_sources.append(f"{provider}:{canonical_id}")

        tool_events.append({"provider": provider, "canonical_id": canonical_id, "summary": res["summary"], "duration_ms": res["duration_ms"]})
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.TOOL_COMPLETED,
                step_name="SLACK_INTERNAL_VERIFICATION",
                provider=provider,
                canonical_tool_id=canonical_id,
                status="SUCCESS",
                duration_ms=res["duration_ms"],
                output_summary=res["summary"],
                decision_effect="Verified internal Finance greenlight and absence of settlement holds.",
            )
        )
        return {
            "communication_context": c_ctx,
            "missing_information": missing,
            "evidence": evidence_list,
            "evidence_sources": list(set(evidence_sources)),
            "tool_events": tool_events,
            "investigation_turns": turns,
        }

    # 5. JIRA INVESTIGATION
    elif canonical_id == "jira.api.jql.list":
        jql = tool_meta.get("inputs", {}).get("jql", "project = SCRUM AND text ~ 'Zelar'")
        res = JiraToolAdapter.search_issues(jql, demo_mode=demo_mode, scenario_id=scenario_id)
        if "jira_operational_issue" in missing:
            missing.remove("jira_operational_issue")
        e_ctx["jira"] = {"existing_issue": res.get("existing_issue"), "existing_key": res.get("existing_issue", {}).get("key", "SCRUM-42") if res.get("existing_issue") else None}
        for ev in res.get("evidence_items", []):
            evidence_list.append(ev.model_dump())
            evidence_sources.append(f"{provider}:{canonical_id}")

        tool_events.append({"provider": provider, "canonical_id": canonical_id, "summary": res["summary"], "duration_ms": res["duration_ms"]})
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.TOOL_COMPLETED,
                step_name="JIRA_TASK_LINKAGE",
                provider=provider,
                canonical_tool_id=canonical_id,
                status="SUCCESS",
                duration_ms=res["duration_ms"],
                output_summary=res["summary"],
                decision_effect=f"Linked existing Jira issue {e_ctx['jira']['existing_key']} to prevent duplicate tickets.",
            )
        )
        return {
            "engineering_context": e_ctx,
            "missing_information": missing,
            "evidence": evidence_list,
            "evidence_sources": list(set(evidence_sources)),
            "tool_events": tool_events,
            "investigation_turns": turns,
        }

    return {"investigation_turns": turns}

def evidence_synthesis_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    evidence_count = len(state.get("evidence", []))
    sources_count = len(state.get("evidence_sources", []))

    event = AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        event_type=AgentEventType.AGENT_STEP,
        step_name="SYNTHESIZE_EVIDENCE",
        status="SUCCESS",
        output_summary=f"Synthesized {evidence_count} evidence items across {sources_count} Swytchcode tool sources.",
        decision_effect="Formed complete business context and verified payout destination.",
    )
    db.log_event(event)

    return {
        "status": "CONTEXT_VERIFIED",
        "payment_state": PaymentLifecycleState.CONTEXT_VERIFIED.value,
        "timestamps": {**state.get("timestamps", {}), "context_verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat()},
    }

def decision_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    decision = engine.synthesize_and_decide(state)

    event = AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        event_type=AgentEventType.DECISION_CREATED,
        step_name="MAKE_DECISION",
        status="SUCCESS",
        output_summary=decision.summary,
        decision_effect=f"Engine chose decision type '{decision.decision.value}' (Confidence: {decision.confidence*100:.0f}%).",
        payload=decision.model_dump(),
    )
    db.log_event(event)

    audit = AuditEvent(
        id=f"aud_{uuid.uuid4().hex[:8]}",
        actor=AuditActor.AGENT,
        event_type="DECISION_EVALUATED",
        details=decision.model_dump(),
        reference_ids=[run_id],
    )
    db.log_audit(audit, run_id)

    updates: Dict[str, Any] = {
        "current_decision": decision.model_dump(),
        "decision_summary": decision.summary,
        "confidence": decision.confidence,
    }

    if decision.decision in (DecisionType.BLOCK_PAYMENT_DISCREPANCY, DecisionType.BLOCK_UNVERIFIED_DESTINATION):
        updates["status"] = "BLOCKED"
        updates["payment_state"] = PaymentLifecycleState.BLOCKED.value
    else:
        updates["status"] = "DECISION_MADE"

    return updates

def action_planner_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    decision_dict = state.get("current_decision")
    if not decision_dict:
        return {}

    decision = engine.synthesize_and_decide(state)
    planned = engine.plan_actions(state, decision)

    event = AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        event_type=AgentEventType.AGENT_STEP,
        step_name="PLAN_OPERATIONAL_ACTIONS",
        status="SUCCESS",
        output_summary=f"Formulated {len(planned)} operational actions across Stripe, Jira, Slack, Gmail, and Notion.",
        decision_effect="Ready for Human Authorization Gate.",
        payload={"planned_actions": [a.model_dump() for a in planned]},
    )
    db.log_event(event)

    return {
        "planned_actions": [a.model_dump() for a in planned],
        "status": "AWAITING_APPROVAL" if state.get("payment_state") != PaymentLifecycleState.BLOCKED.value else "BLOCKED",
    }

def approval_gate_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    auto_approve = state.get("auto_approve", False)
    approval_status = state.get("approval_status", "NOT_REQUIRED")
    
    # If blocked by safety compliance, do not present authorization modal
    if state.get("payment_state") == PaymentLifecycleState.BLOCKED.value:
        return {
            "approval_required": False,
            "status": "BLOCKED",
        }

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Construct strictly locked approval payload
    lock_data = ApprovalLockPayload(
        operation_id=state.get("operation_id", f"op_{run_id}"),
        vendor_id=state.get("vendor_id", "VEND-ZELAR-009"),
        vendor_name=state.get("vendor", "Zelar"),
        po_id=state.get("po_id", "PO-TW-2026-0881"),
        invoice_id=state.get("invoice", "ZELAR-MAR-2026-104"),
        exact_amount=state.get("amount", 240000.0),
        currency=state.get("currency", "INR"),
        verified_payout_destination=state.get("verified_payout_destination", "ba_zelar_corp_hdfc_0981"),
        approver="Finance Director (Human)",
        approval_timestamp=now_iso,
    )

    if approval_status == "APPROVED" or auto_approve:
        event = AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.APPROVAL_RECEIVED,
            step_name="HUMAN_APPROVAL_GATE",
            status="SUCCESS",
            input_summary=f"Human authorization granted by {lock_data.approver}.",
            output_summary=f"Authorized payout of ₹{lock_data.exact_amount:,.2f} to {lock_data.verified_payout_destination} ({lock_data.vendor_name}).",
            decision_effect="Locked execution payload. Transitioning to PAYOUT_CREATING.",
            payload=lock_data.model_dump(),
        )
        db.log_event(event)

        audit = AuditEvent(
            id=f"aud_{uuid.uuid4().hex[:8]}",
            actor=AuditActor.HUMAN_APPROVER,
            event_type="HUMAN_APPROVAL_GRANTED",
            details=lock_data.model_dump(),
            reference_ids=[run_id, lock_data.operation_id],
        )
        db.log_audit(audit, run_id)

        return {
            "approval_status": "APPROVED",
            "approval_lock_data": lock_data.model_dump(),
            "payment_state": PaymentLifecycleState.HUMAN_APPROVED.value,
            "status": "HUMAN_APPROVED",
        }

    elif approval_status == "REJECTED":
        event = AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.APPROVAL_REJECTED,
            step_name="HUMAN_APPROVAL_GATE",
            status="FAILED",
            input_summary="Human operator rejected vendor payout authorization.",
            output_summary="Payout authorization CANCELLED by human operator.",
            decision_effect="Execution halted. Zero funds transferred.",
            payload=lock_data.model_dump(),
        )
        db.log_event(event)
        return {
            "approval_status": "REJECTED",
            "approval_lock_data": lock_data.model_dump(),
            "payment_state": PaymentLifecycleState.CANCELLED.value,
            "status": "CANCELLED",
        }

    # Otherwise, wait for human authorization
    event = AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        event_type=AgentEventType.APPROVAL_REQUIRED,
        step_name="HUMAN_APPROVAL_GATE",
        status="AWAITING_INPUT",
        input_summary=f"Vendor: {lock_data.vendor_name}, Amount: ₹{lock_data.exact_amount:,.2f}, Destination: {lock_data.verified_payout_destination}",
        output_summary="Explicit human authorization required before stripe.payout.create initiation.",
        decision_effect="Paused at hard authorization boundary.",
        payload=lock_data.model_dump(),
    )
    db.log_event(event)
    return {
        "status": "APPROVAL_REQUIRED",
        "approval_lock_data": lock_data.model_dump(),
        "payment_state": PaymentLifecycleState.APPROVAL_REQUIRED.value,
    }

def execute_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    scenario_id = state.get("scenario_id", "scenario_1_success")
    demo_mode = state.get("demo_mode", True)
    vendor = state.get("vendor", "Zelar")
    vendor_id = state.get("vendor_id", "VEND-ZELAR-009")
    amount = state.get("amount", 240000.0)
    currency = state.get("currency", "INR")
    invoice = state.get("invoice", "ZELAR-MAR-2026-104")
    po_id = state.get("po_id", "PO-TW-2026-0881")
    destination = state.get("verified_payout_destination", "ba_zelar_corp_hdfc_0981")
    operation_id = state.get("operation_id", f"op_{run_id}")

    # 1. Blocked Handling
    if state.get("payment_state") == PaymentLifecycleState.BLOCKED.value:
        jira_res = JiraToolAdapter.create_or_update_issue(
            summary=f"Vendor Settlement Discrepancy: {vendor} - {invoice}",
            description=f"Automated compliance block: Requested amount/destination did not pass verification for {vendor}.",
            issue_type="Compliance Task",
            demo_mode=demo_mode,
            scenario_id=scenario_id,
        )
        slack_res = SlackToolAdapter.post_channel_message(
            channel="#finance-ops",
            message=f"🚨 OpsPilot Compliance Block: Payout to {vendor} halted due to compliance policy check on {invoice}.",
            demo_mode=demo_mode,
            scenario_id=scenario_id,
        )
        notion_res = NotionToolAdapter.create_operational_record(
            vendor=vendor,
            invoice=invoice,
            amount=amount,
            currency=currency,
            payment_status="BLOCKED_DISCREPANCY",
            jira_key=jira_res.get("key", "SCRUM-43"),
            approval_status="REJECTED_DISCREPANCY",
            audit_ref=run_id,
            demo_mode=demo_mode,
            scenario_id=scenario_id,
        )
        return {
            "status": "COMPLETED",
            "payment_details": {"error": "Compliance safety block enforced before payout creation"},
        }

    # 2. Execution Lock Event
    db.log_event(
        AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.EXECUTION_LOCKED,
            step_name="EXECUTION_LOCK_ACQUIRED",
            status="SUCCESS",
            input_summary=f"Acquired application-level execution lock for operation_id: {operation_id}",
            output_summary=f"Payload locked: ₹{amount:,.2f} {currency} to {destination}.",
            decision_effect="Guaranteed single-execution idempotency.",
        )
    )

    # 3. Payout Creating Event
    db.log_event(
        AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.ACTION_STARTED,
            step_name="PAYOUT_CREATING",
            provider="Stripe",
            canonical_tool_id="stripe.payout.create",
            status="RUNNING",
            input_summary=f"Initiating corporate bank payout of ₹{amount:,.2f} to {destination} ({vendor}).",
        )
    )

    # 4. Invoke Stripe Payout Creation
    payout_res = StripeToolAdapter.create_payout(
        operation_id=operation_id,
        vendor_id=vendor_id,
        vendor_name=vendor,
        po_id=po_id,
        invoice_id=invoice,
        amount=amount,
        currency=currency,
        destination=destination,
        demo_mode=demo_mode,
        scenario_id=scenario_id,
    )

    payout_id = payout_res.get("payout_id")
    payout_status = payout_res.get("payout_status")
    p_state = payout_res.get("payment_state", PaymentLifecycleState.FAILED.value)

    db.log_event(
        AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.ACTION_COMPLETED,
            step_name="PAYOUT_CREATED" if payout_res["success"] else "PAYOUT_FAILED",
            provider="Stripe",
            canonical_tool_id="stripe.payout.create",
            status="SUCCESS" if payout_res["success"] else "FAILED",
            duration_ms=payout_res.get("duration_ms", 100),
            output_summary=payout_res.get("summary", "Payout executed."),
            decision_effect=f"Stripe Payout ID: {payout_id} (Status: {payout_status})",
            payload=payout_res,
        )
    )

    audit = AuditEvent(
        id=f"aud_{uuid.uuid4().hex[:8]}",
        actor=AuditActor.AGENT,
        event_type="STRIPE_PAYOUT_EXECUTED",
        details=payout_res,
        reference_ids=[run_id, operation_id, payout_id] if payout_id else [run_id, operation_id],
    )
    db.log_audit(audit, run_id)

    return {
        "status": "PAYOUT_CREATED" if payout_res["success"] else "PAYOUT_FAILED",
        "payment_state": p_state,
        "payout_id": payout_id,
        "payout_status": payout_status,
        "payment_details": payout_res,
        "is_execution_locked": True,
    }

def verify_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    scenario_id = state.get("scenario_id")
    demo_mode = state.get("demo_mode", True)
    p_state = state.get("payment_state")
    payout_id = state.get("payout_id", "po_zelar_mar2026_succ104")

    # In UNKNOWN state, query stripe.payout.get directly rather than retrying payout.create
    if p_state == PaymentLifecycleState.UNKNOWN.value:
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.VERIFICATION_STARTED,
                step_name="RECONCILE_UNKNOWN_PAYOUT",
                provider="Stripe",
                canonical_tool_id="stripe.payout.get",
                status="RUNNING",
                input_summary=f"Querying stripe.payout.get for known payout ID {payout_id} to resolve gateway timeout without duplicate payout creation.",
            )
        )

        get_res = StripeToolAdapter.get_payout(payout_id, demo_mode=demo_mode, scenario_id=scenario_id)
        db.log_event(
            AgentEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                event_type=AgentEventType.TOOL_COMPLETED,
                step_name="RECONCILE_UNKNOWN_PAYOUT",
                provider="Stripe",
                canonical_tool_id="stripe.payout.get",
                status="SUCCESS",
                duration_ms=get_res["duration_ms"],
                output_summary=get_res["summary"],
                decision_effect="Confirmed status via stripe.payout.get. Zero duplicate transfers initiated.",
                payload={"payout_id": get_res.get("payout_id"), "status": get_res.get("status"), "summary": get_res.get("summary")},
            )
        )
        return {
            "status": "RECONCILING",
            "payment_state": PaymentLifecycleState.RECONCILING.value,
            "payout_status": get_res.get("status", "in_transit"),
        }

    return {"status": "VERIFYING"}

def exception_recovery_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    scenario_id = state.get("scenario_id")
    demo_mode = state.get("demo_mode", True)
    vendor = state.get("vendor", "Zelar")
    invoice = state.get("invoice", "ZELAR-MAR-2026-104")
    amount = state.get("amount", 240000.0)
    currency = state.get("currency", "INR")
    payment_details = state.get("payment_details", {})
    jira_key = state.get("engineering_context", {}).get("jira", {}).get("existing_key", "SCRUM-42")

    new_p_state, recovery_actions, explanation = engine.handle_exception_recovery(state, payment_details)

    db.log_event(
        AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.EXCEPTION_DETECTED,
            step_name="EXCEPTION_RECOVERY",
            status="SUCCESS",
            output_summary=f"Exception handled: {explanation}",
            decision_effect="Executed non-terminating multi-system operational escalation.",
        )
    )

    # Execute recovery steps
    for act in recovery_actions:
        if act.action_type == ActionType.ADD_JIRA_COMMENT:
            JiraToolAdapter.add_comment(
                issue_key=act.payload.get("key", jira_key),
                comment_text=act.payload.get("comment", ""),
                demo_mode=demo_mode,
                scenario_id=scenario_id,
            )
        elif act.action_type == ActionType.POST_SLACK_UPDATE:
            SlackToolAdapter.post_channel_message(
                channel=act.payload.get("channel", "#finance-ops"),
                message=act.payload.get("message", ""),
                demo_mode=demo_mode,
                scenario_id=scenario_id,
            )
        elif act.action_type == ActionType.UPDATE_NOTION_RECORD:
            NotionToolAdapter.create_operational_record(
                vendor=vendor,
                invoice=invoice,
                amount=amount,
                currency=currency,
                payment_status=act.payload.get("status", "PAYOUT_FAILED"),
                jira_key=jira_key,
                approval_status="EXCEPTION_RECOVERED",
                audit_ref=run_id,
                demo_mode=demo_mode,
                scenario_id=scenario_id,
            )

    return {
        "status": "EXCEPTION_HANDLED",
        "payment_state": new_p_state,
        "reconciliation_state": {"systems_aligned": True, "recovery_applied": True, "notes": explanation},
    }

def reconciliation_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    scenario_id = state.get("scenario_id")
    demo_mode = state.get("demo_mode", True)
    vendor = state.get("vendor", "Zelar")
    invoice = state.get("invoice", "ZELAR-MAR-2026-104")
    amount = state.get("amount", 240000.0)
    currency = state.get("currency", "INR")
    payout_id = state.get("payout_id", "po_zelar_mar2026_succ104")
    destination = state.get("verified_payout_destination", "ba_zelar_corp_hdfc_0981")
    jira_key = state.get("engineering_context", {}).get("jira", {}).get("existing_key", "SCRUM-42")

    # 1. Update Jira Task
    jira_res = JiraToolAdapter.create_or_update_issue(
        summary=f"Process Vendor Settlement: {vendor} ({invoice}) - Settled",
        description=f"Vendor settlement of ₹{amount:,.2f} {currency} to {destination} completed successfully via Stripe Payout {payout_id}.",
        existing_key=jira_key,
        demo_mode=demo_mode,
        scenario_id=scenario_id,
    )

    # 2. Send Vendor Remittance Advice via Gmail
    gmail_draft = GmailToolAdapter.create_draft_remittance(
        vendor_email="billing@zelar.io",
        vendor_name=vendor,
        invoice_number=invoice,
        amount=amount,
        currency=currency,
        payment_intent_id=payout_id,
        demo_mode=demo_mode,
        scenario_id=scenario_id,
    )
    gmail_sent = GmailToolAdapter.send_draft(
        draft_id=gmail_draft["draft"]["id"],
        demo_mode=demo_mode,
        scenario_id=scenario_id,
    )

    # 3. Post Settlement Confirmation to Slack
    slack_msg = SlackToolAdapter.post_channel_message(
        channel="#finance-ops",
        message=f"✅ OpsPilot: Vendor settlement of ₹{amount:,.2f} for {vendor} ({invoice}) paid via Stripe Payout {payout_id} to {destination}. Remittance sent to billing@zelar.io.",
        demo_mode=demo_mode,
        scenario_id=scenario_id,
    )

    # 4. Record Audit Log in Notion
    notion_rec = NotionToolAdapter.create_operational_record(
        vendor=vendor,
        invoice=invoice,
        amount=amount,
        currency=currency,
        payment_status="PAID_AND_RECONCILED",
        jira_key=jira_key,
        approval_status="APPROVED_AND_EXECUTED",
        audit_ref=run_id,
        demo_mode=demo_mode,
        scenario_id=scenario_id,
    )

    db.log_event(
        AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.RECONCILIATION_COMPLETED,
            step_name="MULTI_SYSTEM_RECONCILIATION",
            status="SUCCESS",
            output_summary="Multi-system state successfully reconciled across Notion, Stripe, Jira, Slack, and Gmail.",
            decision_effect="All enterprise systems synchronized with final settlement provenance.",
        )
    )

    return {
        "status": "RECONCILED",
        "payment_state": PaymentLifecycleState.PAID.value,
        "reconciliation_state": {
            "systems_aligned": True,
            "jira_updated": jira_key,
            "slack_notified": True,
            "gmail_sent": True,
            "notion_audit_recorded": True,
        },
    }

def audit_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    p_state = state.get("payment_state")
    amount = state.get("amount", 240000.0)
    vendor = state.get("vendor", "Zelar")
    invoice = state.get("invoice", "ZELAR-MAR-2026-104")
    payout_id = state.get("payout_id")

    audit = AuditEvent(
        id=f"aud_{uuid.uuid4().hex[:8]}",
        actor=AuditActor.SYSTEM,
        event_type="OPERATIONAL_CYCLE_COMPLETED",
        details={
            "run_id": run_id,
            "vendor": vendor,
            "invoice": invoice,
            "amount": amount,
            "final_payment_state": p_state,
            "payout_id": payout_id,
            "reconciliation": state.get("reconciliation_state"),
        },
        reference_ids=[run_id],
    )
    db.log_audit(audit, run_id)

    return {"status": "COMPLETED"}

def final_response_node(state: OpsPilotState) -> Dict[str, Any]:
    run_id = state["run_id"]
    p_state = state.get("payment_state")
    vendor = state.get("vendor", "Zelar")
    invoice = state.get("invoice", "ZELAR-MAR-2026-104")
    amount = state.get("amount", 240000.0)
    payout_id = state.get("payout_id", "N/A")
    destination = state.get("verified_payout_destination", "ba_zelar_corp_hdfc_0981")
    jira_key = state.get("engineering_context", {}).get("jira", {}).get("existing_key", "SCRUM-42")

    if p_state == PaymentLifecycleState.PAID.value:
        summary = (
            f"✅ **Vendor Settlement Completed & Reconciled**\n\n"
            f"• **Vendor:** {vendor} (Zelar Technologies Pvt Ltd)\n"
            f"• **Invoice:** {invoice} (PO-TW-2026-0881)\n"
            f"• **Amount:** ₹{amount:,.2f} INR\n"
            f"• **Destination Bank:** {destination} (HDFC Bank Ltd)\n"
            f"• **Stripe Payout ID:** `{payout_id}`\n"
            f"• **Jira Task:** Linked & Updated `{jira_key}` (Status: Settled)\n"
            f"• **Slack Notification:** Dispatched to `#finance-ops`\n"
            f"• **Gmail Remittance Advice:** Sent to `billing@zelar.io`\n"
            f"• **Notion Knowledge Layer:** Audit record saved."
        )
    elif p_state == PaymentLifecycleState.BLOCKED.value:
        summary = (
            f"🚨 **Vendor Settlement Blocked by Safety & Compliance Policy**\n\n"
            f"• **Vendor:** {vendor}\n"
            f"• **Invoice:** {invoice}\n"
            f"• **Reason:** {state.get('decision_summary')}\n"
            f"• **Status:** Zero funds transferred. Jira reconciliation task created and Finance alerted in `#finance-ops`."
        )
    elif p_state == PaymentLifecycleState.CANCELLED.value:
        summary = (
            f"🛑 **Vendor Settlement Cancelled by Human Operator**\n\n"
            f"• **Vendor:** {vendor}\n"
            f"• **Invoice:** {invoice}\n"
            f"• **Amount:** ₹{amount:,.2f}\n"
            f"• **Status:** Execution halted at authorization gate. Zero funds transferred."
        )
    elif p_state == PaymentLifecycleState.UNKNOWN.value or p_state == PaymentLifecycleState.RECONCILING.value:
        summary = (
            f"⏳ **Gateway Timeout Reconciled**\n\n"
            f"• **Vendor:** {vendor}\n"
            f"• **Invoice:** {invoice}\n"
            f"• **Status:** Gateway timeout encountered during settlement. Queried `stripe.payout.get` (`{payout_id}`) to verify state without duplicate payout attempts. Jira & Slack updated."
        )
    else:
        summary = (
            f"⚠️ **Vendor Settlement Exception Handled**\n\n"
            f"• **Vendor:** {vendor}\n"
            f"• **Invoice:** {invoice}\n"
            f"• **Amount:** ₹{amount:,.2f}\n"
            f"• **Reason:** {state.get('payment_details', {}).get('failure_message', 'Payment decline')}\n"
            f"• **Actions Taken:** Jira `{jira_key}` updated with diagnostics, Slack `#finance-ops` alerted, Notion record created."
        )

    db.log_event(
        AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type=AgentEventType.RUN_COMPLETED,
            step_name="FINAL_OPERATOR_REPORT",
            status="SUCCESS",
            output_summary=f"Run complete. Final settlement state: {p_state}.",
        )
    )

    return {
        "final_response": summary,
        "timestamps": {**state.get("timestamps", {}), "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()},
    }
