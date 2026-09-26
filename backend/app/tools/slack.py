from typing import Any, Dict, List, Optional
from .swytchcode_client import swytchcode_client
from ..models.schema import EvidenceItem

class SlackToolAdapter:
    """
    Slack Internal Operational Context & Notification Adapter via Swytchcode.
    Canonical IDs: slack.search.message.list, slack.chat.postmessage.create
    """

    @staticmethod
    def search_finance_messages(
        query: str = "Zelar invoice approval",
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        canonical_id = "slack.search.message.list"
        inputs = {"query": query}
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )

        matches = raw.get("messages", {}).get("matches", [])
        evidence_items: List[EvidenceItem] = []
        has_payment_hold = False

        for idx, msg in enumerate(matches):
            text = msg.get("text", "")
            user = msg.get("user", "")
            lower_text = text.lower()
            
            # Check for active payment hold while ignoring negative phrases ("no hold", "no payment hold")
            if ("payment hold" in lower_text or "freeze payment" in lower_text or "block payment" in lower_text) and not (
                "no payment hold" in lower_text or "no hold" in lower_text or "not on hold" in lower_text
            ):
                has_payment_hold = True

            evidence_items.append(
                EvidenceItem(
                    id=f"ev_slack_msg_{idx+1}",
                    provider="Slack",
                    canonical_tool_id=canonical_id,
                    identifier=f"slack_msg_{msg.get('ts', idx)}",
                    title=f"Slack #finance-ops Message ({user})",
                    normalized_content={"user": user, "text": text, "timestamp": msg.get("ts")},
                    raw_output=msg,
                    confidence=1.0,
                    impact_on_decision="Confirmed Finance Director greenlight and absence of active operational payment holds.",
                )
            )

        summary = f"Scanned internal Slack #finance-ops. Found {len(matches)} approval discussions (Active Payment Hold: {has_payment_hold})."
        return {
            "success": success,
            "duration_ms": duration_ms,
            "summary": summary,
            "messages": matches,
            "has_payment_hold": has_payment_hold,
            "evidence_items": evidence_items,
            "canonical_id": canonical_id,
        }

    @staticmethod
    def post_channel_message(
        channel: str = "#finance-ops",
        message: str = "",
        demo_mode: bool = True,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        canonical_id = "slack.chat.postmessage.create"
        inputs = {
            "body": {
                "channel": channel,
                "text": message,
            }
        }
        success, raw, duration_ms, error = swytchcode_client.exec(
            canonical_id, inputs, demo_mode=demo_mode, scenario_id=scenario_id
        )
        return {
            "success": success,
            "duration_ms": duration_ms,
            "summary": f"Posted operational update to Slack {channel}: '{message[:60]}...'",
            "ts": raw.get("ts", ""),
            "channel": channel,
            "canonical_id": canonical_id,
        }
