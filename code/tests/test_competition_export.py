"""Competition fallbacks are explicit uncertainty, never verified completion."""
from types import SimpleNamespace

import pytest

from competition_export import build_export
from policy import Policy
from schema import UnresolvedCase
from test_audit import AT, AFTER, BEFORE, obs, store
from validate_output import validate


def pipeline(observations):
    data = store(observations); data.links = []
    return SimpleNamespace(model=None, store=data, activity=[],
        identity=SimpleNamespace(resolve=lambda email, cutoff: ("user_90001", {"user_90001"})),
        policy=Policy([dict(data_category=c, required_action=a, condition="Always") for c,a in
            [("USER_PROFILE", "DELETE"), ("SECURITY_AUDIT_LOG", "RETAIN"),
             ("ACCOUNT_TOMBSTONE", "REDACT"), ("BACKUP_ARCHIVE", "RETAIN")]]))


def query(text="Delete my account"):
    return dict(case_id="custom_fallback", email="fictional@example.test", audit_at=AT, request_text=text)


def failure():
    return dict(case_id="custom_fallback", reason="Completion cannot be established")


def check(rows, queries, p, fallbacks=()):
    validate(rows, queries, {"synthetic_1": dict(captured_at=BEFORE)}, [], [],
        p.store.by_resource[next(iter(p.store.by_resource))] if p.store.by_resource else [],
        fallback_case_ids=set(fallbacks), resource_links=p.store.links)


def test_retained_only_fallback_is_incomplete_with_uncited_future_check():
    p = pipeline([obs("audit_alpha", "PRESENT", "SECURITY_AUDIT_LOG", "security_service")])
    rows, ledger = build_export(p, [query()], [], [failure()])
    assert rows[0]["deletion_status"] == "INCOMPLETE"
    assert [s["operation"] for s in rows[0]["steps"]] == ["VERIFY_RECORD_PRESENT"]
    assert rows[0]["steps"][0]["evidence_id"] == ""
    assert ledger[0]["unverified_fallback"] and ledger[0]["resource_support"][0]["evidence_id"] == "synthetic_1"
    check(rows, [query()], p, ["custom_fallback"])
    with pytest.raises(ValueError, match="needs findings"):
        check(rows, [query()], p)


def test_empty_supported_evidence_yields_empty_fallback_without_invented_ids():
    p = pipeline([])
    rows, ledger = build_export(p, [query()], [], [failure()])
    assert rows == [dict(case_id="custom_fallback", deletion_status="INCOMPLETE", steps=[])]
    assert ledger[0]["resource_support"] == []
    check(rows, [query()], p, ["custom_fallback"])


@pytest.mark.parametrize("text", ["Please handle my privacy matter", "Please do not delete my account"])
def test_unknown_or_non_deletion_intent_cannot_be_recast_as_authorized_fallback(text):
    with pytest.raises(UnresolvedCase):
        build_export(pipeline([]), [query(text)], [], [failure()])


def test_late_ownership_observation_does_not_supply_fallback_resource():
    p = pipeline([obs(state="ABSENT", available=AFTER)])
    rows, ledger = build_export(p, [query()], [], [failure()])
    assert rows[0]["steps"] == [] and ledger[0]["resource_support"] == []


def test_restore_unknown_is_only_a_future_check_not_an_active_risk_finding():
    p = pipeline([obs("backup_alpha", "UNKNOWN", "BACKUP_ARCHIVE", "backup_service")])
    rows, ledger = build_export(p, [query()], [], [failure()])
    assert [s["operation"] for s in rows[0]["steps"]] == ["VERIFY_RESTORE_BLOCKED"]
    assert ledger[0]["resource_support"][0]["observed_state"] == "UNKNOWN"
    check(rows, [query()], p, ["custom_fallback"])


def test_strict_predictions_are_preserved_exactly_and_ordered():
    strict = [dict(case_id="custom_z", deletion_status="NOT_APPLICABLE", steps=[])]
    rows, ledger = build_export(pipeline([]), [query(), dict(case_id="custom_z")], strict, [failure()])
    assert rows[-1] == strict[0] and strict == [dict(case_id="custom_z", deletion_status="NOT_APPLICABLE", steps=[])]
    assert [r["case_id"] for r in rows] == ["custom_fallback", "custom_z"]


def test_fallback_ledger_cannot_allow_fake_resource_or_complete_label():
    p = pipeline([obs("audit_alpha", "PRESENT", "SECURITY_AUDIT_LOG", "security_service")])
    rows, _ = build_export(p, [query()], [], [failure()])
    rows[0]["steps"][0]["resource_id"] = "invented_account"
    with pytest.raises(ValueError, match="resource anchor"):
        check(rows, [query()], p, ["custom_fallback"])
    rows[0]["deletion_status"] = "COMPLETE"
    with pytest.raises(ValueError, match="must be INCOMPLETE"):
        check(rows, [query()], p, ["custom_fallback"])


def test_fallback_cannot_claim_existing_evidence_for_future_verification():
    p = pipeline([obs("audit_alpha", "PRESENT", "SECURITY_AUDIT_LOG", "security_service")])
    rows, _ = build_export(p, [query()], [], [failure()])
    rows[0]["steps"][0]["evidence_id"] = "synthetic_1"
    with pytest.raises(ValueError, match="uncited future"):
        check(rows, [query()], p, ["custom_fallback"])
