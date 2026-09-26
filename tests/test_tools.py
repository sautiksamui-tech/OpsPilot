import pytest
from backend.app.tools.notion import NotionToolAdapter
from backend.app.tools.stripe import StripeToolAdapter
from backend.app.tools.jira import JiraToolAdapter
from backend.app.tools.slack import SlackToolAdapter
from backend.app.tools.gmail import GmailToolAdapter
from backend.app.tools.registry import APPROVED_TOOLS

def test_approved_tools_count():
    assert len(APPROVED_TOOLS) == 17
    providers = {t.provider for t in APPROVED_TOOLS}
    assert providers == {"Notion", "Stripe", "Jira", "Slack", "Gmail"}

def test_notion_search_tool():
    res = NotionToolAdapter.search_business_records("Zelar", demo_mode=True)
    assert res["success"] is True
    assert res["vendor_data"]["vendor_name"] == "Zelar"
    assert res["vendor_data"]["verified_payout_destination"] == "ba_zelar_corp_hdfc_0981"
    assert res["invoice_data"]["invoice_number"] == "ZELAR-MAR-2026-104"
    assert res["invoice_data"]["amount"] == 240000.0

def test_stripe_tools():
    cust_res = StripeToolAdapter.get_customer("cus_ZelarTech_99812", demo_mode=True)
    assert cust_res["success"] is True
    assert cust_res["customer"]["id"] == "cus_ZelarTech_99812"

    pi_res = StripeToolAdapter.list_payment_intents("cus_ZelarTech_99812", demo_mode=True)
    assert pi_res["success"] is True
    assert len(pi_res["intents"]) >= 1

    payout_get = StripeToolAdapter.get_payout("po_zelar_mar2026_succ104", demo_mode=True)
    assert payout_get["success"] is True
    assert payout_get["canonical_id"] == "stripe.payout.get"

def test_jira_duplicate_prevention():
    search_res = JiraToolAdapter.search_issues("Zelar", demo_mode=True)
    assert search_res["success"] is True
    assert search_res["existing_issue"]["key"] == "SCRUM-42"

    # Updating with existing_key avoids creating a duplicate
    update_res = JiraToolAdapter.create_or_update_issue(
        summary="Process Vendor Settlement: Zelar",
        description="Updated",
        existing_key="SCRUM-42",
        demo_mode=True,
    )
    assert update_res["action"] == "UPDATED"
    assert update_res["key"] == "SCRUM-42"

def test_slack_and_gmail_tools():
    slack_res = SlackToolAdapter.search_finance_messages("Zelar", demo_mode=True)
    assert slack_res["success"] is True
    assert slack_res["has_payment_hold"] is False

    draft_res = GmailToolAdapter.create_draft("billing@zelar.io", "Remittance Advice", "Vendor payout ₹2.4L processed", demo_mode=True)
    assert draft_res["success"] is True
    assert "draft_id" in draft_res
