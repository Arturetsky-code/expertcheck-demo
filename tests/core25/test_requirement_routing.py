from core25.contracts import Domain, Requirement25, Scope
from core25.routing import route_requirement


def test_project_global_numeric_route_does_not_require_owner():
    req = Requirement25(
        requirement_id="A1",
        domain=Domain.ASSIGNMENT,
        text="Продолжительность смены 12 часов",
        scope=Scope.PROJECT_GLOBAL,
        verification_kind="TYPED_VALUE",
        parameter_code="SHIFT_DURATION",
        required_value=12.0,
        unit="час",
        expected_sections=("ТХ",),
    )
    route = route_requirement(req)
    assert route.kind == "TYPED_VALUE"
    assert route.requires_owner is False
    assert route.requires_addressable_evidence is True
    assert route.parameter_code == "SHIFT_DURATION"


def test_object_specific_numeric_route_requires_owner():
    req = Requirement25(
        requirement_id="A2",
        domain=Domain.ASSIGNMENT,
        text="Автосамосвал объем кузова 32 м3",
        scope=Scope.OBJECT_SPECIFIC,
        verification_kind="TYPED_VALUE",
        parameter_code="BODY_VOLUME",
        target_object_id="TRUCK-1",
        required_value=32.0,
        unit="м3",
        expected_sections=("ТХ",),
    )
    route = route_requirement(req)
    assert route.kind == "TYPED_VALUE"
    assert route.requires_owner is True


def test_table_cell_value_keeps_structured_source_preference():
    req = Requirement25(
        requirement_id="A22",
        domain=Domain.ASSIGNMENT,
        text="Производственная мощность 1 600 тыс. тонн в год",
        scope=Scope.PROJECT_GLOBAL,
        verification_kind="TABLE_CELL_VALUE",
        parameter_code="ANNUAL_CAPACITY",
    )
    route = route_requirement(req)
    assert route.kind == "TYPED_VALUE"
    assert route.prefer_structured_source is True


def test_unsupported_semantic_requirement_routes_to_review_kind():
    req = Requirement25(
        requirement_id="A3",
        domain=Domain.ASSIGNMENT,
        text="Обеспечить удобство эксплуатации",
        scope=Scope.UNRESOLVED,
        verification_kind="SEMANTIC_UNSUPPORTED",
    )
    route = route_requirement(req)
    assert route.kind == "REVIEW_ONLY"
    assert route.requires_addressable_evidence is False
