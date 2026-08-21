from __future__ import annotations

from typing import Any

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code, is_parameter_entity_name
from .table_row_integrity import is_integrity_blocked
from .entity_scope_graph import infer_entity_level, metric_scope_compatible


ADMIT = "ADMIT"
HOLD = "HOLD"
REJECT = "REJECT"


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace("\u00a0", "").replace(" ", "").replace(",", "."))
    except (TypeError, ValueError, OverflowError):
        return None


def assess_fact_admission(finding: dict[str, Any]) -> dict[str, Any]:
    """Decide whether an extracted value is allowed into the engineering model.

    The gate answers four independent questions: WHO owns the value, WHAT the
    metric is, VALUE is valid, and WHERE it came from. A weak answer to WHO is
    deliberately treated more strictly than a high model confidence.
    """
    code = canonical_parameter_code(finding.get("parameter_code"))
    binding = str(finding.get("binding_status") or finding.get("property_binding_status") or "").upper()
    row_status = str(finding.get("row_integrity_status") or "").upper()
    quality = str(finding.get("evidence_quality_decision") or "").upper()
    scope_decision = str(finding.get("scope_binding_decision") or "ALLOW").upper()
    table_scope_decision = str(finding.get("table_semantic_scope_decision") or "ALLOW").upper()
    obj = str(finding.get("object_hint") or finding.get("semantic_anchor_name") or "").strip()
    entity_level=infer_entity_level(obj, finding.get("genplan_position") or finding.get("semantic_anchor_position"), finding.get("context") or finding.get("table_title"))
    page = finding.get("page")
    document = str(finding.get("document") or "").strip()
    position = str(finding.get("genplan_position") or finding.get("semantic_anchor_position") or "").strip()
    confidence = _num(finding.get("core2_confidence") or finding.get("confidence")) or 0.0
    value = _num(finding.get("value"))

    reasons: list[str] = []
    scope_entity_type = str(finding.get("scope_entity_type") or "").upper().strip()
    metric_scope = str(finding.get("metric_semantic_scope") or "").lower().strip()
    if not metric_scope and code == 'AREA_BUILD':
        metric_scope='building_footprint'
    if metric_scope and not metric_scope_compatible(metric_scope, entity_level):
        return {
            "fact_admission_decision": HOLD,
            "fact_admission_score": 40,
            "fact_admission_reasons": [f"смысловой уровень показателя «{metric_scope}» несовместим с уровнем сущности «{entity_level}»"],
            "fact_who_score": 20, "fact_what_score": 50, "fact_value_score": 50, "fact_where_score": 50,
            "fact_scope_score": 0, "entity_scope_level": entity_level,
        }
    # Drawing semantic boundary: room/schedule areas are valid evidence but are
    # not building TEPs. They stay in the Drawing Graph and must not be promoted
    # to the project object model as AREA_TOTAL/AREA_BUILD.
    if finding.get("comparison_excluded") or scope_entity_type in {"ROOM", "ROOM_SCHEDULE"} or metric_scope in {"room_area", "room_area_sum", "room_schedule_sum"}:
        return {
            "fact_admission_decision": HOLD,
            "fact_admission_score": 70 if finding.get("drawing_evidence") else 50,
            "fact_admission_reasons": [str(finding.get("comparison_exclusion_reason") or "показатель относится к локальной сущности чертежа и не является ТЭП объекта")],
            "fact_who_score": 50, "fact_what_score": 50, "fact_value_score": 50, "fact_where_score": 50,
            "fact_scope_score": 100,
        }
    who = 0
    what = 0
    value_score = 0
    where = 0

    if is_integrity_blocked(finding):
        return {
            "fact_admission_decision": REJECT,
            "fact_admission_score": 0,
            "fact_admission_reasons": ["источник заблокирован контролем целостности строки таблицы"],
            "fact_who_score": 0, "fact_what_score": 0, "fact_value_score": 0, "fact_where_score": 0,
        }
    if table_scope_decision == "HOLD":
        return {
            "fact_admission_decision": HOLD,
            "fact_admission_score": 45,
            "fact_admission_reasons": list(finding.get("table_semantic_scope_reasons") or ["смысловой уровень таблицы не подтверждает владельца показателя"]),
            "fact_who_score": 20, "fact_what_score": 50, "fact_value_score": 50, "fact_where_score": 50,
            "fact_scope_score": 20,
        }
    if scope_decision == "REJECT":
        return {
            "fact_admission_decision": REJECT,
            "fact_admission_score": 0,
            "fact_admission_reasons": ["нарушены границы объекта"],
            "fact_who_score": 0, "fact_what_score": 0, "fact_value_score": 0, "fact_where_score": 0,
        }

    if obj and not is_parameter_entity_name(obj):
        who += 25
    else:
        reasons.append("не доказан владелец инженерного показателя")
    if binding in {"ROW_LOCKED", "POSITION_LOCKED", "EXACT_OBJECT"}:
        who += 35
    elif position:
        who += 25
    elif confidence >= 0.90:
        who += 10
        reasons.append("объект определён только вероятностно")
    if scope_decision == "HOLD":
        who = min(who, 25)
        reasons.append("границы объекта требуют проверки")

    if code and code not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
        what += 35
    else:
        reasons.append("не определён инженерный показатель")
    if finding.get("parameter_name"):
        what += 15

    if value is not None:
        value_score += 35
    else:
        reasons.append("значение не является валидным числом")
    if finding.get("unit") or code in {"FLOORS", "QUANTITY", "PERSONNEL", "LINE_COUNT"}:
        value_score += 15

    if document:
        where += 20
    else:
        reasons.append("не определён исходный документ")
    if page not in (None, ""):
        where += 15
    if finding.get("source_fingerprint") or finding.get("evidence_id"):
        where += 15
    if row_status.startswith("CONFIRMED") or finding.get("table_evidence") or finding.get("row_text"):
        where += 10

    total = min(100, who + what + value_score + where)

    # Hard requirements for admission. High confidence cannot compensate for
    # missing ownership or provenance.
    if who < 40 or what < 35 or value_score < 35 or where < 35:
        decision = HOLD
    elif quality in {"REJECT", "BLOCKED"}:
        decision = REJECT
        reasons.append("источник отклонён Evidence Trust Gate")
    elif quality == "HOLD":
        decision = HOLD
        reasons.append("Evidence Trust Gate требует дополнительного подтверждения")
    else:
        decision = ADMIT

    if decision == ADMIT and not reasons:
        reasons = ["владелец, показатель, значение и источник подтверждены"]

    return {
        "fact_admission_decision": decision,
        "fact_admission_score": total,
        "fact_admission_reasons": reasons,
        "fact_who_score": min(100, who),
        "fact_what_score": min(100, what),
        "fact_value_score": min(100, value_score),
        "fact_where_score": min(100, where),
        "fact_scope_score": 100,
        "entity_scope_level": entity_level,
    }
