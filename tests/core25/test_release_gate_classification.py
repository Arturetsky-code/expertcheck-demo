from core25.release_gate import classify_failed_nodeids


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
