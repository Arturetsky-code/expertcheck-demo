from core25 import verify_assignment
from core25.contracts import DecisionState, Domain, Evidence25, Requirement25, Scope


def _requirements():
    return (
        Requirement25(
            requirement_id="SHIFT",
            domain=Domain.ASSIGNMENT,
            text="Продолжительность смены 12 часов",
            scope=Scope.PROJECT_GLOBAL,
            verification_kind="TYPED_VALUE",
            parameter_code="SHIFT_DURATION",
            required_value=12.0,
            unit="час",
            expected_sections=("ТХ",),
        ),
        Requirement25(
            requirement_id="AREA-LAB",
            domain=Domain.ASSIGNMENT,
            text="Площадь здания проборазделки 89,9 м2",
            scope=Scope.OBJECT_SPECIFIC,
            target_object_id="OBJ-LAB",
            verification_kind="TYPED_VALUE",
            parameter_code="AREA",
            required_value=89.9,
            unit="м2",
            expected_sections=("АР",),
        ),
        Requirement25(
            requirement_id="SEMANTIC",
            domain=Domain.ASSIGNMENT,
            text="Обеспечить удобство эксплуатации",
            scope=Scope.UNRESOLVED,
            verification_kind="SEMANTIC_UNSUPPORTED",
        ),
    )


def _evidence():
    return (
        Evidence25(
            evidence_id="E-SHIFT",
            document="ТХ.pdf",
            section="ТХ",
            page=7,
            fragment="Продолжительность смены составляет 12 часов.",
            addressable=True,
            source_kind="PAGE_TEXT",
            metadata={
                "parameter_code": "SHIFT_DURATION",
                "value": 12.0,
                "unit": "час",
            },
        ),
        Evidence25(
            evidence_id="E-DUST-AREA",
            document="АР.pdf",
            section="АР",
            page=12,
            fragment="Модуль обеспыливания. Площадь 23,5 м2.",
            addressable=True,
            source_kind="PAGE_TEXT",
            metadata={
                "owner_name": "Модуль обеспыливания",
                "parameter_code": "AREA",
                "value": 23.5,
                "unit": "м2",
            },
        ),
    )


def _objects():
    return {
        "OBJ-LAB": ("Здание проборазделки", "Проборазделка"),
        "OBJ-DUST": ("Модуль обеспыливания",),
    }


def test_pipeline_rejects_wrong_owner_and_does_not_create_mismatch():
    results = verify_assignment(_requirements(), _evidence(), _objects())
    area = next(x for x in results if x.requirement.requirement_id == "AREA-LAB")

    assert area.decision.state is DecisionState.REVIEW
    assert all(
        binding.owner_id != "OBJ-LAB" or binding.state.value != "BOUND"
        for binding in area.trace.bindings
    )
    assert area.trace.proof.is_categorical is False


def test_pipeline_traces_categorical_result_to_document_page_fragment():
    results = verify_assignment(_requirements(), _evidence(), _objects())
    shift = next(x for x in results if x.requirement.requirement_id == "SHIFT")

    assert shift.decision.state is DecisionState.COMPLIANT
    assert shift.trace.is_categorical_trace_valid() is True
    assert shift.trace.evidence[0].document == "ТХ.pdf"
    assert shift.trace.evidence[0].page == 7
    assert "12 часов" in shift.trace.evidence[0].fragment


def test_unsupported_semantic_requirement_is_review_not_false_success():
    results = verify_assignment(_requirements(), _evidence(), _objects())
    semantic = next(x for x in results if x.requirement.requirement_id == "SEMANTIC")

    assert semantic.decision.state is DecisionState.REVIEW
    assert semantic.trace.proof.is_categorical is False
