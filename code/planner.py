"""Pure canonical planning; models cannot write submission steps."""
from __future__ import annotations

from policy import Policy
from schema import OPERATIONS, Observation, UnresolvedCase, step_key


def plan(observations: list[Observation], policy: Policy, cutoff: str) -> tuple[str, list[dict]]:
    if not observations:
        raise UnresolvedCase("No admissible resource observations")
    findings, remediation, verification = [], [], []

    def make(phase, op, obs, evidence=""):
        return dict(step_no=0, phase=phase, system_id=obs.system_id, resource_id=obs.resource_id,
                    operation=op, state=OPERATIONS[phase][op], evidence_id=evidence)

    unknown=[]
    deletion_proof=False
    for obs in observations:
        finding, action, check, required = policy.treatment(obs, cutoff)
        if obs.state == "UNKNOWN":
            # A proven resource link can justify a required FUTURE check. It
            # cannot justify a finding, a destructive action, or completion.
            unknown.append(obs.resource_id)
            verification.append(make("VERIFICATION",check,obs))
            continue
        deletion_proof |= required in {"ABSENT","REDACTED","ANONYMIZED"}
        if obs.state != required:
            if not finding:
                raise UnresolvedCase(f"Required retained record missing: {obs.resource_id}")
            findings.append(make("FINDING", finding, obs, obs.evidence_id))
            remediation.append(make("REMEDIATION", action, obs))
        verification.append(make("VERIFICATION", check, obs, obs.evidence_id))
    incomplete = bool(findings)
    if not incomplete and unknown:
        raise UnresolvedCase("Resource states remain unproven: "+", ".join(sorted(unknown)))
    if not incomplete and not deletion_proof:
        raise UnresolvedCase("Retained records or disabled processes alone do not establish deletion completion")
    if incomplete:
        for step in verification:
            step["evidence_id"] = ""
    steps = sorted(findings + remediation + verification, key=step_key)
    for i, step in enumerate(steps, 1):
        step["step_no"] = i
    return ("INCOMPLETE" if incomplete else "COMPLETE"), steps
