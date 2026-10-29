from __future__ import annotations

from types import SimpleNamespace

import pytest

from model_client import ModelClient
from schema import IntentAssessment, SemanticAssessment, SemanticFact, UnresolvedCase


class FakeResponses:
    def __init__(self, result):
        self.result, self.calls = result, 0

    def parse(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(status="completed", output_parsed=self.result,
                               usage=SimpleNamespace(input_tokens=120, output_tokens=30,
                                                     input_tokens_details=SimpleNamespace(cached_tokens=10)))


def client(tmp_path, result):
    fake = FakeResponses(result)
    return ModelClient(tmp_path,model="synthetic-model-for-tests",client=SimpleNamespace(responses=fake)), fake


def test_model_cache_counts_only_new_usage_and_invalidates_on_input(tmp_path):
    interpreter,fake = client(tmp_path,IntentAssessment(authorizes_deletion=True,uncertain=False,rationale="Explicit request"))
    interpreter.assess_intent("Please delete my account.")
    interpreter.assess_intent("Please delete my account.")
    interpreter.assess_intent("Please erase my account.")
    assert fake.calls==2
    assert sum(e["input_tokens"] for e in interpreter.events)==240
    assert sum(e["cache_hit"] for e in interpreter.events)==1


def test_invented_evidence_is_rejected(tmp_path):
    result=SemanticAssessment(facts=[SemanticFact(resource_id="resource_alpha",system_id="support_platform",evidence_id="invented",pii_exposed=True,uncertain=False,supporting_quote="customer")])
    interpreter,_ = client(tmp_path,result)
    with pytest.raises(UnresolvedCase,match="invented"):
        interpreter.assess_evidence([dict(resource_id="resource_alpha",system_id="support_platform",evidence_id="synthetic_1",text="customer")])


def test_ungrounded_quote_rejected(tmp_path):
    result=SemanticAssessment(facts=[SemanticFact(resource_id="resource_alpha",system_id="support_platform",evidence_id="synthetic_1",pii_exposed=True,uncertain=False,supporting_quote="made up text")])
    interpreter,_=client(tmp_path,result)
    with pytest.raises(UnresolvedCase,match="quotation"):
        interpreter.assess_evidence([dict(resource_id="resource_alpha",system_id="support_platform",evidence_id="synthetic_1",text="customer")])


def test_refusal_does_not_create_success_cache(tmp_path):
    class Refusal:
        def parse(self,**kwargs):
            return SimpleNamespace(status="completed",output_parsed=None,usage=SimpleNamespace(input_tokens=2,output_tokens=1,input_tokens_details=SimpleNamespace(cached_tokens=0)))
    interpreter=ModelClient(tmp_path,model="synthetic-model-for-tests",client=SimpleNamespace(responses=Refusal()))
    with pytest.raises(UnresolvedCase):
        interpreter.assess_intent("Please delete my account.")
    assert not list(tmp_path.rglob("*.json"))
    assert interpreter.events[0]["input_tokens"]==2


def test_bounded_retry_accounts_every_attempt(tmp_path,monkeypatch):
    class TemporaryError(Exception):
        status_code=429
    class Flaky(FakeResponses):
        def parse(self,**kwargs):
            if self.calls==0:
                self.calls+=1
                raise TemporaryError()
            return super().parse(**kwargs)
    fake=Flaky(IntentAssessment(authorizes_deletion=True,uncertain=False,rationale="Explicit request"))
    interpreter=ModelClient(tmp_path,model="synthetic-model-for-tests",client=SimpleNamespace(responses=fake),attempts=2)
    monkeypatch.setattr("model_client.time.sleep",lambda _:None)
    assert interpreter.assess_intent("Delete my account").authorizes_deletion
    assert fake.calls==2 and len(interpreter.events)==2
    assert interpreter.events[0]["usage_known"] is False
