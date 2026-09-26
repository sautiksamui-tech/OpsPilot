# OpsPilot System Architecture

## Overview
**OpsPilot** is an Autonomous AI Business Operator engineered for enterprise B2B vendor payout operations, exception management, and multi-system reconciliation.

---

## High-Level System Architecture

```mermaid
flowchart TD
    User([Enterprise User / Ops Lead]) <--> Frontend[React 18 + Vite Console: Command View & Admin Console]
    Frontend <--> |REST & SSE Events| Backend[FastAPI Backend Server]
    
    subgraph Agentic Kernel [OpsPilot LangGraph Engine]
        Backend --> State[OpsPilotState TypedDict]
        State --> Intent[Intent Analysis]
        Intent --> DynamicLoop{Investigation Loop}
        DynamicLoop --> |Notion| NotionAdapter[Notion Adapter]
        DynamicLoop --> |Stripe| StripeAdapter[Stripe Adapter]
        DynamicLoop --> |Slack| SlackAdapter[Slack Adapter]
        DynamicLoop --> |Jira| JiraAdapter[Jira Adapter]
        
        NotionAdapter --> Evidence[Evidence Synthesis]
        StripeAdapter --> Evidence
        SlackAdapter --> Evidence
        JiraAdapter --> Evidence
        
        Evidence --> Decision[Decision Reasoner]
        Decision --> Planner[Action Planner]
        Planner --> Gate{Human Authorization Gate}
        
        Gate --> |Approved & Locked| Executor[Payout Execution: stripe.payout.create]
        Gate --> |Declined| Cancelled[Safe Cancellation]
        
        Executor --> Verifier[Payout State Verifier: stripe.payout.get]
        Verifier --> |Paid / Succeeded| Recon[Multi-System Reconciliation]
        Verifier --> |Failed / Timeout| ExceptionEngine[Exception Recovery Engine]
        
        Recon --> Audit[Audit Trail Vault & Notion Record]
        ExceptionEngine --> Audit
        Audit --> FinalResp[Final Response Generator]
    end
    
    subgraph Execution Boundary [Swytchcode MCP / Kernel]
        NotionAdapter <--> |notion.search.create / page.create| Swytchcode[(Swytchcode Kernel)]
        StripeAdapter <--> |stripe.payout.create / stripe.payout.get / customer.get| Swytchcode
        SlackAdapter <--> |slack.search.message.list / chat.postmessage.create| Swytchcode
        JiraAdapter <--> |jira.api.jql.list / issue.update / comment.create| Swytchcode
        GmailAdapter[Gmail Adapter] <--> |gmail.user.drafts.create / send.create| Swytchcode
    end

    subgraph Persistence [Persistence Layer]
        Backend <--> SQLite[(SQLite Database: Runs, Events, Audits)]
    end
```

---

## 5-Provider Swytchcode Integration Mapping

| Provider | Canonical Swytchcode Method | Read / Write | Business Operational Purpose |
| :--- | :--- | :--- | :--- |
| **Notion** | `notion.search.create`<br>`notion.page.create`<br>`notion.page.update` | Read<br>Write<br>Write | Verified vendor legal entity, PO terms (Net-30), verified bank destination, and approved invoice amount.<br>Creates persistent operational knowledge and audit records. |
| **Stripe** | `stripe.payout.create`<br>`stripe.payout.get`<br>`stripe.customer.get`<br>`stripe.customer.list`<br>`stripe.payment_intent.list` | Write<br>Read<br>Read<br>Read<br>Read | Executes outbound vendor payout directly from company balance to verified recipient bank account destination.<br>Polls payout lifecycle status and verifies customer profile history. |
| **Jira** | `jira.api.jql.list`<br>`jira.api.jql.create`<br>`jira.api.issue.create`<br>`jira.api.issue.update`<br>`jira.api.comment.create` | Read<br>Read<br>Write<br>Write<br>Write | Identifies existing payment incident `SCRUM-42` (preventing duplicate ticket creation) and records operational recovery tasks. |
| **Slack** | `slack.search.message.list`<br>`slack.chat.postmessage.create` | Read<br>Write | Searches internal `#finance-ops` channel for director greenlight and active holds.<br>Publishes concise operational settlement updates. |
| **Gmail** | `gmail.user.drafts.create`<br>`gmail.user.send.create` | Write<br>Write | Creates plain-language remittance advice email draft and transmits confirmation to vendor billing contact. |

---

## Strict 9-Stage Vendor Settlement Lifecycle

```mermaid
stateDiagram-v2
    [*] --> REQUESTED : Natural Language Request
    REQUESTED --> CONTEXT_VERIFIED : 5-Provider Evidence Synthesized
    CONTEXT_VERIFIED --> APPROVAL_REQUIRED : Locked Settlement Payload Constructed
    CONTEXT_VERIFIED --> BLOCKED : Amount Discrepancy / Active Hold
    
    APPROVAL_REQUIRED --> HUMAN_APPROVED : Human Operator Signature
    APPROVAL_REQUIRED --> CANCELLED : Operator Declined
    
    HUMAN_APPROVED --> EXECUTION_LOCKED : Idempotency Lock Enforced
    EXECUTION_LOCKED --> PAYOUT_CREATING : stripe.payout.create Invoked
    
    PAYOUT_CREATING --> PAYOUT_CREATED : Rails Acknowledged
    PAYOUT_CREATED --> RECONCILING : Multi-System Sync
    
    RECONCILING --> PAID : stripe.payout.get Confirmed Paid
    RECONCILING --> FAILED : Destination Bank Error
    RECONCILING --> UNKNOWN : Network / Timeout Exception
    
    UNKNOWN --> ExceptionEngine : Polling Query (stripe.payout.get) / Zero-Duplicate Rule
    FAILED --> ExceptionEngine : Jira Escalated & Slack Notified
    BLOCKED --> DiscrepancyHandling : Jira Reconciliation Created
    
    PAID --> MultiSystemReconciliation : Gmail + Jira + Slack + Notion
    MultiSystemReconciliation --> [*]
    ExceptionEngine --> [*]
    DiscrepancyHandling --> [*]
    CANCELLED --> [*]
```
