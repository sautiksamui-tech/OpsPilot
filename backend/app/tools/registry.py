from typing import Any, Dict, List
from pydantic import BaseModel

class ToolMetadata(BaseModel):
    canonical_id: str
    provider: str
    name: str
    description: str
    is_write: bool
    package: str
    auth_type: str

APPROVED_TOOLS: List[ToolMetadata] = [
    ToolMetadata(
        canonical_id="notion.search.create",
        provider="Notion",
        name="Search Notion Records",
        description="Search Notion workspace for vendor profiles, bank destinations, and purchase records.",
        is_write=False,
        package="Notion.notion@2.0.0",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="notion.page.create",
        provider="Notion",
        name="Create Notion Page",
        description="Create operational settlement knowledge records and audit entries.",
        is_write=True,
        package="Notion.notion@2.0.0",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="notion.page.update",
        provider="Notion",
        name="Update Notion Page",
        description="Update operational vendor settlement records with payout or exception status.",
        is_write=True,
        package="Notion.notion@2.0.0",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="stripe.payout.create",
        provider="Stripe",
        name="Create Stripe Payout",
        description="Disburse corporate funds to verified external vendor bank accounts for invoice settlement.",
        is_write=True,
        package="Stripe.stripe@2026-06-24.dahlia",
        auth_type="api_key (managed)",
    ),
    ToolMetadata(
        canonical_id="stripe.payout.get",
        provider="Stripe",
        name="Get Stripe Payout",
        description="Query settlement and delivery status of a known payout for safe reconciliation without duplicate retries.",
        is_write=False,
        package="Stripe.stripe@2026-06-24.dahlia",
        auth_type="api_key (managed)",
    ),
    ToolMetadata(
        canonical_id="stripe.customer.get",
        provider="Stripe",
        name="Get Stripe Customer",
        description="Retrieve verified vendor customer account details and delinquency status.",
        is_write=False,
        package="Stripe.stripe@2026-06-24.dahlia",
        auth_type="api_key (managed)",
    ),
    ToolMetadata(
        canonical_id="stripe.customer.list",
        provider="Stripe",
        name="List Stripe Customers",
        description="Query Stripe for customer accounts matching vendor identity.",
        is_write=False,
        package="Stripe.stripe@2026-06-24.dahlia",
        auth_type="api_key (managed)",
    ),
    ToolMetadata(
        canonical_id="stripe.payment_intent.list",
        provider="Stripe",
        name="List Settlement History",
        description="Inspect prior transactions to verify settlement history and prevent collision.",
        is_write=False,
        package="Stripe.stripe@2026-06-24.dahlia",
        auth_type="api_key (managed)",
    ),
    ToolMetadata(
        canonical_id="jira.api.jql.list",
        provider="Jira",
        name="Search Issues (JQL GET)",
        description="Search Jira operational issues and vendor settlement tasks using JQL.",
        is_write=False,
        package="Jira.jira@v1",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="jira.api.jql.create",
        provider="Jira",
        name="Search Issues (JQL POST)",
        description="Search Jira for issues using JQL structured payload.",
        is_write=False,
        package="Jira.jira@v1",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="jira.api.issue.create",
        provider="Jira",
        name="Create Jira Issue",
        description="Create new operational tasks or finance exception tickets.",
        is_write=True,
        package="Jira.jira@v1",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="jira.api.issue.update",
        provider="Jira",
        name="Update Jira Issue",
        description="Update existing Jira issues without creating duplicate tickets.",
        is_write=True,
        package="Jira.jira@v1",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="jira.api.comment.create",
        provider="Jira",
        name="Add Jira Comment",
        description="Append operational evidence and resolution notes to Jira issues.",
        is_write=True,
        package="Jira.jira@v1",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="slack.search.message.list",
        provider="Slack",
        name="Search Slack Messages",
        description="Search internal finance/ops channels for approvals and payment holds.",
        is_write=False,
        package="Slack.slack@1.7.0",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="slack.chat.postmessage.create",
        provider="Slack",
        name="Post Slack Message",
        description="Publish concise operational updates to internal team channels.",
        is_write=True,
        package="Slack.slack@1.7.0",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="gmail.user.drafts.create",
        provider="Gmail",
        name="Create Gmail Draft",
        description="Draft vendor remittance advice emails.",
        is_write=True,
        package="Gmail.gmail@v1",
        auth_type="oauth2 (managed)",
    ),
    ToolMetadata(
        canonical_id="gmail.user.send.create",
        provider="Gmail",
        name="Send Gmail Message",
        description="Send finalized remittance emails to vendors.",
        is_write=True,
        package="Gmail.gmail@v1",
        auth_type="oauth2 (managed)",
    ),
]

def get_tool_catalog() -> List[Dict[str, Any]]:
    return [tool.model_dump() for tool in APPROVED_TOOLS]
