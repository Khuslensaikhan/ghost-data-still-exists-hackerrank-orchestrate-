# Public case-by-case comparison — current corrected strict pipeline

All 32 examples are included. Step alignment matches exact semantic steps before pairing a shared resource or operation. Missing/extra counts below exclude paired field mismatches; the benchmark's raw multiset missing/extra counts include them. This diagnostic alignment does not affect predictions or scores.

| Case | Reference → prediction | Exact row | Missing | Extra | Wrong operation | Resource ID | State | Evidence ID | Order |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| case_01 | COMPLETE → UNRESOLVED | no | 1 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_02 | COMPLETE → UNRESOLVED | no | 1 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_03 | COMPLETE → COMPLETE | no | 1 | 0 | 0 | 0 | 0 | 0 | valid |
| case_04 | COMPLETE → UNRESOLVED | no | 2 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_05 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_06 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_07 | INCOMPLETE → INCOMPLETE | no | 1 | 3 | 0 | 0 | 0 | 0 | valid |
| case_08 | INCOMPLETE → INCOMPLETE | no | 1 | 0 | 0 | 0 | 0 | 0 | valid |
| case_09 | INCOMPLETE → INCOMPLETE | no | 2 | 0 | 0 | 0 | 0 | 0 | valid |
| case_10 | INCOMPLETE → INCOMPLETE | no | 1 | 0 | 0 | 0 | 0 | 0 | valid |
| case_11 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_12 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_13 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_14 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_15 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_16 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_17 | INCOMPLETE → INCOMPLETE | no | 0 | 2 | 0 | 0 | 0 | 0 | valid |
| case_18 | INCOMPLETE → INCOMPLETE | no | 2 | 0 | 0 | 0 | 0 | 0 | valid |
| case_19 | INCOMPLETE → INCOMPLETE | yes | 0 | 0 | 0 | 0 | 0 | 0 | valid |
| case_20 | INCOMPLETE → INCOMPLETE | no | 2 | 0 | 0 | 0 | 0 | 0 | valid |
| case_21 | COMPLETE → UNRESOLVED | no | 3 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_22 | INCOMPLETE → INCOMPLETE | no | 1 | 0 | 0 | 0 | 0 | 0 | valid |
| case_23 | INCOMPLETE → INCOMPLETE | no | 2 | 0 | 0 | 0 | 0 | 0 | valid |
| case_24 | INCOMPLETE → INCOMPLETE | no | 1 | 0 | 0 | 0 | 0 | 0 | valid |
| case_25 | COMPLETE → UNRESOLVED | no | 3 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_26 | COMPLETE → UNRESOLVED | no | 6 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_27 | COMPLETE → UNRESOLVED | no | 6 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_28 | COMPLETE → UNRESOLVED | no | 6 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_29 | INCOMPLETE → INCOMPLETE | no | 2 | 0 | 0 | 0 | 0 | 0 | valid |
| case_30 | INCOMPLETE → INCOMPLETE | no | 2 | 0 | 0 | 0 | 0 | 0 | valid |
| case_31 | COMPLETE → UNRESOLVED | no | 3 | 0 | 0 | 0 | 0 | 0 | n/a |
| case_32 | INCOMPLETE → INCOMPLETE | no | 1 | 0 | 0 | 0 | 0 | 0 | valid |

## case_01

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_001 / ABSENT / evidence_54

Extra steps:

None.

Paired field mismatches:

None.

## case_02

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_002 / ABSENT / evidence_54

Extra steps:

None.

Paired field mismatches:

None.

## case_03

Status: COMPLETE → COMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_9406 / ANONYMIZED / evidence_94

Extra steps:

None.

Paired field mismatches:

None.

## case_04

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_004 / ABSENT / evidence_54
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_901 / ANONYMIZED / evidence_56

Extra steps:

None.

Paired field mismatches:

None.

## case_05

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_06

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_07

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_007 / ABSENT / (future)

