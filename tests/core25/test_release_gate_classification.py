from core25.release_gate import classify_failed_nodeids, failed_nodeids_from_pytest_output


def test_release_gate_classifies_only_explicit_legacy_diagnostics():
    failures = (
        "test_general_plan_engine.py::test_dsk_general_plan_explication_is_extracted",
        "test_release_version_152a1.py::test_ui_and_core_identify_release_160",
        "test_new_current_contract.py::test_unexpected_regression",
    )

    result = classify_failed_nodeids(failures)

    assert result["fixture_bound"] == (
        "test_general_plan_engine.py::test_dsk_general_plan_explication_is_extracted",
    )
    assert result["obsolete"] == (
        "test_release_version_152a1.py::test_ui_and_core_identify_release_160",
    )
    assert result["blockers"] == (
        "test_new_current_contract.py::test_unexpected_regression",
    )


def test_release_gate_never_allows_unknown_failure():
    result = classify_failed_nodeids(("unknown.py::test_something",))
    assert result["blockers"] == ("unknown.py::test_something",)


def test_release_gate_separates_baseline_existing_debt_from_new_regressions():
    result = classify_failed_nodeids((
        "test_cross_section_proof_th.py::test_two_control_sections_cannot_replace_missing_th_owner",
    ))
    assert result["baseline_existing"] == (
        "test_cross_section_proof_th.py::test_two_control_sections_cannot_replace_missing_th_owner",
    )
    assert result["blockers"] == ()


def test_release_gate_extracts_pytest_failed_nodeids_without_duplicates():
    output = """
FAILED test_old.py::test_a - AssertionError
FAILED test_old.py::test_a - AssertionError
FAILED test_new.py::test_b - ValueError
32 failed, 494 passed in 9.66s
"""
    assert failed_nodeids_from_pytest_output(output) == (
        "test_old.py::test_a",
        "test_new.py::test_b",
    )
