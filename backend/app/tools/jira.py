from typing import Any, Dict, List, Optional
from .swytchcode_client import swytchcode_client
from ..models.schema import EvidenceItem

class JiraToolAdapter:
    """
    Jira Operational Tasks & Exception Management Adapter via Swytchcode.
    Canonical IDs: jira.api.jql.list, jira.api.jql.create, jira.api.issue.create, jira.api.issue.update, jira.api.comment.create
    """

    @staticmethod
    def search_issues(
        jql: str = "project = SCRUM AND text ~ 'Zelar'",
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Searches Jira using JQL enhanced search (GET) - canonical: jira.api.jql.list
        """
        canonical_id = "jira.api.jql.list"
        inputs = {"jql": jql}
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )

        issues = raw.get("issues", [])
        evidence_items: List[EvidenceItem] = []
        existing_issue = None

        if issues:
            first_issue = issues[0]
            fields = first_issue.get("fields", {})
            existing_issue = {
                "key": first_issue.get("key"),
                "id": first_issue.get("id"),
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name", "In Progress"),
                "priority": fields.get("priority", {}).get("name", "High"),
                "assignee": fields.get("assignee", {}).get("displayName", "Unassigned"),
            }
            evidence_items.append(
                EvidenceItem(
                    id=f"ev_jira_{first_issue.get('key')}",
                    provider="Jira",
                    canonical_tool_id=canonical_id,
                    identifier=first_issue.get("key"),
                    title=f"Jira Task: {first_issue.get('key')} - {fields.get('summary')}",
                    normalized_content=existing_issue,
                    raw_output=first_issue,
                    confidence=1.0,
                    impact_on_decision=f"Identified existing tracking task {first_issue.get('key')}. Will update rather than creating duplicates.",
                )
            )

        summary = f"Found {len(issues)} matching Jira issue(s). Linked primary task: {existing_issue.get('key') if existing_issue else 'None'}."
        return {
            "success": success,
            "duration_ms": duration_ms,
            "summary": summary,
            "issues": issues,
            "existing_issue": existing_issue,
            "evidence_items": evidence_items,
            "canonical_id": canonical_id,
        }

    @staticmethod
    def create_or_update_issue(
        summary: str,
        description: str,
        issue_type: str = "Task",
        existing_key: Optional[str] = None,
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prevents duplicate Jira issues. Updates if existing_key is provided, otherwise creates.
        """
        if existing_key:
            canonical_id = "jira.api.issue.update"
            inputs = {
                "issueIdOrKey": existing_key,
                "body": {
                    "fields": {
                        "summary": summary,
                    }
                },
            }
            success, raw, duration_ms, error = swytchcode_client.exec(
                canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
            )
            return {
                "success": success,
                "duration_ms": duration_ms,
                "action": "UPDATED",
                "key": existing_key,
                "summary": f"Updated existing Jira task {existing_key}: '{summary}' (Prevented duplicate ticket creation).",
                "canonical_id": canonical_id,
            }
        else:
            canonical_id = "jira.api.issue.create"
            inputs = {
                "body": {
                    "fields": {
                        "project": {"key": "SCRUM"},
                        "summary": summary,
                        "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]},
                        "issuetype": {"name": issue_type},
                    }
                }
            }
            success, raw, duration_ms, error = swytchcode_client.exec(
                canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
            )
            created_key = raw.get("key", "SCRUM-43")
            return {
                "success": success,
                "duration_ms": duration_ms,
                "action": "CREATED",
                "key": created_key,
                "summary": f"Created new Jira operational task {created_key}: '{summary}'.",
                "canonical_id": canonical_id,
            }

    @staticmethod
    def add_comment(
        issue_key: str,
        comment_text: str,
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        canonical_id = "jira.api.comment.create"
        inputs = {
            "issueIdOrKey": issue_key,
            "body": {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment_text}]}],
                }
            },
        }
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )
        return {
            "success": success,
            "duration_ms": duration_ms,
            "summary": f"Appended operational audit comment to Jira ticket {issue_key}.",
            "comment_id": raw.get("id", "comment_new"),
            "canonical_id": canonical_id,
        }