Extra steps:

- FINDING / REPORT_REMAINING_RECORD / object_storage / object_19 / PRESENT / evidence_46
- REMEDIATION / DELETE_RECORD / object_storage / object_19 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_ABSENT / object_storage / object_19 / ABSENT / (future)

Paired field mismatches:

None.

## case_08

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_008 / ABSENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_09

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_3960 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_4902 / PRESENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_10

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_010 / ABSENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_11

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_12

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_13

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_14

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_15

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_16

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_17

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

None.

Extra steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_6523 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_REDACTED / identity_service / tombstone_17 / REDACTED / (future)

Paired field mismatches:

None.

## case_18

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5521 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_6645 / PRESENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_19

Status: INCOMPLETE → INCOMPLETE; exact row: True.

Missing steps:

None.

Extra steps:

None.

Paired field mismatches:

None.

## case_20

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5037 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_5569 / PRESENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_21

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_6440 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_3737 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_5335 / ANONYMIZED / evidence_92

Extra steps:

None.

Paired field mismatches:

None.

## case_22

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_4990 / ABSENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_23

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_410 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_4128 / PRESENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_24

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_7095 / PRESENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_25

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_3136 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_451 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_1895 / ANONYMIZED / evidence_92

Extra steps:

None.

Paired field mismatches:

None.

## case_26

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5684 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_5416 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_REDACTED / support_platform / support_4715 / REDACTED / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_4566 / ANONYMIZED / evidence_92
- VERIFICATION / VERIFY_DATA_FLOW_DISABLED / integration_service / data_flow_6244 / DISABLED / evidence_92
- VERIFICATION / VERIFY_RESTORE_BLOCKED / backup_service / backup_3120 / BLOCKED / evidence_92

Extra steps:

None.

Paired field mismatches:

None.

## case_27

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_3866 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_3830 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_REDACTED / support_platform / support_4707 / REDACTED / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_4574 / ANONYMIZED / evidence_92
- VERIFICATION / VERIFY_DATA_FLOW_DISABLED / integration_service / data_flow_2295 / DISABLED / evidence_92
- VERIFICATION / VERIFY_RESTORE_BLOCKED / backup_service / backup_5970 / BLOCKED / evidence_92

Extra steps:

None.

Paired field mismatches:

None.

## case_28

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_5482 / ABSENT / evidence_92
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_9265 / PRESENT / evidence_92
- VERIFICATION / VERIFY_RECORD_REDACTED / support_platform / support_2351 / REDACTED / evidence_92
- VERIFICATION / VERIFY_RECORD_ANONYMIZED / analytics_platform / analytics_6077 / ANONYMIZED / evidence_92
- VERIFICATION / VERIFY_DATA_FLOW_DISABLED / integration_service / data_flow_2337 / DISABLED / evidence_92
- VERIFICATION / VERIFY_RESTORE_BLOCKED / backup_service / backup_838 / BLOCKED / evidence_92

Extra steps:

None.

Paired field mismatches:

None.

## case_29

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_7012 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_3954 / PRESENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_30

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_4163 / ABSENT / (future)
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_1707 / PRESENT / (future)

Extra steps:

None.

Paired field mismatches:

None.

## case_31

Status: COMPLETE → UNRESOLVED; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_4857 / ABSENT / evidence_51
- VERIFICATION / VERIFY_RECORD_PRESENT / security_service / audit_record_6909 / PRESENT / evidence_51
- VERIFICATION / VERIFY_RECORD_REDACTED / identity_service / tombstone_440 / REDACTED / evidence_51

Extra steps:

None.

Paired field mismatches:

None.

## case_32

Status: INCOMPLETE → INCOMPLETE; exact row: False.

Missing steps:

- VERIFICATION / VERIFY_RECORD_ABSENT / account_service / account_8858 / ABSENT / (future)

Extra steps:

None.

Paired field mismatches:

None.
