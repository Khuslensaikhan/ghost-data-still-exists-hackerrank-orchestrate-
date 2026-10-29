"""Interpret consent; never delegate policy or final output to the model."""
from __future__ import annotations

import re
from typing import Protocol

from schema import IntentAssessment, UnresolvedCase


class IntentInterpreter(Protocol):
    def assess_intent(self, text: str) -> IntentAssessment: ...


def baseline_intent(text: str) -> IntentAssessment:
    """Conservative lexical baseline, explicitly separate from semantic inference."""
    lower = text.casefold()
    negatives = (
        r"(?:do not|don't|not asking for|not a request to)\s+(?:close|delet\w*|eras\w*)",
        r"(?:keep|leave) (?:the |my )?(?:account|profile).*(?:as it is|active|in place)",
        r"(?:marketing lists|promotional emails).*?(?:only|still|need)",
        r"(?:replace|correct|change).*?(?:phone|mobile|surname|email address)",
        r"(?:copy|download|portable format|what personal information).*?(?:still use|keep|leave|information request)",
        r"without removing any",
    )
    if any(re.search(p, lower) for p in negatives):
        return IntentAssessment(authorizes_deletion=False, uncertain=False, rationale="Explicit non-deletion request or negated authorization")
    positives = (r"delet\w*|eras\w*|clos(?:e|ed|ure|ing).*?account|account.*?clos(?:e|ed|ure|ing)",
                 r"remove.*?(?:profile|account|records|personal|details|reference)",
                 r"remove that search result|profile is gone|already been removed",
                 r"suppr(?:ession|imer)|elimin(?:ación|ar)|exclus[aã]o|削除|삭제")
    if any(re.search(p, lower) for p in positives):
        return IntentAssessment(authorizes_deletion=True, uncertain=False, rationale="Deletion or deletion verification requested")
    return IntentAssessment(authorizes_deletion=False, uncertain=True, rationale="Lexical baseline cannot establish authorization")


def authorized(text: str, interpreter: IntentInterpreter | None = None) -> bool:
    assessment = interpreter.assess_intent(text) if interpreter else baseline_intent(text)
    if assessment.uncertain:
        raise UnresolvedCase("Deletion intent requires semantic review")
    return assessment.authorizes_deletion


def account_audit_required(text: str) -> bool:
    """Broad account audits need account proof; clearly narrow requests do not.

    This is a conservative scope gate, not a rule that inserts account steps.
    Resource IDs still have to come from evidence or explicit relationships.
    """
    lower=text.casefold()
    account=re.search(r"\b(?:account|profile|cuenta|compte|conta|konto)\b|アカウント|계정",lower)
    narrow=re.search(r"\b(?:delete|remove) only (?:this |the |my )?(?:support )?(?:attachment|export|log|analytics record)\b",lower)
    return bool(account) or not bool(narrow)
