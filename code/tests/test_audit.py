"""Independent synthetic regressions; no public sample answers in test inputs."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import pytest

from assessor import authorized
from evidence import EvidenceStore, identifiers, parse_log_fields, record_state
from identity import IdentityIndex
from planner import plan
from policy import Policy
from schema import Observation, ResourceLink, Scope, UnresolvedCase
from state_resolver import resolve
from validate_output import validate
from writer import write_atomic

AT = "2026-04-10T12:00:00Z"
BEFORE = "2026-04-09T12:00:00Z"
AFTER = "2026-04-11T12:00:00Z"


def obs(rid="account_alpha", state="PRESENT", category="USER_PROFILE", system="account_service",
        at=BEFORE, available=BEFORE, replica="default", ids=("user_90001",), evidence="synthetic_1", fields=None):
    return Observation(resource_id=rid, state=state, category=category, system_id=system,
                       observed_at=at, available_at=available, replica=replica,
                       identifiers=ids, evidence_id=evidence, fields=fields or {})


def store(observations, scopes=()):
    by_resource = defaultdict(list)
    by_identifier = defaultdict(set)
    for o in observations:
        by_resource[(o.system_id,o.resource_id)].append(o)
        for v in o.identifiers:
            by_identifier[v].add((o.system_id,o.resource_id))
    return SimpleNamespace(by_resource=by_resource, by_identifier=by_identifier, scopes=scopes)


def policy():
    actions = dict(USER_PROFILE="DELETE", SECONDARY_IDENTIFIER="DELETE", SEARCH_INDEX_ENTRY="DELETE",
                   SUPPORT_MESSAGE="REDACT", ACCOUNT_TOMBSTONE="REDACT", ANALYTICS_PROFILE="ANONYMIZE",
                   SECURITY_AUDIT_LOG="RETAIN", LEGAL_HOLD_RECORD="RETAIN", BACKUP_ARCHIVE="RETAIN")
    return Policy([dict(data_category=k, required_action=v, condition="Synthetic condition") for k,v in actions.items()])


@pytest.mark.parametrize("text", [
    "Please do not delete my account. Send a copy of my records.",
    "Remove me from marketing lists only; I still use my account.",
    "Correct my surname without removing any records.",
    "Please change the email address used for this account.",
])
def test_non_deletion_consent(text):
    assert not authorized(text)


@pytest.mark.parametrize("text", ["Please erase my account.", "Je demande la suppression du compte.",
                                 "Solicito la eliminación de la cuenta.", "アカウントの削除を依頼します。", "계정 삭제를 요청합니다."])
def test_multilingual_baseline(text):
    assert authorized(text)


def test_unknown_intent_requires_review():
    with pytest.raises(UnresolvedCase):
        authorized("Please handle my privacy matter.")


def test_historical_identity_exact_match_and_future_rollback():
    users = [dict(user_id="user_90001",email="new@example.test",phone="+48 111 222 333",email_hash="a"*64),
             dict(user_id="user_90002",email="old.jr@example.test",phone="+48 444 555 666",email_hash="b"*64)]
    history = [dict(user_id="user_90001",field_name="email",old_value="old@example.test",new_value="new@example.test",event_time=BEFORE),
               dict(user_id="user_90001",field_name="phone",old_value="+48 777 888 999",new_value="+48 111 222 333",event_time=AFTER)]
    index = IdentityIndex(users,history)
    user, values = index.resolve("OLD@EXAMPLE.TEST",AT)
    assert user == "user_90001" and "old.jr@example.test" not in values
    assert "48777888999" in values and "48111222333" not in values


def test_structured_identifier_extraction_does_not_capture_python_quotes():
    assert "old@example.test" in identifiers({"email":"old@example.test"})
    assert "user_90001" not in identifiers("user_900012")


def test_delete_then_recreation_before_audit():
    observations = [obs(state="ABSENT"),obs(state="PRESENT",at=AT,evidence="synthetic_2")]
    current = resolve(store(observations),{"user_90001"},AT,[])
    status,steps = plan(current,policy(),AT)
    assert status == "INCOMPLETE" and steps[0]["evidence_id"] == "synthetic_2"
    assert [s["operation"] for s in steps] == ["REPORT_REMAINING_RECORD","DELETE_RECORD","VERIFY_RECORD_ABSENT"]


def test_replica_drift_is_not_erased_by_primary_absence():
    observations = [obs(state="ABSENT",replica="primary",at=AT),
                    obs(state="PRESENT",replica="regional",at=BEFORE)]
    current = resolve(store(observations),{"user_90001"},AT,[])
    assert current[0].state == "PRESENT" and current[0].replica == "regional"


def test_redacted_tombstone_preserves_stable_reference():
    fields = dict(subject_reference="user_90001",name=None,email=None,phone=None,email_hash=None,account_status="DELETED")
    assert record_state("ACCOUNT_TOMBSTONE",fields) == "REDACTED"
    fields["email_hash"] = "a"*64
    assert record_state("ACCOUNT_TOMBSTONE",fields) == "PRESENT"
    fields["email_hash"]=None
    fields["subject_reference"]="person@example.test"
    assert record_state("ACCOUNT_TOMBSTONE",fields)=="PRESENT"


def test_false_retention_condition_requires_alternate_policy():
    with pytest.raises(UnresolvedCase,match="Policy condition not satisfied"):
        policy().treatment(obs("legal_alpha","PRESENT","LEGAL_HOLD_RECORD","legal_service",
                               fields={"legal_hold_active":False}),AT)


def test_restore_and_flow_actions_precede_record_changes():
    observations = [obs(),obs("backup_alpha","ACTIVE","BACKUP_ARCHIVE","backup_service"),
                    obs("flow_alpha","ACTIVE","DATA_FLOW","integration_service")]
    status,steps = plan(observations,policy(),AT)
    assert status == "INCOMPLETE"
    assert [s["operation"] for s in steps if s["phase"]=="REMEDIATION"] == ["DISABLE_DATA_FLOW","BLOCK_RESTORE","DELETE_RECORD"]
    assert all(s["evidence_id"]=="" for s in steps if s["phase"]!="FINDING")


def test_required_retained_security_and_legal_records_stay_present():
    observations = [obs(state="ABSENT"),obs("security_alpha","PRESENT","SECURITY_AUDIT_LOG","security_service"),
                    obs("legal_alpha","PRESENT","LEGAL_HOLD_RECORD","legal_service")]
    status,steps = plan(observations,policy(),AT)
    assert status == "COMPLETE" and all(s["phase"]=="VERIFICATION" for s in steps)
    assert sum(s["operation"]=="VERIFY_RECORD_PRESENT" for s in steps)==2


def test_missing_required_retained_record_cannot_be_fabricated():
    with pytest.raises(UnresolvedCase,match="retained record missing"):
        plan([obs("security_alpha","ABSENT","SECURITY_AUDIT_LOG","security_service")],policy(),AT)


def test_post_cutoff_capture_and_event_excluded():
    observations = [obs(state="PRESENT"),obs(state="ABSENT",at=AT,available=AFTER),obs(state="ABSENT",at=AFTER)]
    assert resolve(store(observations),{"user_90001"},AT,[])[0].state == "PRESENT"


def test_future_identity_link_cannot_associate_existing_anonymous_resource():
    observations = [obs(ids=())]
    event = dict(event_type="LINK_RESOURCE_IDENTITY",event_time=AFTER,target_system="account_service",resource_id="account_alpha",details="Linked to user_90001")
    assert resolve(store(observations),{"user_90001"},AT,[event]) == []


def test_workflow_success_is_not_state_proof():
    event = dict(event_type="DELETE_RECORD",event_time=AT,target_system="account_service",resource_id="account_alpha",details="Deleted user_90001",reported_result="SUCCESS")
    assert resolve(store([obs()]),{"user_90001"},AT,[event])[0].state == "PRESENT"


def test_retained_security_alone_is_not_deletion_proof():
    with pytest.raises(UnresolvedCase,match="alone do not establish"):
        plan([obs("audit_alpha","PRESENT","SECURITY_AUDIT_LOG","security_service")],policy(),AT)


def test_explicit_source_link_adds_future_verification_without_finding():
    search=obs("search_90001","PRESENT","SEARCH_INDEX_ENTRY","search_service")
    data=store([search]);data.links=[ResourceLink(source_system="search_service",source_resource="search_90001",
        target_system="account_service",target_resource="account_90001",target_category="USER_PROFILE",
        observed_at=BEFORE,available_at=BEFORE,evidence_id="synthetic_1",field_path="source_resource_id")]
    states=resolve(data,{"user_90001"},AT,[])
    assert next(o for o in states if o.resource_id=="account_90001").state=="UNKNOWN"
    status,steps=plan(states,policy(),AT)
    assert status=="INCOMPLETE"
    assert any(s["resource_id"]=="account_90001" and s["operation"]=="VERIFY_RECORD_ABSENT" and not s["evidence_id"] for s in steps)
    assert not any(s["resource_id"]=="account_90001" and s["phase"] in {"FINDING","REMEDIATION"} for s in steps)


def test_identifier_free_child_retrieved_through_explicit_owning_source():
    account=obs("account_90001",state="ABSENT")
    child=obs("search_90001","PRESENT","SEARCH_INDEX_ENTRY","search_service",ids=())
    data=store([account,child]);data.links=[ResourceLink(source_system="search_service",source_resource="search_90001",
        target_system="account_service",target_resource="account_90001",target_category="USER_PROFILE",
        observed_at=BEFORE,available_at=BEFORE,evidence_id="synthetic_1",field_path="source_resource_id")]
    assert len(resolve(data,{"user_90001"},AT,[]))==2


def test_post_cutoff_resource_link_does_not_create_account_verification():
    data=store([obs("search_90001","PRESENT","SEARCH_INDEX_ENTRY","search_service")])
    data.links=[ResourceLink(source_system="search_service",source_resource="search_90001",
        target_system="account_service",target_resource="account_90001",target_category="USER_PROFILE",
        observed_at=BEFORE,available_at=AFTER,evidence_id="synthetic_1",field_path="source_resource_id")]
    assert len(resolve(data,{"user_90001"},AT,[]))==1


def test_resource_mentions_in_unstructured_text_do_not_create_ownership():
    from evidence import resource_references
    assert not list(resource_references({"text":"A different customer uses account_90002"}))


def test_unknown_linked_resource_blocks_completion():
    with pytest.raises(UnresolvedCase,match="remain unproven"):
        plan([obs(state="UNKNOWN")],policy(),AT)


def test_empty_primary_table_is_not_dropped_from_scope_inventory():
    s=EvidenceStore.__new__(EvidenceStore);s.observations=[];s.scopes=[]
    s.sql_file(dict(file_id="synthetic_sql",captured_at=BEFORE),
        'CREATE TABLE customer_profiles_primary(resource_id TEXT,user_id TEXT);'
        'CREATE TABLE customer_profiles_failover_replica(resource_id TEXT,user_id TEXT);'
        "INSERT INTO customer_profiles_failover_replica VALUES('account_90001','user_90001');")
    assert any(scope.replica=="customer_profiles_primary" and scope.resource_ids==() for scope in s.scopes)


def test_conflicting_same_time_observations_fail_closed():
    with pytest.raises(UnresolvedCase,match="Contradictory simultaneous"):
        resolve(store([obs(state="ABSENT"),obs(state="PRESENT")]),{"user_90001"},AT,[])


def test_partial_snapshot_does_not_prove_absence():
    partial=Scope(system_id="account_service",category="USER_PROFILE",observed_at=AT,available_at=AT,
                  evidence_id="synthetic_1",replica="default",resource_ids=(),complete=False)
    assert resolve(store([obs()],scopes=[partial]),{"user_90001"},AT,[])[0].state=="PRESENT"


@pytest.mark.parametrize("body", [
    'level=INFO service=account_service trace_id=t1 event=profile_lookup_completed resource_id=account_1 rows=0',
    '[INFO] [account_service] [t1] profile_lookup_completed: resource_id="account_1" rows="0"',
    'INFO | account_service | t1 | profile_lookup_completed | resource_id="account_1" rows="0"',
    '<14>1 node-1 account_service t1 - - event="profile_lookup_completed" resource_id="account_1" rows="0"',
    '{"event":"profile_lookup_completed","resource_id":"account_1","rows":"0"}',
    'requestId=t1 function=account_service message="event=\\"profile_lookup_completed\\" resource_id=\\"account_1\\" rows=\\"0\\""',
])
def test_log_formats(body):
    fields = parse_log_fields(body)
    assert fields["event"] == "profile_lookup_completed" and fields["resource_id"]=="account_1"


def test_invalid_evidence_and_future_work_citations_rejected():
    status,steps = plan([obs()],policy(),AT)
    row=dict(case_id="custom_alpha",deletion_status=status,steps=steps)
    request=dict(case_id="custom_alpha",audit_at=AT)
    sources={"synthetic_1":dict(captured_at=BEFORE)}
    validate([row],[request],sources,[],[],[obs()])
    steps[0]["evidence_id"]="invented"
    with pytest.raises(ValueError,match="Unknown or post-cutoff"):
        validate([row],[request],sources,[],[])


def test_atomic_output_failure_preserves_previous_file(tmp_path):
    path = tmp_path/"output.csv"
    path.write_text("previous valid output")
    with pytest.raises(KeyError):
        write_atomic(path,[dict(case_id="custom_alpha")])
    assert path.read_text()=="previous valid output"


def test_unsafe_sql_cannot_attach_files(tmp_path):
    s=EvidenceStore.__new__(EvidenceStore)
    s.observations=[];s.scopes=[]
    meta=dict(file_id="synthetic_sql",captured_at=BEFORE)
    import sqlite3
    with pytest.raises(sqlite3.DatabaseError):
        s.sql_file(meta,"ATTACH DATABASE '/tmp/never-created-deletion-audit.db' AS external;")
