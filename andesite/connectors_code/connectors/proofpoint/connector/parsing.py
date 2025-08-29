"""
Tools to prune the ProofPoint data to the essentials.
This is used to reduce the size of the data sent to an LLM.
"""

from typing import Any
from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)


def remove_null_values(obj):
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            v2 = remove_null_values(v)
            if v2:
                cleaned[k] = v2
        return cleaned

    elif isinstance(obj, list):
        cleaned = []
        for item in obj:
            item2 = remove_null_values(item)
            if item2:
                cleaned.append(item2)
        return cleaned

    else:
        return obj


def parse_proofpoint_click_event(event: dict[str, Any]) -> dict[str, str | list | dict]:
    """Parse the essentials from ProofPoint click events."""
    return remove_null_values(
        {
            "campaign_id": event.get("campaignId"),
            "classification": event.get("classification"),
            "click_ip": event.get("clickIP"),
            "click_time": event.get("clickTime"),
            "recipient": event.get("recipient"),
            "sender": event.get("sender"),
            "sender_ip": event.get("senderIP"),
            "threat_id": event.get("threatID"),
            "threat_time": event.get("threatTime"),
            "threat_status": event.get("threatStatus"),
            "url": event.get("url"),
            "user_agent": event.get("userAgent"),
        }
    )


def parse_proofpoint_message_event(
    event: dict[str, Any],
) -> dict[str, str | list | dict]:
    """Parse the essentials from ProofPoint message events."""
    return remove_null_values(
        {
            "message_time": event.get("messageTime"),
            "spam_score": event.get("spamScore"),
            "phish_score": event.get("phishScore"),
            "imposter_score": event.get("impostorScore"),
            "malware_score": event.get("malwareScore"),
            "quarantine_folder": event.get("quarantineFolder"),
            "sender": event.get("sender"),
            "sender_ip": event.get("senderIP"),
            "recipient": event.get("recipient"),
            "recipient_email": event.get("recipient_email"),
            "message_subject": event.get("subject"),
            "message_time": event.get("message_time"),
            "header_from": event.get("headerFrom"),
            "header_reply_to": event.get("headerReplyTo"),
            "from_address": event.get("fromAddress", []),
            "cc_address": event.get("ccAddresses", []),
            "reply_to_address": event.get("replyToAddress", []),
            "to_addresses": event.get("toAddresses", []),
            "xmailer": event.get("xmailer"),
            "message_parts": [
                {
                    "disposition": part.get("disposition"),
                    "filename": part.get("filename"),
                    "sandbox_status": part.get("sandboxStatus"),
                    "sha256": part.get("sha256"),
                    "md5": part.get("md5"),
                    "true_content_type": part.get("contentType"),
                }
                for part in event.get("messageParts", [])
                if part.get("disposition") == "attached"
            ],
            "threats_info": [
                {
                    "threat_id": threat.get("threatID"),
                    "status": threat.get("threatStatus"),
                    "classification": threat.get("classification"),
                    "threat": threat.get("threat"),
                }
                for threat in event.get("threatsInfoMap", [])
            ],
        }
    )


def parse_proofpoint_messages(
    message_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Parse the essentials from ProofPoint messages."""
    try:
        pruned_events = []
        for event in message_events:
            pruned_event = parse_proofpoint_message_event(event)
            pruned_events.append(pruned_event)
    except Exception:
        logger().exception("Failed to parse messages")
        return message_events
    return pruned_events


def parse_proofpoint_clicks(click_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse the essentials from ProofPoint clicks."""
    try:
        pruned_events = []
        for event in click_events:
            pruned_event = parse_proofpoint_click_event(event)
            pruned_events.append(pruned_event)
    except Exception:
        logger().exception("Failed to parse clicks")
        return click_events
    return pruned_events


def parse_proofpoint_evidence_object(evidence: dict[str, Any]) -> dict[str, Any]:
    """Parse the essentials from a ProofPoint evidence."""
    return remove_null_values(
        {
            "type": evidence.get("type"),
            "display": evidence.get("display"),
            "what": evidence.get("what"),
            "platform": evidence.get("platform"),
        }
    )


def parse_proofpooint_forensics(
    forensics_report: dict[str, Any], include_nonmalicious=False
) -> dict[str, Any]:
    """Parse the essentials from ProofPoint forensics reports."""
    pruned_reports = []
    for report in forensics_report.get("reports", []):
        pruned_forensics = []
        for evidence in report.get("forensics", []):
            if not include_nonmalicious and evidence.get("malicious", False):
                pruned_evidence = parse_proofpoint_evidence_object(evidence)
                pruned_forensics.append(pruned_evidence)
        report["forensics"] = pruned_forensics
        pruned_reports.append(report)
    forensics_report["reports"] = pruned_reports
    return forensics_report
