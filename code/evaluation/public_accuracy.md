# Public benchmark diagnosis

All 32 cases; previous is the saved 29/32 best-effort run. UNRESOLVED is an internal abstention, counted as an error. Support is evaluated against the supplied evidence at the cutoff, independently of reference agreement. Supported means within the observed resource universe; exhaustive global coverage is not established by this benchmark.

| Case | Expected | Previous | Current | Missing / extra | Op / state / resource / evidence errors | Reference support |
|---|---|---|---|---|---|---|
| case_01 | COMPLETE | UNRESOLVED | UNRESOLVED | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_02 | COMPLETE | UNRESOLVED | UNRESOLVED | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_03 | COMPLETE | COMPLETE | COMPLETE | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_04 | COMPLETE | UNRESOLVED | UNRESOLVED | 2 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_05 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_06 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_07 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 1 / 3 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_08 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_09 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 2 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_10 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_11 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_12 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_13 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_14 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_15 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_16 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_17 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 2 | 0 / 0 / 0 / 0 | REFERENCE_OMITS_SUPPORTED_STEPS |
| case_18 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 2 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_19 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 0 / 0 | 0 / 0 / 0 / 0 | SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE |
| case_20 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 2 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_21 | COMPLETE | COMPLETE | UNRESOLVED | 3 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_22 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_23 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 2 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_24 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_25 | COMPLETE | COMPLETE | UNRESOLVED | 3 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_26 | COMPLETE | COMPLETE | UNRESOLVED | 6 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_27 | COMPLETE | COMPLETE | UNRESOLVED | 6 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_28 | COMPLETE | COMPLETE | UNRESOLVED | 6 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_29 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 2 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_30 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 2 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_31 | COMPLETE | COMPLETE | UNRESOLVED | 3 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |
| case_32 | INCOMPLETE | INCOMPLETE | INCOMPLETE | 1 / 0 | 0 / 0 / 0 / 0 | UNSUPPORTED_RESOURCE_OR_CITATION |

## case_01

