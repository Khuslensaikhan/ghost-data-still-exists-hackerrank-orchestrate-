"""Policy lookup and independent field-level compliance checks."""
from __future__ import annotations

from identity import EMAIL_RE, PHONE_RE
from schema import Observation, UnresolvedCase, timestamp

DIRECT_FIELDS = {"name", "full_name", "display_name", "email", "phone", "email_hash",
                 "requester_name", "requester_email", "requester_phone", "owner_email", "owner_phone",
                 "customer_email", "matched_value", "recipient_email", "recipient", "to"}
LINK_FIELDS = {"user_id", "customer_reference", "subject_reference"}
EMPTY = (None, "", "null", "None", "[REDACTED]", "[redacted]", "REDACTED", "redacted", "anonymous")


def exposed(fields: dict, *, stable_allowed: bool) -> bool:
    for key, value in fields.items():
        if isinstance(value, dict) and exposed(value, stable_allowed=stable_allowed):
            return True
        if isinstance(value, list) and any(isinstance(item,dict) and exposed(item,stable_allowed=stable_allowed) for item in value):
            return True
        if key in DIRECT_FIELDS and value not in EMPTY:
            return True
        if not stable_allowed and key in LINK_FIELDS and value not in EMPTY:
            return True
        if stable_allowed and key in LINK_FIELDS and value not in EMPTY:
            if isinstance(value,str) and (EMAIL_RE.search(value) or PHONE_RE.search(value)):
                return True
        if key in {"message_text", "message_excerpt", "text", "body"} and isinstance(value, str):
            if EMAIL_RE.search(value) or PHONE_RE.search(value):
                return True
    return False


class Policy:
    def __init__(self, rows: list[dict]):
        self.rules = {r["data_category"]: r for r in rows}
        if len(self.rules) != len(rows):
            raise ValueError("Multiple policies for a category require explicit precedence")

    def treatment(self, observation: Observation, cutoff: str) -> tuple[str, str, str, str]:
        """Return finding, remediation, verification, required final state."""
        category = observation.category
        if category == "DATA_FLOW":
            return "REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED", "DISABLED"
        if category not in self.rules:
            raise UnresolvedCase(f"Unknown data category {category}")
        action = self.rules[category]["required_action"]
        fields=observation.fields
        # Respect explicit evidence that a conditional policy does not apply.
        # The supplied rules define no alternate treatment for these situations.
        counterexamples={
            "SUPPORT_ATTACHMENT": ("belongs_only_to_subject",False),
            "SUPPORT_MESSAGE": ("shared_context_must_be_retained",False),
            "SECURITY_AUDIT_LOG": ("within_retention_period",False),
            "LEGAL_HOLD_RECORD": ("legal_hold_active",False),
            "BACKUP_ARCHIVE": ("restore_access_can_be_blocked",False),
        }
        if category in counterexamples:
            flag,value=counterexamples[category]
            if flag in fields and fields[flag] is value:
                raise UnresolvedCase(f"Policy condition not satisfied for {category}; alternate treatment is unspecified")
        if category=="ACCOUNT_TOMBSTONE" and fields.get("account_status") not in (None,"DELETED"):
            raise UnresolvedCase("Tombstone policy requires a deleted account")
        if category == "BACKUP_ARCHIVE":
            return "REPORT_RESTORE_RISK", "BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED", "BLOCKED"
        if action == "DELETE":
            return "REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT", "ABSENT"
        if action == "REDACT":
            return "REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED", "REDACTED"
        if action == "ANONYMIZE":
            return "REPORT_EXPOSED_PII", "ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"
        if action == "RETAIN":
            until = observation.fields.get("retention_until") or observation.fields.get("retained_until")
            if until and timestamp(str(until)) <= timestamp(cutoff):
                raise UnresolvedCase("Retention expired; supplied policy does not specify subsequent treatment")
            return "", "", "VERIFY_RECORD_PRESENT", "PRESENT"
        raise UnresolvedCase(f"Unsupported policy action {action}")
