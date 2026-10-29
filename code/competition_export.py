"""Explicit competition-only fallback; never changes strict audit conclusions."""
from __future__ import annotations

from assessor import authorized
from schema import OPERATIONS, UnresolvedCase, step_key
from state_resolver import resolve


def build_export(pipeline, requests: list[dict], strict_rows: list[dict], unresolved: list[dict]):
    """Keep resolved rows; map authorized uncertainty to unverified INCOMPLETE.

    Fallback checks describe future policy obligations, not current-state proof.
    They carry no citations, findings or destructive actions. The sidecar retains
    actual supporting resource observations and the original strict failure.
    """
    rows = list(strict_rows)
    queries = {q["case_id"]: q for q in requests}
    fallbacks = []
    for failure in unresolved:
        q = queries[failure["case_id"]]
        # Unknown intent must still block publication. Never turn it into a
        # confident NOT_APPLICABLE or an invented deletion authorization.
        if not authorized(q["request_text"], pipeline.model):
            raise UnresolvedCase("Competition fallback requires confirmed deletion authorization")
        observations = []
        omissions = []
        try:
            _, values = pipeline.identity.resolve(q["email"], q["audit_at"])
            observations = resolve(pipeline.store, values, q["audit_at"], pipeline.activity)
        except UnresolvedCase as error:
            omissions.append(str(error))
        # Model disagreement is not permission to publish disputed semantics.
        if "Semantic interpretation" in failure["reason"]:
            observations = []
            omissions.append("Disputed semantic interpretation omitted")
        checks = []
        support = []
        for observation in observations:
            try:
                _, _, check, required = pipeline.policy.treatment(observation, q["audit_at"])
            except UnresolvedCase as error:
                omissions.append(str(error))
                continue
            checks.append(dict(step_no=0, phase="VERIFICATION", system_id=observation.system_id,
                resource_id=observation.resource_id, operation=check, state=required, evidence_id=""))
            support.append(dict(system_id=observation.system_id, resource_id=observation.resource_id,
                observed_state=observation.state, evidence_id=observation.evidence_id,
                observed_at=observation.observed_at, available_at=observation.available_at))
        checks.sort(key=step_key)
        for number, check in enumerate(checks, 1):
            check["step_no"] = number
            assert check["state"] == OPERATIONS["VERIFICATION"][check["operation"]]
        rows.append(dict(case_id=q["case_id"], deletion_status="INCOMPLETE", steps=checks))
        fallbacks.append(dict(case_id=q["case_id"], deletion_status="INCOMPLETE", unverified_fallback=True,
            strict_reason=failure["reason"], step_count=len(checks), resource_support=support,
            omissions=omissions, meaning="Completion unverified; not a confirmed policy violation or canonical label"))
    return sorted(rows, key=lambda r: r["case_id"]), fallbacks
