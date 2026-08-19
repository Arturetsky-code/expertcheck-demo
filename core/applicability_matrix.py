from __future__ import annotations

from typing import Any

from .object_semantics import canonical_parameter_code, parameter_applicability

# Universal section roles. Industry profiles may extend/override this later.
_SECTION_ROLES: dict[str, tuple[str, ...]] = {
    "AREA_BUILD": ("ПЗУ", "ПЗ", "АР"),
    "AREA_TOTAL": ("АР", "ПЗ"),
    "VOLUME_BUILD": ("АР", "ПЗ"),
    "HEIGHT_BUILD": ("АР", "КР", "ПЗ"),
    "FLOORS": ("АР", "ПЗ"),
    "CAPACITY": ("ТХ", "ПЗ"),
    "POWER_INSTALLED": ("ИОС1", "ТХ", "ПЗ"),
    "POWER_CALCULATED": ("ИОС1", "ТХ"),
    "VOLTAGE": ("ИОС1", "ТХ"),
    "FLOW_RATE": ("ИОС2", "ТХ"),
    "PRESSURE": ("ИОС2", "ТХ"),
    "DIAMETER": ("ИОС2", "ТХ", "ПЗУ"),
    "LENGTH": ("ПЗУ", "ТХ", "ИОС2", "ПЗ"),
    "WIDTH": ("ПЗУ", "АР", "КР"),
    "DEPTH": ("ПЗУ", "КР", "ТХ"),
    "QUANTITY": ("ПЗ", "ПЗУ", "ТХ"),
    "VOLUME": ("ТХ", "ИОС2", "ПЗ"),
    "RES_VOLUME": ("ТХ", "ИОС2", "ПЗ"),
}


def section_expectations(object_type: str, parameter_code: Any) -> dict[str, str]:
    """Return section applicability without claiming regulatory obligation.

    required = core owner for a parameter that is required for the object type;
    expected = useful independent corroboration; allowed = may legitimately occur;
    not_applicable = do not search merely for completeness.
    """
    code = canonical_parameter_code(parameter_code)
    object_level = parameter_applicability(object_type, code)
    sections = _SECTION_ROLES.get(code, ())
    if object_level == "not_applicable":
        return {s: "not_applicable" for s in sections}
    result: dict[str, str] = {}
    for idx, section in enumerate(sections):
        if idx == 0 and object_level == "required":
            result[section] = "required"
        elif idx <= 1 and object_level in {"required", "expected"}:
            result[section] = "expected"
        else:
            result[section] = "allowed"
    return result


def expected_sections(object_type: str, parameter_code: Any, *, include_allowed: bool = False) -> list[str]:
    matrix = section_expectations(object_type, parameter_code)
    accepted = {"required", "expected", "allowed"} if include_allowed else {"required", "expected"}
    return [section for section, status in matrix.items() if status in accepted]


def should_compare_section(object_type: str, parameter_code: Any, section: str) -> bool:
    status = section_expectations(object_type, parameter_code).get(section, "not_applicable")
    return status in {"required", "expected", "allowed"}
