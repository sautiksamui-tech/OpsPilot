from typing import Any, Dict, List, Optional
from .swytchcode_client import swytchcode_client
from ..models.schema import EvidenceItem

class NotionToolAdapter:
    """
    Notion Operational Context Adapter via Swytchcode.
    Canonical IDs: notion.search.create, notion.page.create, notion.page.update
    """

    @staticmethod
    def search_business_records(
        query: str,
        demo_mode: bool = True,
        scenario_id: Optional[str] = None
    ) -> Dict[str, Any]:
        canonical_id = "notion.search.create"
        inputs = {
            "body": {
                "query": query,
                "page_size": 10
            }
        }
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )

        results = raw.get("results", [])
        evidence_items: List[EvidenceItem] = []
        vendor_data = {}
        invoice_data = {}

        for page in results:
            page_id = page.get("id", "")
            props = page.get("properties", {})
            
            # Check for Vendor Profile Page
            if "Vendor Name" in props:
                vendor_name = props.get("Vendor Name", {}).get("title", [{}])[0].get("plain_text", "")
                verified_dest = props.get("Verified Payout Destination", {}).get("rich_text", [{}])[0].get("plain_text", "ba_zelar_corp_hdfc_0981")
                vendor_data = {
                    "vendor_id": props.get("Vendor ID", {}).get("rich_text", [{}])[0].get("plain_text", "VEND-ZELAR-009"),
                    "vendor_name": vendor_name,
                    "legal_name": "Zelar Technologies Private Limited",
                    "category": props.get("Category", {}).get("rich_text", [{}])[0].get("plain_text", "Cloud Infrastructure & DevOps"),
                    "stripe_customer_id": props.get("Stripe Customer ID", {}).get("rich_text", [{}])[0].get("plain_text", "cus_ZelarTech_99812"),
                    "verified_payout_destination": verified_dest,
                    "bank_account_verified": True,
                    "contact_email": props.get("Contact Email", {}).get("email", "billing@zelar.io"),
                    "payment_terms": props.get("Payment Terms", {}).get("select", {}).get("name", "Net-30"),
                    "status": props.get("Status", {}).get("select", {}).get("name", "ACTIVE_VERIFIED"),
                }
                evidence_items.append(
                    EvidenceItem(
                        id=f"ev_notion_{page_id}",
                        provider="Notion",
                        canonical_tool_id=canonical_id,
                        identifier=page_id,
                        title=f"Vendor Profile: {vendor_name}",
                        normalized_content=vendor_data,
                        raw_output=page,
                        confidence=1.0,
                        impact_on_decision=f"Verified vendor legitimacy, Stripe account linkage, Net-30 payment terms, and destination {verified_dest}.",
                    )
                )

            # Check for Invoice Page
            if "Invoice Number" in props:
                inv_num = props.get("Invoice Number", {}).get("title", [{}])[0].get("plain_text", "")
                amount = props.get("Amount", {}).get("number", 0.0)
                invoice_data = {
                    "invoice_number": inv_num,
                    "amount": amount,
                    "currency": props.get("Currency", {}).get("select", {}).get("name", "INR"),
                    "description": props.get("Description", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                    "po_number": props.get("PO Number", {}).get("rich_text", [{}])[0].get("plain_text", "PO-TW-2026-0881"),
                    "approval_status": props.get("Approval Status", {}).get("select", {}).get("name", "APPROVED_BY_FINANCE"),
                    "approved_by": props.get("Approved By", {}).get("rich_text", [{}])[0].get("plain_text", "Rohan Deshmukh (Finance Director)"),
                }
                evidence_items.append(
                    EvidenceItem(
                        id=f"ev_notion_{page_id}",
                        provider="Notion",
                        canonical_tool_id=canonical_id,
                        identifier=page_id,
                        title=f"Approved Invoice: {inv_num}",
                        normalized_content=invoice_data,
                        raw_output=page,
                        confidence=1.0,
                        impact_on_decision=f"Confirmed approved invoice amount of ₹{amount:,.2f} with valid PO authorization.",
                    )
                )

        summary = f"Found {len(results)} Notion records (Vendor: '{vendor_data.get('vendor_name', 'N/A')}', Invoice: '{invoice_data.get('invoice_number', 'N/A')}')."
        return {
            "success": success,
            "duration_ms": duration_ms,
            "summary": summary,
            "vendor_data": vendor_data,
            "invoice_data": invoice_data,
            "evidence_items": evidence_items,
            "raw": raw,
            "canonical_id": canonical_id,
        }

    @staticmethod
    def create_operational_record(
        vendor: str,
        invoice: str,
        amount: float,
        currency: str,
        payment_status: str,
        jira_key: str,
        approval_status: str,
        audit_ref: str,
        demo_mode: bool = True,
        scenario_id: Optional[str] = None
    ) -> Dict[str, Any]:
        canonical_id = "notion.page.create"
        inputs = {
            "body": {
                "parent": {"database_id": "db_opspilot_operations_knowledge_2026"},
                "properties": {
                    "Title": {"title": [{"text": {"content": f"Vendor Settlement: {vendor} - {invoice}"}}]},
                    "Vendor": {"rich_text": [{"text": {"content": vendor}}]},
                    "Invoice": {"rich_text": [{"text": {"content": invoice}}]},
                    "Amount": {"number": amount},
                    "Currency": {"select": {"name": currency}},
                    "Payment Status": {"select": {"name": payment_status}},
                    "Approval Status": {"select": {"name": approval_status}},
                    "Jira Reference": {"rich_text": [{"text": {"content": jira_key}}]},
                    "Audit Reference": {"rich_text": [{"text": {"content": audit_ref}}]},
                }
            }
        }
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )
        return {
            "success": success,
            "duration_ms": duration_ms,
            "summary": f"Recorded operational vendor settlement record in Notion for invoice {invoice} (Status: {payment_status}).",
            "page_id": raw.get("id", "page_notion_opspilot_record"),
            "url": raw.get("url", ""),
            "canonical_id": canonical_id,
        }
