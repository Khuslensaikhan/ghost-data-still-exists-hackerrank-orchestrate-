"""Independent counterexamples for cutoff, scope and attribution integrity."""
from types import SimpleNamespace

import pytest

from evidence import EvidenceStore
from main import AuditPipeline
from policy import Policy
from schema import IntentAssessment, Scope, SemanticAssessment, SemanticFact
from schema import UnresolvedCase
from state_resolver import resolve
from test_audit import AT, BEFORE, obs, store
from validate_output import validate


def test_anonymous_404_cannot_be_assigned_by_shared_file():
    anonymous = obs(state="ABSENT", ids=())
    security = obs("audit_alpha", "PRESENT", "SECURITY_AUDIT_LOG", "security_service")
    states = resolve(store([anonymous, security]), {"user_90001"}, AT, [])
    assert [o.resource_id for o in states] == ["audit_alpha"]


def test_sql_without_explicit_scope_does_not_claim_complete_inventory():
    evidence = EvidenceStore.__new__(EvidenceStore)
    evidence.observations = []; evidence.scopes = []
    evidence.sql_file(dict(file_id="synthetic_sql", captured_at=BEFORE),
        "CREATE TABLE customer_profiles_primary(resource_id TEXT, user_id TEXT);")
    assert evidence.scopes and not any(s.complete for s in evidence.scopes)


def test_explicit_sql_scope_preserves_empty_primary_negative_observation():
    evidence = EvidenceStore.__new__(EvidenceStore)
    evidence.observations = []; evidence.scopes = []
    evidence.sql_file(dict(file_id="synthetic_sql", captured_at=BEFORE),
        "CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT);"
        f"INSERT INTO snapshot_scope VALUES('account_service','{BEFORE}');"
        "CREATE TABLE customer_profiles_primary(resource_id TEXT,user_id TEXT);"
        "CREATE TABLE customer_profiles_failover_replica(resource_id TEXT,user_id TEXT);"
        "INSERT INTO customer_profiles_failover_replica VALUES('account_alpha','user_90001');")
    assert any(s.complete and s.replica == "customer_profiles_primary" and not s.resource_ids
               for s in evidence.scopes)
    # An empty primary does not hide the positive failover row.
    assert resolve(store(evidence.observations, evidence.scopes), {"user_90001"}, AT, [])[0].state == "PRESENT"
    previous = obs(at="2026-04-08T12:00:00Z", evidence="synthetic_sql", replica="customer_profiles_primary")
    primary_scope = [s for s in evidence.scopes if s.replica == "customer_profiles_primary"]
    assert resolve(store([previous], primary_scope), {"user_90001"}, AT, [])[0].state == "ABSENT"


def test_complete_scope_cannot_validate_an_invented_resource_id():
    known = obs("account_other", evidence="synthetic_sql")
    scope = Scope(system_id="account_service", category="USER_PROFILE", observed_at=BEFORE,
                  available_at=BEFORE, evidence_id="synthetic_sql", replica="default",
                  resource_ids=("account_other",), complete=True)
    step = dict(step_no=1, phase="VERIFICATION", system_id="account_service", resource_id="account_invented",
                operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id="synthetic_sql")
    with pytest.raises(ValueError, match="Citation does not identify"):
        validate([dict(case_id="custom", deletion_status="COMPLETE", steps=[step])],
                 [dict(case_id="custom", audit_at=AT)],
                 {"synthetic_sql": dict(captured_at=BEFORE)}, [], [], [known], [scope])


def test_partial_json_export_cannot_supersede_known_present_state():
    evidence = EvidenceStore.__new__(EvidenceStore)
    evidence.observations = []; evidence.scopes = []
    evidence.json_file(dict(file_id="synthetic_sql", captured_at=AT), dict(snapshots=[dict(
        collection="customer_profiles", data_store="account_service", captured_at=AT, records=[])]))
    assert evidence.scopes and not any(s.complete for s in evidence.scopes)
    assert resolve(store([obs()], evidence.scopes), {"user_90001"}, AT, [])[0].state == "PRESENT"


def test_redacted_tombstone_and_retention_do_not_prove_primary_account_absence():
    tombstone = obs("tombstone_alpha", "REDACTED", "ACCOUNT_TOMBSTONE", "identity_service")
    security = obs("audit_alpha", "PRESENT", "SECURITY_AUDIT_LOG", "security_service")
    pipeline = AuditPipeline.__new__(AuditPipeline)
    pipeline.model = None; pipeline.traces = []; pipeline.activity = []
    pipeline.identity = SimpleNamespace(resolve=lambda email, cutoff: ("user_90001", {"user_90001"}))
    pipeline.store = store([tombstone, security]); pipeline.store.coverage = [dict(parsed=True)]
    pipeline.policy = Policy([dict(data_category=c, required_action=a, condition="Always")
        for c, a in [("ACCOUNT_TOMBSTONE", "REDACT"), ("SECURITY_AUDIT_LOG", "RETAIN")]])
    with pytest.raises(UnresolvedCase, match="account absence proof"):
        pipeline.process(dict(case_id="custom", email="fictional@example.test",
                              audit_at=AT, request_text="Delete my account"))


def test_observed_sync_recreation_before_cutoff_overrides_earlier_absence():
    deleted = obs(state="ABSENT")
    recreated = obs(state="PRESENT", at=AT, evidence="synthetic_sync")
    event = dict(event_type="SYNC_RECORD", event_time=AT, target_system="account_service",
                 resource_id="account_alpha", reported_result="SUCCESS", details="Copied user_90001")
    assert resolve(store([deleted, recreated]), {"user_90001"}, AT, [event])[0].state == "PRESENT"
    # The synchronization claim alone is not an independently observed copy.
    assert resolve(store([deleted]), {"user_90001"}, AT, [event])[0].state == "ABSENT"


def test_actual_pipeline_invokes_optional_intent_and_evidence_adapter():
    calls = []
    class Adapter:
        def assess_intent(self, text):
            calls.append("intent")
            return IntentAssessment(authorizes_deletion=True, uncertain=False, rationale="Synthetic authorization")

        def assess_evidence(self, candidates):
            calls.append("evidence")
            return SemanticAssessment(facts=[SemanticFact(**{k: c[k] for k in
                ("system_id", "resource_id", "evidence_id")}, pii_exposed=True, uncertain=False,
                supporting_quote=c["text"]) for c in candidates])

    account = obs(state="ABSENT")
    support = obs("support_alpha", "PRESENT", "SUPPORT_MESSAGE", "support_platform",
                  fields={"text": "Fictional direct identifier remains"})
    pipeline = AuditPipeline.__new__(AuditPipeline)
    pipeline.model = Adapter(); pipeline.traces = []; pipeline.activity = []
    pipeline.identity = SimpleNamespace(resolve=lambda email, cutoff: ("user_90001", {"user_90001"}))
    pipeline.store = store([account, support]); pipeline.store.coverage = [dict(parsed=True)]
    pipeline.policy = Policy([dict(data_category=c, required_action=a, condition="Always")
        for c, a in [("USER_PROFILE", "DELETE"), ("SUPPORT_MESSAGE", "REDACT")]])
    rows, unresolved = pipeline.run([dict(case_id="custom", email="fictional@example.test",
        audit_at=AT, request_text="Delete my account")])
    assert not unresolved and rows[0]["deletion_status"] == "INCOMPLETE"
    assert calls == ["intent", "evidence"]
