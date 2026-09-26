from typing import Any, Dict, List, Optional
from .swytchcode_client import swytchcode_client
from ..models.schema import EvidenceItem

class GmailToolAdapter:
    """
    Gmail External Communication Adapter via Swytchcode.
    Canonical IDs: gmail.user.drafts.create, gmail.user.send.create
    """

    @staticmethod
    def create_draft(
        recipient_email: str,
        subject: str,
        body_text: str,
        thread_id: Optional[str] = None,
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        canonical_id = "gmail.user.drafts.create"
        inputs = {
            "userId": "me",
            "body": {
                "message": {
                    "threadId": thread_id or "thread_zelar_inv_104",
                    "snippet": body_text[:120],
                }
            },
        }
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )

        draft_id = raw.get("id", "draft_new")
        return {
            "success": success,
            "duration_ms": duration_ms,
            "draft_id": draft_id,
            "draft": raw,
            "summary": f"Created remittance draft email for {recipient_email} ('{subject}').",
            "canonical_id": canonical_id,
            "raw": raw,
        }

    @staticmethod
    def create_draft_remittance(
        vendor_email: str,
        vendor_name: str,
        invoice_number: str,
        amount: float,
        currency: str,
        payment_intent_id: str,
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        subject = f"Remittance Advice: Invoice {invoice_number} - {vendor_name}"
        body = (
            f"Dear {vendor_name} Accounts Team,\n\n"
            f"We have processed the vendor settlement of ₹{amount:,.2f} {currency} for invoice {invoice_number}.\n"
            f"Stripe Payout Reference: {payment_intent_id}\n\n"
            f"Regards,\nThoughtworks Finance Operations"
        )
        return GmailToolAdapter.create_draft(
            recipient_email=vendor_email,
            subject=subject,
            body_text=body,
            demo_mode=demo_mode,
            scenario_id=scenario_id,
        )

    @staticmethod
    def send_draft(
        draft_id: str,
        recipient_email: str = "billing@zelar.io",
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        canonical_id = "gmail.user.send.create"
        inputs = {
            "userId": "me",
            "body": {
                "id": draft_id,
            },
        }
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )

        msg_id = raw.get("id", "msg_sent")
        return {
            "success": success,
            "duration_ms": duration_ms,
            "message_id": msg_id,
            "summary": f"Sent formal payment remittance email to vendor at {recipient_email} (Msg ID: {msg_id}).",
            "canonical_id": canonical_id,
            "raw": raw,
        }
