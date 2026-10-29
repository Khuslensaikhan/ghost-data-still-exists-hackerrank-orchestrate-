import pytest

from evidence import restore_permission_from_text,record_state
from planner import plan
from schema import Observation,UnresolvedCase
from state_resolver import resolve
from test_audit import store,policy


def backup(state,at,evidence,fields=None):
    return Observation(system_id="backup_service",resource_id="backup_90001",category="BACKUP_ARCHIVE",
                       state=state,observed_at=at,available_at=at,evidence_id=evidence,
                       identifiers=("user_90001",),fields=fields or {})


def test_archive_presence_and_healthy_console_do_not_prove_restore_access():
    assert restore_permission_from_text("Customer archives\nHealthy\nbackup_90001\nArchive AES-256\nLast drill completed")=="UNKNOWN"
    assert record_state("BACKUP_ARCHIVE",{"archive_present":True})=="UNKNOWN"


@pytest.mark.parametrize("text,state",[
    ("Restore access: Allowed","ACTIVE"),("Restore allowed=false","BLOCKED"),
    ("Restore authorization\nDenied","BLOCKED"),("Restore permission: Enabled","ACTIVE"),
    ("Restore access: Allowed\nRestore allowed: false","UNKNOWN"),
])
def test_only_explicit_restore_controls_establish_state(text,state):
    assert restore_permission_from_text(text)==state


def test_later_permission_readback_cannot_resolve_earlier_unknown_policy():
    early="2026-04-29T09:00:00Z";audit="2026-04-30T11:00:00Z";late="2026-09-15T12:00:00Z"
    observations=[backup("UNKNOWN",early,"synthetic_metadata",{"unknown_fields":["restore_allowed"]}),
                  backup("ACTIVE",late,"synthetic_later",{"restore_allowed":True})]
    current=resolve(store(observations),{"user_90001"},audit,[])
    assert current[0].state=="UNKNOWN"
    with pytest.raises(UnresolvedCase,match="remain unproven"):
        plan(current,policy(),audit)


def test_independent_earlier_permission_is_not_replaced_by_metadata_only_view():
    observations=[backup("ACTIVE","2026-04-28T09:00:00Z","synthetic_policy",{"restore_allowed":True}),
                  backup("UNKNOWN","2026-04-29T09:00:00Z","synthetic_metadata",{"unknown_fields":["restore_allowed"]})]
    current=resolve(store(observations),{"user_90001"},"2026-04-30T11:00:00Z",[])
    assert current[0].state=="ACTIVE" and current[0].evidence_id=="synthetic_policy"


def test_conflicting_later_permission_does_not_reuse_earlier_policy():
    observations=[backup("ACTIVE","2026-04-28T09:00:00Z","synthetic_policy",{"restore_allowed":True}),
                  backup("UNKNOWN","2026-04-29T09:00:00Z","synthetic_conflict",{"restore_permission_observed":True})]
    assert resolve(store(observations),{"user_90001"},"2026-04-30T11:00:00Z",[])[0].state=="UNKNOWN"


@pytest.mark.parametrize("known,expected",[("BLOCKED","UNKNOWN"),("ACTIVE","ACTIVE")])
def test_independent_replica_uncertainty_is_not_hidden_by_newer_compliant_read(known,expected):
    observations=[backup(known,"2026-04-29T09:00:00Z","synthetic_primary").model_copy(update={"replica":"primary"}),
                  backup("UNKNOWN","2026-04-28T09:00:00Z","synthetic_replica").model_copy(update={"replica":"regional"})]
    assert resolve(store(observations),{"user_90001"},"2026-04-30T11:00:00Z",[])[0].state==expected
