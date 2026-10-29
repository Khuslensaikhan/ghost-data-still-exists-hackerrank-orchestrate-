from types import SimpleNamespace

import pytest

from main import AuditPipeline
from policy import Policy
from schema import Observation,UnresolvedCase
from validate_output import validate
from assessor import account_audit_required


def test_best_effort_cannot_override_security_only_completion_gate():
    at="2026-04-10T12:00:00Z"
    o=Observation(system_id="security_service",resource_id="audit_alpha",category="SECURITY_AUDIT_LOG",
                  state="PRESENT",observed_at=at,available_at=at,evidence_id="synthetic_1",identifiers=("user_90001",))
    p=AuditPipeline.__new__(AuditPipeline)
    p.model=None;p.best_effort=True;p.review_required=[];p.traces=[];p.activity=[]
    p.identity=SimpleNamespace(resolve=lambda email,cutoff:("user_90001",{"user_90001"}))
    p.policy=Policy([dict(data_category="SECURITY_AUDIT_LOG",required_action="RETAIN",condition="Always")])
    p.store=SimpleNamespace(by_identifier={"user_90001":{("security_service","audit_alpha")}},
                            by_resource={("security_service","audit_alpha"):[o]},scopes=[],coverage=[dict(parsed=True)])
    with pytest.raises(UnresolvedCase,match="alone do not establish"):
        p.process(dict(case_id="custom_alpha",email="person@example.test",audit_at=at,request_text="Delete my account."))


def test_standalone_validator_rejects_security_only_completion():
    step=dict(step_no=1,phase="VERIFICATION",system_id="security_service",resource_id="audit_alpha",
              operation="VERIFY_RECORD_PRESENT",state="PRESENT",evidence_id="synthetic_1")
    with pytest.raises(ValueError,match="retained records alone"):
        validate([dict(case_id="custom_alpha",deletion_status="COMPLETE",steps=[step])],
                 [dict(case_id="custom_alpha",audit_at="2026-04-10T12:00:00Z")],
                 {"synthetic_1":dict(captured_at="2026-04-09T12:00:00Z")},[],[])


def test_narrow_attachment_request_does_not_require_an_account_step():
    assert not account_audit_required("Please delete only this support attachment.")
    assert account_audit_required("Please delete my account and its support attachments.")
