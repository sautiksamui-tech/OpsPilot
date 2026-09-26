import json
import subprocess
import time
import logging
from typing import Any, Dict, Optional, Tuple
from ..agent.scenarios import MOCK_DATA

logger = logging.getLogger("opspilot.swytchcode")

class SwytchcodeClient:
    """
    Swytchcode MCP & Kernel Execution Client.
    Delegates external API calls strictly through Swytchcode canonical IDs.
    """

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = workspace_dir

    def exec(
        self,
        canonical_id: str,
        inputs: Dict[str, Any],
        demo_mode: bool = True,
        scenario_id: Optional[str] = "scenario_1_success",
    ) -> Tuple[bool, Dict[str, Any], int, Optional[str]]:
        """
        Executes a canonical Swytchcode method.
        Returns: (success: bool, output: dict, duration_ms: int, error_category: Optional[str])
        """
        start_time = time.perf_counter()

        # In REAL mode, strictly execute via Swytchcode kernel and return real results/errors
        if not demo_mode:
            try:
                input_json = json.dumps(inputs)
                # Run swytchcode CLI with stdin redirection on Windows
                cmd = f'swytchcode exec {canonical_id} --input "{input_json}" < NUL'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=self.workspace_dir,
                    timeout=15,
                )
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                if result.returncode == 0:
                    try:
                        output = json.loads(result.stdout.strip())
                        return True, output, duration_ms, None
                    except json.JSONDecodeError:
                        return True, {"raw_output": result.stdout.strip()}, duration_ms, None
                else:
                    err_msg = result.stderr.strip() or result.stdout.strip()
                    category = "execution_error"
                    try:
                        err_obj = json.loads(err_msg)
                        category = err_obj.get("category", "execution_error")
                    except Exception:
                        if "auth" in err_msg.lower() or "unauthorized" in err_msg.lower():
                            category = "auth"
                        elif "not found" in err_msg.lower():
                            category = "not_found"
                        elif "policy" in err_msg.lower():
                            category = "policy_denied"

                    logger.error(f"Swytchcode live exec failed for {canonical_id} [{category}]: {err_msg}")
                    return False, {"error": err_msg, "category": category, "canonical_id": canonical_id}, duration_ms, category
            except Exception as e:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                logger.error(f"Live Swytchcode exec exception for {canonical_id}: {e}")
                return False, {"error": str(e), "category": "system_error", "canonical_id": canonical_id}, duration_ms, "system_error"

        # Deterministic schema-compliant simulator for DEMO mode and offline scenarios
        time.sleep(0.06)  # brief realistic latency
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        output = self._get_mock_output(canonical_id, inputs, scenario_id)
        return True, output, duration_ms, None

    def _get_mock_output(
        self, canonical_id: str, inputs: Dict[str, Any], scenario_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Returns authentic schema-compliant mock outputs corresponding exactly to Swytchcode info schemas.
        """
        # 1. NOTION METHODS
        if canonical_id == "notion.search.create":
            query = inputs.get("body", {}).get("query", "").lower() if isinstance(inputs.get("body"), dict) else ""
            if "zelar" in query or "invoice" in query or not query:
                return {
                    "results": [
                        {
                            "id": "page_notion_zelar_profile_01",
                            "object": "page",
                            "created_time": "2026-01-10T08:00:00.000Z",
                            "properties": {
                                "Vendor Name": {"title": [{"plain_text": MOCK_DATA["zelar_vendor_profile"]["vendor_name"]}]},
                                "Vendor ID": {"rich_text": [{"plain_text": MOCK_DATA["zelar_vendor_profile"]["vendor_id"]}]},
                                "Category": {"rich_text": [{"plain_text": MOCK_DATA["zelar_vendor_profile"]["category"]}]},
                                "Stripe Customer ID": {"rich_text": [{"plain_text": MOCK_DATA["zelar_vendor_profile"]["stripe_customer_id"]}]},
                                "Verified Payout Destination": {"rich_text": [{"plain_text": MOCK_DATA["zelar_vendor_profile"]["verified_payout_destination"]}]},
                                "Contact Email": {"email": MOCK_DATA["zelar_vendor_profile"]["contact_email"]},
                                "Status": {"select": {"name": MOCK_DATA["zelar_vendor_profile"]["status"]}},
                                "Payment Terms": {"select": {"name": MOCK_DATA["zelar_vendor_profile"]["payment_terms"]}},
                            },
                        },
                        {
                            "id": "page_notion_zelar_inv104_02",
                            "object": "page",
                            "created_time": "2026-03-15T09:00:00.000Z",
                            "properties": {
                                "Invoice Number": {"title": [{"plain_text": MOCK_DATA["zelar_invoice"]["invoice_number"]}]},
                                "Amount": {"number": MOCK_DATA["zelar_invoice"]["amount"]},
                                "Currency": {"select": {"name": MOCK_DATA["zelar_invoice"]["currency"]}},
                                "Description": {"rich_text": [{"plain_text": MOCK_DATA["zelar_invoice"]["description"]}]},
                                "PO Number": {"rich_text": [{"plain_text": MOCK_DATA["zelar_invoice"]["po_number"]}]},
                                "Approval Status": {"select": {"name": MOCK_DATA["zelar_invoice"]["approval_status"]}},
                                "Approved By": {"rich_text": [{"plain_text": MOCK_DATA["zelar_invoice"]["approver"]}]},
                            },
                        },
                    ],
                    "total": 2,
                    "has_more": False,
                }
            return {"results": [], "total": 0, "has_more": False}

        elif canonical_id in ("notion.page.create", "notion.page.update"):
            return {
                "id": "page_notion_opspilot_audit_9012",
                "object": "page",
                "created_time": "2026-03-26T11:45:00.000Z",
                "properties": inputs.get("body", {}).get("properties", {}),
                "url": "https://notion.so/thoughtworks/opspilot/record-9012",
                "status": "RECORDED",
            }

        # 2. STRIPE METHODS
        elif canonical_id == "stripe.customer.get":
            return MOCK_DATA["stripe_records"]["customer"]

        elif canonical_id == "stripe.customer.list":
            return {
                "object": "list",
                "data": [MOCK_DATA["stripe_records"]["customer"]],
                "has_more": False,
                "url": "/v1/customers",
            }

        elif canonical_id == "stripe.payment_intent.list":
            return {
                "object": "list",
                "data": MOCK_DATA["stripe_records"]["payment_intents_history"],
                "has_more": False,
                "url": "/v1/payment_intents",
            }

        elif canonical_id == "stripe.payout.create":
            if scenario_id == "scenario_2_failure":
                return MOCK_DATA["stripe_records"]["payout_failed"]
            elif scenario_id == "scenario_3_unknown_timeout":
                return {
                    "id": "po_zelar_mar2026_timeout_recon",
                    "object": "payout",
                    "amount": inputs.get("amount", 24000000),
                    "currency": inputs.get("currency", "inr"),
                    "destination": inputs.get("destination", "ba_zelar_corp_hdfc_0981"),
                    "status": "pending",
                    "arrival_date": 1742468000,
                    "method": "standard",
                    "created": 1742467200,
                    "metadata": inputs.get("metadata", {}),
                }
            return MOCK_DATA["stripe_records"]["payout_success"]

        elif canonical_id == "stripe.payout.get":
            payout_id = inputs.get("payout", "po_zelar_mar2026_timeout_recon")
            if "fail" in payout_id or scenario_id == "scenario_2_failure":
                return MOCK_DATA["stripe_records"]["payout_failed"]
            return MOCK_DATA["stripe_records"]["payout_pending_recon"]

        # 3. JIRA METHODS
        elif canonical_id in ("jira.api.jql.list", "jira.api.jql.create"):
            return {
                "startAt": 0,
                "maxResults": 50,
                "total": 1,
                "issues": [
                    {
                        "id": MOCK_DATA["jira_incident"]["id"],
                        "key": MOCK_DATA["jira_incident"]["key"],
                        "self": f"https://thoughtworks.atlassian.net/rest/api/3/issue/{MOCK_DATA['jira_incident']['id']}",
                        "fields": {
                            "summary": MOCK_DATA["jira_incident"]["summary"],
                            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": MOCK_DATA["jira_incident"]["description"]}]}]},
                            "status": {"name": MOCK_DATA["jira_incident"]["status"]},
                            "issuetype": {"name": MOCK_DATA["jira_incident"]["issue_type"]},
                            "priority": {"name": MOCK_DATA["jira_incident"]["priority"]},
                            "assignee": {"displayName": MOCK_DATA["jira_incident"]["assignee"]},
                            "reporter": {"displayName": MOCK_DATA["jira_incident"]["reporter"]},
                            "labels": MOCK_DATA["jira_incident"]["labels"],
                        },
                    }
                ],
            }

        elif canonical_id == "jira.api.issue.create":
            return {
                "id": "10043",
                "key": "SCRUM-43",
                "self": "https://thoughtworks.atlassian.net/rest/api/3/issue/10043",
                "status": "CREATED",
            }

        elif canonical_id == "jira.api.issue.update":
            return {"status": 204, "message": "Issue updated successfully"}

        elif canonical_id == "jira.api.comment.create":
            return {
                "id": "comment_501",
                "self": "https://thoughtworks.atlassian.net/rest/api/3/issue/10042/comment/comment_501",
                "body": inputs.get("body", {}),
                "created": "2026-03-26T11:46:00.000Z",
            }

        # 4. SLACK METHODS
        elif canonical_id == "slack.search.message.list":
            return {
                "ok": True,
                "query": inputs.get("query", ""),
                "messages": {
                    "total": len(MOCK_DATA["slack_finance_discussion"]["messages"]),
                    "matches": MOCK_DATA["slack_finance_discussion"]["messages"],
                },
            }

        elif canonical_id == "slack.chat.postmessage.create":
            body = inputs.get("body", {})
            return {
                "ok": True,
                "channel": body.get("channel", "C089FINOPS"),
                "ts": "1742468000.002200",
                "message": {
                    "text": body.get("text", ""),
                    "bot_id": "B_OPSPILOT_AI",
                    "type": "message",
                },
            }

        # 5. GMAIL METHODS
        elif canonical_id == "gmail.user.drafts.create":
            return {
                "id": "draft_g_99210",
                "message": {
                    "id": "msg_draft_99210",
                    "threadId": "thread_zelar_inv_104",
                    "labelIds": ["DRAFT"],
                    "snippet": "Remittance Advice: Vendor payout of ₹2,40,000 for Invoice ZELAR-MAR-2026-104 has been processed.",
                },
            }

        elif canonical_id == "gmail.user.send.create":
            return {
                "id": "msg_sent_99210",
                "threadId": "thread_zelar_inv_104",
                "labelIds": ["SENT"],
                "snippet": "Vendor payout remittance confirmed to billing@zelar.io.",
            }

        return {"status": "ok", "canonical_id": canonical_id, "data": inputs}

swytchcode_client = SwytchcodeClient()
