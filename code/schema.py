"""Typed observations and the single canonical output vocabulary."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Observation(StrictModel):
    system_id: str
    resource_id: str
    category: str
    state: Literal["PRESENT", "ABSENT", "REDACTED", "ANONYMIZED", "ACTIVE", "DISABLED", "BLOCKED", "UNKNOWN"]
    observed_at: str
    available_at: str
    evidence_id: str
    replica: str = "default"
    identifiers: tuple[str, ...] = ()
    fields: dict[str, object] = Field(default_factory=dict)


class Scope(StrictModel):
    system_id: str
    category: str
    observed_at: str
    available_at: str
    evidence_id: str
    replica: str
    resource_ids: tuple[str, ...]
    complete: bool = False


class ResourceLink(StrictModel):
    source_system: str
    source_resource: str
    target_system: str
    target_resource: str
    target_category: str
    observed_at: str
    available_at: str
    evidence_id: str
    field_path: str


class IntentAssessment(StrictModel):
    authorizes_deletion: bool
    uncertain: bool
    rationale: str


class SemanticFact(StrictModel):
    resource_id: str
    system_id: str
    evidence_id: str
    pii_exposed: bool
    uncertain: bool
    supporting_quote: str


class SemanticAssessment(StrictModel):
    facts: list[SemanticFact]


OPERATIONS = {
    "FINDING": {
        "REPORT_REMAINING_RECORD": "PRESENT",
        "REPORT_EXPOSED_PII": "PRESENT",
        "REPORT_ACTIVE_DATA_FLOW": "ACTIVE",
        "REPORT_RESTORE_RISK": "ACTIVE",
    },
    "REMEDIATION": {
        "DISABLE_DATA_FLOW": "DISABLED",
        "BLOCK_RESTORE": "BLOCKED",
        "DELETE_RECORD": "ABSENT",
        "REDACT_RECORD": "REDACTED",
        "ANONYMIZE_RECORD": "ANONYMIZED",
    },
    "VERIFICATION": {
        "VERIFY_RECORD_ABSENT": "ABSENT",
        "VERIFY_RECORD_PRESENT": "PRESENT",
        "VERIFY_RECORD_REDACTED": "REDACTED",
        "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED",
        "VERIFY_DATA_FLOW_DISABLED": "DISABLED",
        "VERIFY_RESTORE_BLOCKED": "BLOCKED",
    },
}
COLUMNS = ("case_id", "deletion_status", "steps_json")


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Evidence timestamps must include a timezone")
    return parsed


def step_key(step: dict) -> tuple:
    phase = step["phase"]
    return (list(OPERATIONS).index(phase), list(OPERATIONS[phase]).index(step["operation"]),
            step["system_id"], step["resource_id"])


class UnresolvedCase(ValueError):
    """Stop before publishing output; the three labels have no UNKNOWN value."""
