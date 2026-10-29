"""Exact, timestamped identity joins. Similar-looking email addresses never join."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict

from schema import UnresolvedCase, timestamp

EMAIL_RE = re.compile(r"\b[\w][\w.!#$%&'*+/=?^`{|}~-]*@[\w.-]+\.[A-Za-z]{2,}")
USER_RE = re.compile(r"\buser_\d+\b", re.I)
HASH_RE = re.compile(r"\b[0-9a-f]{64}\b", re.I)
PHONE_RE = re.compile(r"\+\d[\d ()-]{7,}\d")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    if value.startswith("+"):
        return re.sub(r"\D", "", value)
    return value


def identifiers(value: object) -> set[str]:
    if isinstance(value, dict):
        return set().union(*(identifiers(v) for v in value.values())) if value else set()
    if isinstance(value, (list, tuple)):
        return set().union(*(identifiers(v) for v in value)) if value else set()
    text = str(value)
    return {normalize(m.group()) for pattern in (EMAIL_RE, USER_RE, HASH_RE, PHONE_RE)
            for m in pattern.finditer(text)}


class IdentityIndex:
    def __init__(self, users: list[dict], history: list[dict]):
        self.users = {r["user_id"]: r for r in users}
        self.history = defaultdict(list)
        self.email_candidates = defaultdict(set)
        for row in users:
            self.email_candidates[normalize(row["email"])].add(row["user_id"])
        for row in history:
            self.history[row["user_id"]].append(row)
            if row["field_name"] == "email":
                for k in ("old_value", "new_value"):
                    self.email_candidates[normalize(row[k])].add(row["user_id"])

    def values_at(self, user_id: str, cutoff: str) -> set[str]:
        row = dict(self.users[user_id])
        changes = sorted(self.history[user_id], key=lambda r: timestamp(r["event_time"]), reverse=True)
        # Roll future changes back before collecting historical values.
        for change in changes:
            if timestamp(change["event_time"]) > timestamp(cutoff):
                row[change["field_name"]] = change["old_value"]
        values = {normalize(user_id)}
        for k in ("email", "phone", "email_hash"):
            if row.get(k):
                values.add(normalize(row[k]))
        for change in changes:
            if timestamp(change["event_time"]) <= timestamp(cutoff) and change["field_name"] in ("email", "phone", "email_hash"):
                values.update(normalize(change[k]) for k in ("old_value", "new_value"))
        values.update(hashlib.sha256(v.encode()).hexdigest() for v in list(values) if "@" in v)
        return values

    def resolve(self, email: str, cutoff: str) -> tuple[str, set[str]]:
        email = normalize(email)
        candidates = [u for u in self.email_candidates[email] if email in self.values_at(u, cutoff)]
        if len(candidates) != 1:
            raise UnresolvedCase(f"Identity resolution expected one subject; found {len(candidates)}")
        user = candidates[0]
        return user, self.values_at(user, cutoff)