Exact row: False. Identity trace: `{"subject": "user_01", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-03T11:30:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_001 / ABSENT / evidence_54

Extra steps:

None.

- `account_001`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

The cited SQL snapshot has no subject-linked row identifying the expected absent account. A deletion-worker activity claim does not supply the missing subject/resource join or prove readback. Array position or numeric suffix cannot supply ownership.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_02

Exact row: False. Identity trace: `{"subject": "user_02", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-04T15:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_002 / ABSENT / evidence_54

Extra steps:

None.

- `account_002`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

The cited SQL snapshot has no subject-linked row identifying the expected absent account. A deletion-worker activity claim does not supply the missing subject/resource join or prove readback. Array position or numeric suffix cannot supply ownership.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_03

Exact row: False. Identity trace: `{"subject": "user_43", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-26T11:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_9406 / ANONYMIZED / evidence_94

Extra steps:

None.

- `analytics_9406`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "analytics_platform", "resource": "analytics_9406", "state": "ANONYMIZED", "evidence": "evidence_94", "observed_at": "2026-09-26T09:54:09Z", "available_at": "2026-09-26T10:38:56Z", "replica": "default"}]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_04

Exact row: False. Identity trace: `{"subject": "user_04", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-07T10:20:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_004 / ABSENT / evidence_54
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_901 / ANONYMIZED / evidence_56

Extra steps:

None.

- `account_004`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.
- `analytics_901`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "analytics_platform", "resource": "analytics_901", "state": "ANONYMIZED", "evidence": "evidence_56", "observed_at": "2026-09-07T09:45:00Z", "available_at": "2026-09-07T09:45:00Z", "replica": "default"}]`. Subject-bearing facts: `[]`.

The cited SQL snapshot has no subject-linked row identifying the expected absent account. A deletion-worker activity claim does not supply the missing subject/resource join or prove readback. Array position or numeric suffix cannot supply ownership.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_05

Exact row: True. Identity trace: `{"subject": "user_05", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-08T13:40:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_06

Exact row: True. Identity trace: `{"subject": "user_06", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-10T09:15:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_07

Exact row: False. Identity trace: `{"subject": "user_07", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-12T08:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_007 / ABSENT / (future)

Extra steps:

- FINDING / REPORT_REMAINING_RECORD / object_storage / object_19 / PRESENT / evidence_46
- REMEDIATION / DELETE_RECORD / object_storage / object_19 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_ABSENT / object_storage / object_19 / ABSENT / (future)

- `account_007`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

Extra steps cover independently linked resources omitted by the reference; removing them would reduce evidence coverage.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_08

Exact row: False. Identity trace: `{"subject": "user_08", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-14T16:10:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_008 / ABSENT / (future)

Extra steps:

None.

- `account_008`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_09

Exact row: False. Identity trace: `{"subject": "user_61", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-16T09:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_3960 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_4902 / PRESENT / (future)

Extra steps:

None.

- `account_3960`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "account_service", "resource": "account_3960", "state": "ABSENT", "evidence": "evidence_06", "observed_at": "2026-09-16T08:57:34Z", "available_at": "2026-09-18T11:55:24Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "account_service", "resource": "account_3960", "state": "ABSENT", "evidence": "evidence_06", "observed_at": "2026-09-16T08:57:34Z", "available_at": "2026-09-18T11:55:24Z", "replica": "default"}]`.
- `audit_record_4902`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "security_service", "resource": "audit_record_4902", "state": "PRESENT", "evidence": "evidence_06", "observed_at": "2026-09-16T08:52:59Z", "available_at": "2026-09-18T11:55:24Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "security_service", "resource": "audit_record_4902", "state": "PRESENT", "evidence": "evidence_06", "observed_at": "2026-09-16T08:52:59Z", "available_at": "2026-09-18T11:55:24Z", "replica": "default"}]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_10

Exact row: False. Identity trace: `{"subject": "user_10", "identifier_count": 8, "history_changes": 4, "request_uses_current_email": false, "audit_at": "2026-09-18T12:25:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_010 / ABSENT / (future)

Extra steps:

None.

- `account_010`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_11

Exact row: True. Identity trace: `{"subject": "user_32", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-10-01T12:00:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_12

Exact row: True. Identity trace: `{"subject": "user_12", "identifier_count": 6, "history_changes": 2, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_13

Exact row: True. Identity trace: `{"subject": "user_33", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-10-01T12:00:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_14

Exact row: True. Identity trace: `{"subject": "user_37", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-10-01T12:00:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_15

Exact row: True. Identity trace: `{"subject": "user_15", "identifier_count": 5, "history_changes": 1, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_16

Exact row: True. Identity trace: `{"subject": "user_53", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-21T10:00:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_17

Exact row: False. Identity trace: `{"subject": "user_17", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Missing steps:

None.

Extra steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_6523 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_REDACTED / identity_service / tombstone_17 / REDACTED / (future)


Extra steps cover independently linked resources omitted by the reference; removing them would reduce evidence coverage.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_18

Exact row: False. Identity trace: `{"subject": "user_50", "identifier_count": 5, "history_changes": 1, "request_uses_current_email": true, "audit_at": "2026-09-26T11:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5521 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_6645 / PRESENT / (future)

Extra steps:

None.

- `account_5521`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.
- `audit_record_6645`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_19

Exact row: True. Identity trace: `{"subject": "user_19", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.
Missing steps:

None.

Extra steps:

None.


Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_20

Exact row: False. Identity trace: `{"subject": "user_48", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-26T11:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5037 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_5569 / PRESENT / (future)

Extra steps:

None.

- `account_5037`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.
- `audit_record_5569`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_21

Exact row: False. Identity trace: `{"subject": "user_21", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Status regression: corrected unsupported completion inference; no new source-supported defect found.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_6440 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_3737 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_5335 / ANONYMIZED / evidence_92

Extra steps:

None.

- `account_6440`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "account_service", "resource": "account_6440", "state": "ABSENT", "evidence": "evidence_92", "observed_at": "2026-09-15T09:31:19Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.
- `analytics_5335`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "analytics_platform", "resource": "analytics_5335", "state": "ANONYMIZED", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}, {"system": "analytics_platform", "resource": "analytics_5335", "state": "ANONYMIZED", "evidence": "evidence_92", "observed_at": "2026-09-15T09:34:42Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_22

Exact row: False. Identity trace: `{"subject": "user_51", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-21T10:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_4990 / ABSENT / (future)

Extra steps:

None.

- `account_4990`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_23

Exact row: False. Identity trace: `{"subject": "user_23", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_410 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_4128 / PRESENT / (future)

Extra steps:

None.

- `account_410`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.
- `audit_record_4128`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "security_service", "resource": "audit_record_4128", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "security_service", "resource": "audit_record_4128", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_24

Exact row: False. Identity trace: `{"subject": "user_24", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_7095 / PRESENT / (future)

Extra steps:

None.

- `audit_record_7095`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "security_service", "resource": "audit_record_7095", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "security_service", "resource": "audit_record_7095", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_25

Exact row: False. Identity trace: `{"subject": "user_25", "identifier_count": 5, "history_changes": 1, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Status regression: corrected unsupported completion inference; no new source-supported defect found.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_3136 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_451 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_1895 / ANONYMIZED / evidence_92

Extra steps:

None.

- `account_3136`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "account_service", "resource": "account_3136", "state": "ABSENT", "evidence": "evidence_92", "observed_at": "2026-09-15T09:31:40Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.
- `analytics_1895`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "analytics_platform", "resource": "analytics_1895", "state": "ANONYMIZED", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}, {"system": "analytics_platform", "resource": "analytics_1895", "state": "ANONYMIZED", "evidence": "evidence_92", "observed_at": "2026-09-15T09:58:44Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_26

Exact row: False. Identity trace: `{"subject": "user_26", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Status regression: corrected unsupported completion inference; no new source-supported defect found.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5684 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_5416 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_REDACTED / support_platform / support_4715 / REDACTED / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_4566 / ANONYMIZED / evidence_92
- VERIFICATION / VERIFY_DATA_FLOW_DISABLED / integration_service / data_flow_6244 / DISABLED / evidence_92
- VERIFICATION / VERIFY_RESTORE_BLOCKED / backup_service / backup_3120 / BLOCKED / evidence_92

Extra steps:

None.

- `account_5684`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "account_service", "resource": "account_5684", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-09T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}, {"system": "account_service", "resource": "account_5684", "state": "ABSENT", "evidence": "evidence_92", "observed_at": "2026-09-15T09:01:48Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "account_service", "resource": "account_5684", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-09T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`.
- `analytics_4566`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "analytics_platform", "resource": "analytics_4566", "state": "ANONYMIZED", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}, {"system": "analytics_platform", "resource": "analytics_4566", "state": "ANONYMIZED", "evidence": "evidence_92", "observed_at": "2026-09-15T11:29:16Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_27

Exact row: False. Identity trace: `{"subject": "user_27", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Status regression: corrected unsupported completion inference; no new source-supported defect found.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_3866 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_3830 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_REDACTED / support_platform / support_4707 / REDACTED / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_4574 / ANONYMIZED / evidence_92
- VERIFICATION / VERIFY_DATA_FLOW_DISABLED / integration_service / data_flow_2295 / DISABLED / evidence_92
- VERIFICATION / VERIFY_RESTORE_BLOCKED / backup_service / backup_5970 / BLOCKED / evidence_92

Extra steps:

None.

- `account_3866`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "account_service", "resource": "account_3866", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-17T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}, {"system": "account_service", "resource": "account_3866", "state": "ABSENT", "evidence": "evidence_92", "observed_at": "2026-09-15T09:59:48Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "account_service", "resource": "account_3866", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-17T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`.
- `analytics_4574`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "analytics_platform", "resource": "analytics_4574", "state": "ANONYMIZED", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}, {"system": "analytics_platform", "resource": "analytics_4574", "state": "ANONYMIZED", "evidence": "evidence_92", "observed_at": "2026-09-15T10:07:38Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.

evidence_92 contains an anonymous absent account. The subject-bearing account link in evidence_02 is first available September 17, after the September 15 cutoff. It cannot backdate ownership.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_28

Exact row: False. Identity trace: `{"subject": "user_28", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Status regression: corrected unsupported completion inference; no new source-supported defect found.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5482 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_9265 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_REDACTED / support_platform / support_2351 / REDACTED / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_6077 / ANONYMIZED / evidence_92
- VERIFICATION / VERIFY_DATA_FLOW_DISABLED / integration_service / data_flow_2337 / DISABLED / evidence_92
- VERIFICATION / VERIFY_RESTORE_BLOCKED / backup_service / backup_838 / BLOCKED / evidence_92

Extra steps:

None.

- `account_5482`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "account_service", "resource": "account_5482", "state": "ABSENT", "evidence": "evidence_92", "observed_at": "2026-09-15T11:07:16Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.
- `analytics_6077`: RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN. Observed resource facts: `[{"system": "analytics_platform", "resource": "analytics_6077", "state": "ANONYMIZED", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}, {"system": "analytics_platform", "resource": "analytics_6077", "state": "ANONYMIZED", "evidence": "evidence_92", "observed_at": "2026-09-15T11:44:55Z", "available_at": "2026-09-15T11:44:55Z", "replica": "default"}]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_29

Exact row: False. Identity trace: `{"subject": "user_29", "identifier_count": 6, "history_changes": 2, "request_uses_current_email": false, "audit_at": "2026-09-15T12:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_7012 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_3954 / PRESENT / (future)

Extra steps:

None.

- `account_7012`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.
- `audit_record_3954`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "security_service", "resource": "audit_record_3954", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "security_service", "resource": "audit_record_3954", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_30

Exact row: False. Identity trace: `{"subject": "user_30", "identifier_count": 6, "history_changes": 2, "request_uses_current_email": false, "audit_at": "2026-09-15T12:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_4163 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_1707 / PRESENT / (future)

Extra steps:

None.

- `account_4163`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.
- `audit_record_1707`: OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE. Observed resource facts: `[{"system": "security_service", "resource": "audit_record_1707", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`. Subject-bearing facts: `[{"system": "security_service", "resource": "audit_record_1707", "state": "PRESENT", "evidence": "evidence_02", "observed_at": "2026-09-15T12:00:00Z", "available_at": "2026-09-17T12:00:00Z", "replica": "default"}]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_31

Exact row: False. Identity trace: `{"subject": "user_541", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Status regression: corrected unsupported completion inference; no new source-supported defect found.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_4857 / ABSENT / evidence_51
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_6909 / PRESENT / evidence_51
- VERIFICATION / VERIFY_RECORD_REDACTED / identity_service / tombstone_440 / REDACTED / evidence_51

Extra steps:

None.

- `account_4857`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

evidence_51 proves the redacted tombstone and retained audit record. Its empty customer_profiles array is a partial JSON snapshot with no account_4857 row or scoped subject query; it cannot establish primary-account absence.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.

## case_32

Exact row: False. Identity trace: `{"subject": "user_542", "identifier_count": 4, "history_changes": 0, "request_uses_current_email": true, "audit_at": "2026-09-15T12:00:00Z"}`.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_8858 / ABSENT / (future)

Extra steps:

None.

- `account_8858`: NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN. Observed resource facts: `[]`. Subject-bearing facts: `[]`.

Paired field mismatches: `{"phase": [], "operation": [], "system_id": [], "resource_id": [], "state": [], "evidence_id": []}`. Relative order wrong: False.
