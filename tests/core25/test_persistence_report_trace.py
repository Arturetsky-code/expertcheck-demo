from core25 import verify_assignment
from core25.contracts import DecisionState, Domain, Evidence25, Requirement25, Scope
from core25.persistence import dump_result, load_result
from core25.report_trace import report_trace_row


def _categorical_result():
    requirement = Requirement25(
        requirement_id="SHIFT-PERSIST",
        domain=Domain.ASSIGNMENT,
        text="Продолжительность смены 12 часов",
        scope=Scope.PROJECT_GLOBAL,
        verification_kind="TYPED_VALUE",
        parameter_code="SHIFT_DURATION",
        required_value=12.0,
        unit="час",
        expected_sections=("ТХ",),
    )
    evidence = Evidence25(
        evidence_id="E-SHIFT-PERSIST",
        document="ТХ.pdf",
        section="ТХ",
        page=7,
        fragment="Продолжительность смены составляет 12 часов.",
        addressable=True,
        source_kind="PAGE_TEXT",
        metadata={"parameter_code": "SHIFT_DURATION", "value": 12.0, "unit": "час"},
    )
    return verify_assignment((requirement,), (evidence,), {})[0]


def test_persistence_roundtrip_preserves_canonical_trace():
    original = _categorical_result()
    restored = load_result(dump_result(original))

    assert restored.decision.state is DecisionState.COMPLIANT
    assert restored.trace.is_categorical_trace_valid() is True
    assert restored.trace.proof.proof_id == original.trace.proof.proof_id
    assert restored.trace.proof.evidence_ids == original.trace.proof.evidence_ids
    assert restored.trace.proof.binding_ids == original.trace.proof.binding_ids
    assert restored.trace.evidence[0].document == "ТХ.pdf"
    assert restored.trace.evidence[0].page == 7
    assert "12 часов" in restored.trace.evidence[0].fragment


def test_report_trace_row_is_auditable_and_sanitized():
    result = _categorical_result()
    row = report_trace_row(result)

    assert row["decision"] == "COMPLIANT"
    assert row["proof_id"] == result.trace.proof.proof_id
    assert row["evidence_id"] == "E-SHIFT-PERSIST"
    assert row["binding_id"]
    assert row["document"] == "ТХ.pdf"
    assert row["page"] == 7
    assert "12 часов" in row["fragment"]
    assert "nan" not in str(row).casefold()
