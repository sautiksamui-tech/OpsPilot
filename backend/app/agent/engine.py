import re
import uuid
import datetime
from typing import Any, Dict, List, Optional, Tuple
from ..models.schema import (
    DecisionType,
    DecisionObject,
    ActionType,
    ActionStatus,
    ActionItem,
    PaymentLifecycleState,
    AuditEvent,
    AuditActor,
    OperationType,
)

class OpsPilotEngine:
    """
    Core AI Decision, Planning & Exception Reasoning Engine for Vendor Settlements.
    """

    @staticmethod
    def analyze_intent(user_request: str, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses intent, target vendor, amount, invoice hints from natural language.
        """
        text = user_request.lower()
        
        # Vendor detection
        vendor = "Zelar"
        if "zelar" in text:
            vendor = "Zelar"
        elif "stripe" in text and "vendor" in text:
            vendor = "Stripe Vendor"

        # Explicit amount regex (e.g., ₹2,80,000 or 280000 or 2.4L or ₹2,40,000)
        amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', user_request, re.IGNORECASE)
        amount_override = None
        if amount_match:
            raw_val = amount_match.group(1).replace(",", "")
            try:
                val = float(raw_val)
                if val > 100:
                    amount_override = val
            except ValueError:
                pass

        # Scenario 4 amount mismatch simulation
        if scenario_id == "scenario_4_mismatch" and not amount_override:
            amount_override = 280000.0

        return {
            "customer": "Thoughtworks",
            "vendor": vendor,
            "purpose": "March Cloud Infrastructure & DevOps Services",
            "explicit_amount": amount_override,
            "currency": "INR",
            "operation_type": OperationType.VENDOR_PAYOUT.value,
        }

    @staticmethod
    def select_next_tool(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Dynamically selects the next Swytchcode tool to gather missing evidence.
        Investigation priority: Notion -> Stripe Customer -> Stripe Payments -> Slack -> Jira
        """
        missing = state.get("missing_information", [])
        vendor = state.get("vendor", "Zelar")

        if "vendor_invoice_record" in missing:
            return {
                "provider": "Notion",
                "canonical_id": "notion.search.create",
                "purpose": f"Search Notion operational knowledge layer for '{vendor}' profile, verified payout destination, and approved invoices.",
                "reasoning": f"Need baseline business context, verified invoice number, approved PO amount, and verified bank destination for vendor {vendor}.",
            }

        if "stripe_financial_state" in missing:
            customer_id = state.get("business_context", {}).get("vendor_profile", {}).get("stripe_customer_id", "cus_ZelarTech_99812")
            return {
                "provider": "Stripe",
                "canonical_id": "stripe.customer.get",
                "inputs": {"customer_id": customer_id},
                "purpose": f"Verify Stripe vendor account '{customer_id}' and delinquency status.",
                "reasoning": "Need to confirm active corporate payment recipient and financial standing on Stripe rails.",
            }

        if "stripe_payment_history" in missing:
            customer_id = state.get("business_context", {}).get("vendor_profile", {}).get("stripe_customer_id", "cus_ZelarTech_99812")
            return {
                "provider": "Stripe",
                "canonical_id": "stripe.payment_intent.list",
                "inputs": {"customer_id": customer_id},
                "purpose": "Inspect prior Stripe settlement history to verify payment cadence and prevent collision.",
                "reasoning": "Must verify no duplicate payout or settlement intent has already been initiated for the active billing cycle.",
            }

        if "internal_finance_chatter" in missing:
            return {
                "provider": "Slack",
                "canonical_id": "slack.search.message.list",
                "inputs": {"query": f"{vendor} invoice approval"},
                "purpose": "Scan Slack #finance-ops channel for director greenlight or operational payment holds.",
                "reasoning": "Check for internal team discussions, approvals, or operational freezes before requesting payout authorization.",
            }

        if "jira_operational_issue" in missing:
            return {
                "provider": "Jira",
                "canonical_id": "jira.api.jql.list",
                "inputs": {"jql": f"project = SCRUM AND text ~ '{vendor}'"},
                "purpose": f"Query Jira for existing vendor settlement task related to {vendor}.",
                "reasoning": "Link operational tracking task to prevent duplicate Jira ticket creation across systems.",
            }

        return None

    @staticmethod
    def synthesize_and_decide(state: Dict[str, Any]) -> DecisionObject:
        """
        Evaluates collected multi-system evidence and produces an actionable structured decision.
        """
        evidence_list = state.get("evidence", [])
        evidence_ids = [e["id"] for e in evidence_list if "id" in e]
        vendor = state.get("vendor", "Zelar")
        invoice_num = state.get("invoice", "ZELAR-MAR-2026-104")
        invoice_amount = state.get("amount", 240000.0)
        explicit_requested_amount = state.get("business_context", {}).get("explicit_amount")
        destination = state.get("verified_payout_destination")
        is_dest_verified = state.get("is_destination_verified", False)

        # 1. AMOUNT MISMATCH CHECK (e.g. Scenario 4)
        if explicit_requested_amount and abs(explicit_requested_amount - invoice_amount) > 1.0:
            variance = explicit_requested_amount - invoice_amount
            summary = (
                f"DISCREPANCY DETECTED: Requested payout of ₹{explicit_requested_amount:,.2f} does not match "
                f"approved Notion invoice {invoice_num} (₹{invoice_amount:,.2f}). Variance: ₹{variance:,.2f}."
            )
            return DecisionObject(
                decision=DecisionType.BLOCK_PAYMENT_DISCREPANCY,
                summary=summary,
                rationale="Enterprise compliance prohibits executing payouts with unapproved amount variances. Escalating to Jira and Finance.",
                confidence=1.0,
                evidence_ids=evidence_ids,
                next_action="block_and_escalate_reconciliation",
                blocked_reasons=[
                    f"Amount requested (₹{explicit_requested_amount:,.2f}) > Approved PO amount (₹{invoice_amount:,.2f})",
                    "Unauthorized variance requires Finance Director re-approval",
                ],
            )

        # 2. DESTINATION VERIFICATION CHECK (Security Gate)
        if not destination or not is_dest_verified or not destination.startswith("ba_"):
            return DecisionObject(
                decision=DecisionType.BLOCK_UNVERIFIED_DESTINATION,
                summary=f"PAYOUT BLOCKED: Destination account '{destination}' is not verified in master vendor registry.",
                rationale="AI Safety rule: Outbound payouts strictly require a verified external bank account from the verified vendor profile.",
                confidence=1.0,
                evidence_ids=evidence_ids,
                next_action="block_unverified_destination",
                blocked_reasons=["Unverified or missing payout destination in Notion vendor master"],
            )

        # 3. PAYMENT HOLD CHECK
        slack_context = state.get("communication_context", {}).get("slack", {})
        if slack_context.get("has_payment_hold"):
            return DecisionObject(
                decision=DecisionType.BLOCK_PAYMENT_DISCREPANCY,
                summary=f"PAYOUT BLOCKED: Active operational payment hold detected in Slack #finance-ops for {vendor}.",
                rationale="Internal team chatter indicates an unresolved operational hold.",
                confidence=0.95,
                evidence_ids=evidence_ids,
                next_action="block_and_notify_hold",
                blocked_reasons=["Active payment hold in #finance-ops"],
            )

        # 4. STANDARD VALID APPROVED PATH
        summary = (
            f"All business records verified. Invoice {invoice_num} for ₹{invoice_amount:,.2f} is approved by Finance. "
            f"Verified bank destination '{destination}'. Ready for explicit human authorization."
        )
        return DecisionObject(
            decision=DecisionType.PROCEED_TO_APPROVAL,
            summary=summary,
            rationale=f"Notion PO approved, verified destination {destination}, Slack confirmed no holds, Jira SCRUM-42 identified.",
            confidence=1.0,
            evidence_ids=evidence_ids,
            next_action="request_human_authorization",
        )

    @staticmethod
    def plan_actions(state: Dict[str, Any], decision: DecisionObject) -> List[ActionItem]:
        """
        Creates the sequenced action plan based on the synthesized decision.
        """
        actions: List[ActionItem] = []
        vendor = state.get("vendor", "Zelar")
        vendor_id = state.get("vendor_id", "VEND-ZELAR-009")
        invoice = state.get("invoice", "ZELAR-MAR-2026-104")
        po_id = state.get("po_id", "PO-TW-2026-0881")
        amount = state.get("amount", 240000.0)
        currency = state.get("currency", "INR")
        destination = state.get("verified_payout_destination", "ba_zelar_corp_hdfc_0981")
        operation_id = state.get("operation_id", "op_zelar_mar2026_104")
        jira_key = state.get("engineering_context", {}).get("jira", {}).get("existing_key", "SCRUM-42")

        if decision.decision == DecisionType.PROCEED_TO_APPROVAL:
            # Plan 1: Execute Payout
            actions.append(
                ActionItem(
                    id="act_payout_01",
                    action_type=ActionType.CREATE_PAYOUT,
                    provider="Stripe",
                    canonical_tool_id="stripe.payout.create",
                    payload={
                        "amount": int(round(amount * 100)),
                        "currency": currency.lower(),
                        "destination": destination,
                        "description": f"Vendor Settlement: {invoice} ({vendor})",
                        "metadata": {
                            "opspilot_operation_id": operation_id,
                            "vendor_id": vendor_id,
                            "po_id": po_id,
                            "invoice_id": invoice,
                        },
                    },
                    status=ActionStatus.PLANNED,
                    result_summary=f"Initiate vendor payout of ₹{amount:,.2f} to {destination} for {invoice}.",
                )
            )
            # Plan 2: Verify Payout Status
            actions.append(
                ActionItem(
                    id="act_verify_02",
                    action_type=ActionType.GET_PAYOUT,
                    provider="Stripe",
                    canonical_tool_id="stripe.payout.get",
                    payload={"payout": f"po_{operation_id}"},
                    status=ActionStatus.PLANNED,
                    result_summary="Verify terminal payout status on Stripe via stripe.payout.get.",
                )
            )
            # Plan 3: Update Jira Task
            actions.append(
                ActionItem(
                    id="act_jira_03",
                    action_type=ActionType.UPDATE_JIRA_TASK,
                    provider="Jira",
                    canonical_tool_id="jira.api.issue.update",
                    payload={"key": jira_key, "summary": f"Process Vendor Settlement: {vendor} ({invoice}) - Settled"},
                    status=ActionStatus.PLANNED,
                    result_summary=f"Update existing Jira task {jira_key} to avoid duplicates.",
                )
            )
            # Plan 4: Send Gmail Remittance Advice
            actions.append(
                ActionItem(
                    id="act_gmail_04",
                    action_type=ActionType.SEND_GMAIL_NOTIFICATION,
                    provider="Gmail",
                    canonical_tool_id="gmail.user.send.create",
                    payload={"recipient": "billing@zelar.io", "subject": f"Remittance Advice: Invoice {invoice}"},
                    status=ActionStatus.PLANNED,
                    result_summary=f"Send plain-language remittance email to vendor at billing@{vendor.lower()}.io.",
                )
            )
            # Plan 5: Post Slack Update
            actions.append(
                ActionItem(
                    id="act_slack_05",
                    action_type=ActionType.POST_SLACK_UPDATE,
                    provider="Slack",
                    canonical_tool_id="slack.chat.postmessage.create",
                    payload={"channel": "#finance-ops", "message": f"OpsPilot update: {vendor} vendor settlement ₹{amount/100000:,.1f}L settled to {destination}."},
                    status=ActionStatus.PLANNED,
                    result_summary="Post concise settlement notification to Slack #finance-ops.",
                )
            )
            # Plan 6: Record in Notion
            actions.append(
                ActionItem(
                    id="act_notion_06",
                    action_type=ActionType.UPDATE_NOTION_RECORD,
                    provider="Notion",
                    canonical_tool_id="notion.page.create",
                    payload={"vendor": vendor, "invoice": invoice, "amount": amount, "destination": destination},
                    status=ActionStatus.PLANNED,
                    result_summary="Record complete operational outcome and audit metadata in Notion.",
                )
            )

        elif decision.decision in (DecisionType.BLOCK_PAYMENT_DISCREPANCY, DecisionType.BLOCK_UNVERIFIED_DESTINATION):
            actions.append(
                ActionItem(
                    id="act_jira_block_01",
                    action_type=ActionType.CREATE_JIRA_TASK,
                    provider="Jira",
                    canonical_tool_id="jira.api.issue.create",
                    payload={"summary": f"Vendor Settlement Discrepancy: {vendor} - {invoice}"},
                    status=ActionStatus.PLANNED,
                    result_summary="Create Jira reconciliation task for Finance audit.",
                )
            )
            actions.append(
                ActionItem(
                    id="act_slack_block_02",
                    action_type=ActionType.POST_SLACK_UPDATE,
                    provider="Slack",
                    canonical_tool_id="slack.chat.postmessage.create",
                    payload={"channel": "#finance-ops", "message": f"🚨 OpsPilot Alert: Blocked payout to {vendor} ({decision.summary})."},
                    status=ActionStatus.PLANNED,
                    result_summary="Alert Finance team in Slack regarding blocked transaction.",
                )
            )
            actions.append(
                ActionItem(
                    id="act_notion_block_03",
                    action_type=ActionType.UPDATE_NOTION_RECORD,
                    provider="Notion",
                    canonical_tool_id="notion.page.create",
                    payload={"vendor": vendor, "invoice": invoice, "status": "BLOCKED_DISCREPANCY"},
                    status=ActionStatus.PLANNED,
                    result_summary="Log safety block in Notion audit log.",
                )
            )

        return actions

    @staticmethod
    def handle_exception_recovery(
        state: Dict[str, Any], payout_result: Dict[str, Any]
    ) -> Tuple[str, List[ActionItem], str]:
        """
        Analyzes payout outcome and constructs safe exception recovery plan.
        Returns: (new_payment_state: str, recovery_actions: List[ActionItem], explanation: str)
        """
        payment_state = payout_result.get("payment_state", PaymentLifecycleState.FAILED.value)
        payout_id = payout_result.get("payout_id", "po_zelar_mar2026_timeout_recon")
        vendor = state.get("vendor", "Zelar")
        invoice = state.get("invoice", "ZELAR-MAR-2026-104")
        amount = state.get("amount", 240000.0)
        jira_key = state.get("engineering_context", {}).get("jira", {}).get("existing_key", "SCRUM-42")

        recovery_actions: List[ActionItem] = []

        # Case A: FAILED (Destination bank error)
        if payment_state == PaymentLifecycleState.FAILED.value:
            explanation = (
                f"Payout execution FAILED with error code '{payout_result.get('error_code')}'. "
                f"Initiating operational recovery: Updating Jira task {jira_key}, alerting Finance in Slack, "
                f"and logging failure record in Notion without blind retries."
            )
            recovery_actions.append(
                ActionItem(
                    id="rec_jira_01",
                    action_type=ActionType.ADD_JIRA_COMMENT,
                    provider="Jira",
                    canonical_tool_id="jira.api.comment.create",
                    payload={"key": jira_key, "comment": f"Payout FAILED: {payout_result.get('failure_message')}."},
                    status=ActionStatus.PLANNED,
                    result_summary=f"Add failure diagnosis comment to Jira {jira_key}.",
                )
            )
            recovery_actions.append(
                ActionItem(
                    id="rec_slack_02",
                    action_type=ActionType.POST_SLACK_UPDATE,
                    provider="Slack",
                    canonical_tool_id="slack.chat.postmessage.create",
                    payload={"channel": "#finance-ops", "message": f"⚠️ Payout Failed for {vendor} (₹{amount:,.2f}): {payout_result.get('failure_message')}."},
                    status=ActionStatus.PLANNED,
                    result_summary="Notify Finance channel of payout failure.",
                )
            )
            recovery_actions.append(
                ActionItem(
                    id="rec_notion_03",
                    action_type=ActionType.UPDATE_NOTION_RECORD,
                    provider="Notion",
                    canonical_tool_id="notion.page.create",
                    payload={"vendor": vendor, "invoice": invoice, "status": "PAYOUT_FAILED"},
                    status=ActionStatus.PLANNED,
                    result_summary="Record failed transaction diagnostics in Notion.",
                )
            )
            return PaymentLifecycleState.FAILED.value, recovery_actions, explanation

        # Case B: UNKNOWN STATE (Gateway Timeout)
        elif payment_state == PaymentLifecycleState.UNKNOWN.value:
            explanation = (
                "Payout status is UNKNOWN due to gateway timeout. Distinguishing UNKNOWN from FAILED. "
                "CRITICAL SAFETY RULE: Prohibiting duplicate payout creation retry. Querying Stripe via stripe.payout.get."
            )
            # Safe recovery step: query stripe.payout.get with known payout ID
            recovery_actions.append(
                ActionItem(
                    id="rec_verify_timeout_01",
                    action_type=ActionType.GET_PAYOUT,
                    provider="Stripe",
                    canonical_tool_id="stripe.payout.get",
                    payload={"payout": payout_id},
                    status=ActionStatus.PLANNED,
                    result_summary=f"Query stripe.payout.get for {payout_id} to resolve timeout ambiguity safely.",
                )
            )
            recovery_actions.append(
                ActionItem(
                    id="rec_jira_timeout_02",
                    action_type=ActionType.ADD_JIRA_COMMENT,
                    provider="Jira",
                    canonical_tool_id="jira.api.comment.create",
                    payload={"key": jira_key, "comment": f"Gateway timeout during payout settlement. Reconciling transaction state with payout ID {payout_id} without duplicate payouts."},
                    status=ActionStatus.PLANNED,
                    result_summary="Log timeout reconciliation event in Jira.",
                )
            )
            recovery_actions.append(
                ActionItem(
                    id="rec_slack_timeout_03",
                    action_type=ActionType.POST_SLACK_UPDATE,
                    provider="Slack",
                    canonical_tool_id="slack.chat.postmessage.create",
                    payload={"channel": "#finance-ops", "message": f"⏳ OpsPilot reconciling {vendor} payout {payout_id} after gateway timeout. Duplicate prevention active."},
                    status=ActionStatus.PLANNED,
                    result_summary="Inform Finance team of timeout reconciliation protocol.",
                )
            )
            return PaymentLifecycleState.UNKNOWN.value, recovery_actions, explanation

        return payment_state, recovery_actions, "Payout succeeded normally."

engine = OpsPilotEngine()
