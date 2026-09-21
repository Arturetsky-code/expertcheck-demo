from core25.binding import bind_evidence
from core25.contracts import BindingState, Domain, Evidence25, Requirement25, Scope


OBJECTS = {
    "OBJ-LAB": ("здание проборазделки", "проборазделка"),
    "OBJ-DUST": ("модуль обеспыливания", "обеспыливание"),
}


def test_wrong_owner_cannot_bind_same_parameter():
    req = Requirement25(
        requirement_id="R1",
        domain=Domain.ASSIGNMENT,
        text="Площадь здания проборазделки 89,9 м2",
        scope=Scope.OBJECT_SPECIFIC,
        target_object_id="OBJ-LAB",
        verification_kind="TYPED_VALUE",
        parameter_code="AREA",
    )
    ev = Evidence25(
        evidence_id="E1",
        document="АР.pdf",
        page=12,
        fragment="Модуль обеспыливания. Площадь 23,5 м2",
        addressable=True,
        metadata={"owner_name": "Модуль обеспыливания", "parameter_code": "AREA"},
    )
    result = bind_evidence(req, ev, OBJECTS)
    assert result.state is BindingState.REJECTED
    assert result.owner_id == "OBJ-DUST"
    assert result.reason_code == "OWNER_CONFLICT"


def test_correct_structured_owner_and_parameter_bind():
    req = Requirement25(
        requirement_id="R1",
        domain=Domain.ASSIGNMENT,
        text="Площадь здания проборазделки 89,9 м2",
        scope=Scope.OBJECT_SPECIFIC,
        target_object_id="OBJ-LAB",
        verification_kind="TYPED_VALUE",
        parameter_code="AREA",
    )
    ev = Evidence25(
        evidence_id="E2",
        document="АР.pdf",
        page=12,
        row_id="4",
        fragment="Здание проборазделки. Площадь 89,9 м2",
        addressable=True,
        metadata={"owner_name": "Здание проборазделки", "parameter_code": "AREA"},
    )
    result = bind_evidence(req, ev, OBJECTS)
    assert result.state is BindingState.BOUND
    assert result.owner_id == "OBJ-LAB"
    assert result.parameter_code == "AREA"
    assert result.method == "STRUCTURED_OWNER_PARAMETER"


def test_matching_owner_with_wrong_parameter_is_rejected():
    req = Requirement25(
        requirement_id="R3",
        domain=Domain.ASSIGNMENT,
        text="Площадь здания проборазделки 89,9 м2",
        scope=Scope.OBJECT_SPECIFIC,
        target_object_id="OBJ-LAB",
        verification_kind="TYPED_VALUE",
        parameter_code="AREA",
    )
    ev = Evidence25(
        evidence_id="E3",
        document="АР.pdf",
        page=12,
        fragment="Здание проборазделки. Высота 8,5 м",
        addressable=True,
        metadata={"owner_name": "Здание проборазделки", "parameter_code": "HEIGHT"},
    )
    result = bind_evidence(req, ev, OBJECTS)
    assert result.state is BindingState.REJECTED
    assert result.owner_id == "OBJ-LAB"
    assert result.reason_code == "PARAMETER_CONFLICT"


def test_project_global_value_can_bind_without_owner():
    req = Requirement25(
        requirement_id="R2",
        domain=Domain.ASSIGNMENT,
        text="Продолжительность смены 12 часов",
        scope=Scope.PROJECT_GLOBAL,
        verification_kind="TYPED_VALUE",
        parameter_code="SHIFT_DURATION",
    )
    ev = Evidence25(
        evidence_id="E4",
        document="ТХ.pdf",
        page=7,
        fragment="Продолжительность смены составляет 12 часов",
        addressable=True,
        metadata={"parameter_code": "SHIFT_DURATION"},
    )
    result = bind_evidence(req, ev, {})
    assert result.state is BindingState.BOUND
    assert result.owner_id == "PROJECT"


def test_object_specific_semantic_alias_without_structured_owner_is_ambiguous():
    req = Requirement25(
        requirement_id="R5",
        domain=Domain.ASSIGNMENT,
        text="Площадь здания проборазделки 89,9 м2",
        scope=Scope.OBJECT_SPECIFIC,
        target_object_id="OBJ-LAB",
        verification_kind="TYPED_VALUE",
        parameter_code="AREA",
    )
    ev = Evidence25(
        evidence_id="E5",
        document="АР.pdf",
        page=14,
        fragment="Для проборазделки принята площадь 89,9 м2",
        addressable=True,
        metadata={"parameter_code": "AREA"},
    )
    result = bind_evidence(req, ev, OBJECTS)
    assert result.state is BindingState.AMBIGUOUS
    assert result.owner_id == "OBJ-LAB"
