"""An independent temporary dataset exercises the terminal pipeline end to end."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from main import AuditPipeline
from validate_output import read_output, validate
from writer import write_atomic


def csv_file(path,fieldnames,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames);writer.writeheader();writer.writerows(rows)


def test_complete_incomplete_and_non_deletion_in_one_dataset(tmp_path):
    dataset=tmp_path/"dataset";dataset.mkdir()
    records=dataset/"evidence"/"records";records.mkdir(parents=True)
    at="2026-05-01T12:00:00Z"
    users=[dict(user_id=f"user_{90000+i}",name="Fictional User",email=f"person{i}@example.test",phone=f"+48 111 222 {i:03d}",email_hash=str(i)*64,updated_at="2026-01-01T00:00:00Z") for i in range(1,4)]
    csv_file(dataset/"user_identities.csv",list(users[0]),users)
    csv_file(dataset/"user_audit_log.csv",["audit_id","user_id","event_time","field_name","old_value","new_value"],[])
    csv_file(dataset/"system_activity.csv",["activity_id","event_time","event_type","source_system","target_system","resource_id","reported_result","details"],[])
    csv_file(dataset/"deletion_rules.csv",["rule_id","data_category","condition","required_action"],
             [dict(rule_id="rule_custom",data_category="USER_PROFILE",condition="Always",required_action="DELETE")])
    evidence=dict(file_id="custom_evidence",file_path="evidence/records/state.json",origin="synthetic_test",captured_at=at)
    csv_file(dataset/"evidence_files.csv",list(evidence),[evidence])
    data=dict(exported_at=at,origin="synthetic_test",records=[
        dict(recorded_at=at,system="account_service",resource_id="account_alpha",record_type="USER_PROFILE",result="NOT_FOUND",subject_reference="person1@example.test"),
        dict(recorded_at=at,system="account_service",resource_id="account_beta",record_type="USER_PROFILE",result="FOUND",subject_reference="person2@example.test")])
    (records/"state.json").write_text(json.dumps(data))
    requests=[dict(case_id=f"custom_{i}",email=f"person{i}@example.test",audit_at=at,request_text="Please erase my account." if i<3 else "Send a copy; please do not delete my account.") for i in range(1,4)]
    pipeline=AuditPipeline(dataset,tmp_path/"cache")
    predictions,unresolved=pipeline.run(requests)
    assert not unresolved
    assert [r["deletion_status"] for r in predictions]==["COMPLETE","INCOMPLETE","NOT_APPLICABLE"]
    assert len(pipeline.traces)==3
    assert {t["assessment"] for t in pipeline.traces}=={"CONFIRMED_COMPLETE","CONFIRMED_INCOMPLETE","NOT_APPLICABLE"}
    validate(predictions,requests,pipeline.store.sources,[],[],pipeline.store.observations)
    output=tmp_path/"output.csv";write_atomic(output,predictions)
    assert read_output(output)==predictions


def test_unresolved_intent_has_internal_assessment_without_a_fourth_csv_status():
    pipeline=AuditPipeline.__new__(AuditPipeline);pipeline.model=None
    rows,unresolved=pipeline.run([dict(case_id="custom_unknown",request_text="Please handle my privacy matter.")])
    assert rows==[] and len(unresolved)==1
    assert pipeline.traces[0]["assessment"]=="UNRESOLVED"
    assert pipeline.traces[0]["status"] is None


def test_incomplete_extraction_cannot_certify_complete(tmp_path):
    # The pipeline test above covers normal wiring; this regression tests its gate.
    from types import SimpleNamespace
    from schema import Observation, UnresolvedCase
    from policy import Policy
    import pytest
    at="2026-05-01T12:00:00Z"
    observation=Observation(system_id="account_service",resource_id="account_alpha",category="USER_PROFILE",
                            state="ABSENT",observed_at=at,available_at=at,evidence_id="synthetic_1",identifiers=("user_90001",))
    pipeline=AuditPipeline.__new__(AuditPipeline)
    pipeline.model=None
    pipeline.traces=[]
    pipeline.best_effort=False
    pipeline.review_required=[]
    pipeline.identity=SimpleNamespace(resolve=lambda email,cutoff:("user_90001",{"user_90001"}))
    pipeline.activity=[]
    pipeline.policy=Policy([dict(data_category="USER_PROFILE",required_action="DELETE",condition="Always")])
    pipeline.store=SimpleNamespace(by_identifier={"user_90001":{("account_service","account_alpha")}},
                                   by_resource={("account_service","account_alpha"):[observation]},scopes=[],
                                   coverage=[dict(parsed=False)])
    with pytest.raises(UnresolvedCase,match="extraction incomplete"):
        pipeline.process(dict(case_id="custom_alpha",email="person@example.test",audit_at=at,request_text="Delete my account."))
