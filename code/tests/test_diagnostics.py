from evaluation.diagnostics import compare_case


def step(rid="account_alpha",op="VERIFY_RECORD_ABSENT",state="ABSENT",evidence="synthetic_1",number=1):
    return dict(step_no=number,phase="VERIFICATION",system_id="account_service",resource_id=rid,
                operation=op,state=state,evidence_id=evidence)


def row(steps):return dict(case_id="synthetic_case",deletion_status="COMPLETE",steps=steps)


def test_field_mismatches_are_paired_without_double_counting_missing_steps():
    expected=row([step()])
    actual=row([step(op="VERIFY_RECORD_PRESENT",state="PRESENT",evidence="synthetic_2")])
    result=compare_case(expected,actual)
    assert not result["missing_steps"] and not result["extra_steps"]
    assert len(result["mismatches"]["operation"])==1
    assert len(result["mismatches"]["state"])==1
    assert len(result["mismatches"]["evidence_id"])==1


def test_wrong_resource_is_reported_separately():
    result=compare_case(row([step()]),row([step(rid="account_beta")]))
    assert len(result["mismatches"]["resource_id"])==1
    assert not result["missing_steps"]


def test_reordering_does_not_become_resource_mismatches():
    result=compare_case(row([step(),step(rid="account_beta",number=2)]),
                        row([step(rid="account_beta"),step(number=2)]))
    assert result["relative_order_wrong"]
    assert not result["mismatches"]["resource_id"]
