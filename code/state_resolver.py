"""Resolve admissible observations independently for each replica."""
from __future__ import annotations

from collections import defaultdict

from identity import identifiers
from schema import Observation, UnresolvedCase, timestamp


def admissible(observation, cutoff: str) -> bool:
    at = timestamp(cutoff)
    return timestamp(observation.available_at) <= at and timestamp(observation.observed_at) <= at


def resolve(store, identity_values: set[str], cutoff: str, activity: list[dict]) -> list[Observation]:
    keys = set()
    for value in identity_values:
        keys.update(store.by_identifier.get(value, set()))
    # Content association must itself exist before the cutoff.
    keys = {key for key in keys if any(admissible(o, cutoff) and identity_values.intersection(o.identifiers)
                                      for o in store.by_resource[key])}
    for event in activity:
        if event["event_type"] == "LINK_RESOURCE_IDENTITY" and timestamp(event["event_time"]) <= timestamp(cutoff):
            if identity_values.intersection(identifiers(event["details"])):
                keys.add((event["target_system"], event["resource_id"]))
    links=[link for link in getattr(store,"links",()) if admissible(link,cutoff)]
    linked={}
    changed=True
    while changed:
        changed=False
        for link in links:
            source=(link.source_system,link.source_resource)
            target=(link.target_system,link.target_resource)
            if source in keys and target not in keys:
                keys.add(target);linked[target]=link;changed=True
            # A derived personal record and its explicit owning source share the
            # subject. This also retrieves identifier-free downstream copies.
            if target in keys and source not in keys:
                keys.add(source);changed=True
    result = []
    for key in sorted(keys):
        candidates = [o for o in store.by_resource.get(key, []) if admissible(o, cutoff)]
        if not candidates:
            if key in linked:
                link=linked[key]
                result.append(Observation(system_id=key[0],resource_id=key[1],category=link.target_category,
                    state="UNKNOWN",observed_at=link.observed_at,available_at=link.available_at,
                    evidence_id=link.evidence_id,fields={"state_unproven":True,"link_field":link.field_path}))
                continue
            raise UnresolvedCase(f"Catalog-linked resource has no admissible state proof: {key[1]}")
        per_replica = defaultdict(list)
        for obs in candidates:
            per_replica[obs.replica].append(obs)
        # An explicit complete SQL table can prove absence of a previously linked resource.
        for scope in store.scopes:
            if not scope.complete:
                continue
            if scope.system_id == key[0] and admissible(scope, cutoff) and key[1] not in scope.resource_ids:
                if scope.evidence_id not in {o.evidence_id for o in candidates}:
                    continue  # A different export may have a different subject scope.
                template = candidates[-1]
                if scope.category != template.category:
                    continue
                per_replica[scope.replica].append(template.model_copy(update=dict(
                    state="ABSENT", observed_at=scope.observed_at, available_at=scope.available_at,
                    evidence_id=scope.evidence_id, replica=scope.replica, fields={})))
        current = []
        for replica, history in per_replica.items():
            # A metadata-only read does not measure restore permission and must
            # not supersede an independent earlier authorization observation.
            measured=[o for o in history if o.state!="UNKNOWN"]
            if measured and all(o.state!="UNKNOWN" or o.fields.get("unknown_fields")==["restore_allowed"] for o in history):
                history=measured
            latest_time = max(timestamp(o.observed_at) for o in history)
            latest = [o for o in history if timestamp(o.observed_at) == latest_time]
            states = {o.state for o in latest}
            if len(states) > 1:
                raise UnresolvedCase(f"Contradictory simultaneous observations for {key[1]} in {replica}")
            current.append(sorted(latest, key=lambda o: (timestamp(o.available_at), o.evidence_id))[-1])
        # A later direct read of a service does not prove that independent replicas are clean.
        violations = [o for o in current if o.state in {"PRESENT", "ACTIVE"}]
        unresolved=[o for o in current if o.state=="UNKNOWN"]
        chosen = max(violations or unresolved or current, key=lambda o: (timestamp(o.observed_at), timestamp(o.available_at), o.evidence_id))
        result.append(chosen)
    return result
