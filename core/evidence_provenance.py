from __future__ import annotations

import hashlib
import re
from typing import Any

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code, is_parameter_entity_name
from .table_row_integrity import is_integrity_blocked

STRONG_BINDINGS = {"ROW_LOCKED", "POSITION_LOCKED", "EXACT_OBJECT"}
STRUCTURED_METHOD_TOKENS = (
    "строка таблицы",
    "экспликац",
    "состав сложного объекта",
    "таблицы тэп",
    "та же строка таблицы",
    "pz complex object register",
    "general plan",
)


def _confidence(item: dict[str, Any]) -> float:
    try:
        return max(0.0, min(1.0, float(item.get("core2_confidence") or item.get("confidence") or 0.0)))
    except Exception:
        return 0.0


def _binding(item: dict[str, Any]) -> str:
    return str(item.get("binding_status") or item.get("property_binding_status") or "").upper().strip()


def _original_object(item: dict[str, Any]) -> str:
    return str(item.get("object_hint") or "").strip()


def evidence_id(item: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(item.get("document") or ""),
            str(item.get("page") or ""),
            str(item.get("table_index") or item.get("table_no") or ""),
            str(item.get("row_index") or item.get("table_row") or ""),
            _original_object(item),
            canonical_parameter_code(item.get("parameter_code")),
            str(item.get("value") if item.get("value") is not None else item.get("value_text") or ""),
            str(item.get("unit") or ""),
        ]
    )
    return "EV-" + hashlib.blake2b(raw.encode("utf-8"), digest_size=8).hexdigest().upper()


def assess_evidence(item: dict[str, Any]) -> dict[str, Any]:
    """Create a conservative provenance/trust passport for one engineering fact.

    The score is not a probability. It is a deterministic indicator of how well
    the value is bound to its source, object and parameter. Low-trust evidence is
    retained for diagnostics but is not allowed to create a discrepancy by itself.
    """
    code = canonical_parameter_code(item.get("parameter_code"))
    obj = _original_object(item)
    binding = _binding(item)
    method = normalize_text(item.get("match_method") or "")
    row_status = str(item.get("row_integrity_status") or "")
    confidence = _confidence(item)

    reasons: list[str] = []
    factors: dict[str, int] = {}

    if is_integrity_blocked(item):
        return {
            "evidence_id": evidence_id(item),
            "score": 0,
            "grade": "REJECTED",
            "decision": "REJECT",
            "comparison_eligible": False,
            "mismatch_eligible": False,
            "reasons": ["Запись заблокирована контролем целостности строки таблицы."],
            "factors": {"integrity_block": -100},
        }

    if not obj or is_parameter_entity_name(obj):
        return {
            "evidence_id": evidence_id(item),
            "score": 0,
            "grade": "REJECTED",
            "decision": "REJECT",
            "comparison_eligible": False,
            "mismatch_eligible": False,
            "reasons": ["Не подтверждён инженерный объект, которому принадлежит показатель."],
            "factors": {"invalid_object": -100},
        }

    # Binding to the physical row/object is intentionally weighted higher than
    # model confidence. A confident extractor with a weak binding must not win.
    if binding in STRONG_BINDINGS:
        factors["strong_binding"] = 28
        reasons.append("Есть жёсткая привязка показателя к объекту.")
    if row_status.startswith("CONFIRMED"):
        factors["row_integrity"] = 24
        reasons.append("Привязка подтверждена контролем целостности строки.")
    if item.get("genplan_position"):
        factors["genplan_position"] = 18
        reasons.append("Есть позиция объекта по генплану.")
    if any(token in method for token in STRUCTURED_METHOD_TOKENS):
        factors["structured_source"] = 16
        reasons.append("Значение извлечено из структурированного источника.")
    if item.get("table_evidence") or item.get("table_index") is not None or item.get("row_index") is not None:
        factors["table_trace"] = 8
        reasons.append("Сохранён табличный след источника.")
    if item.get("document") and item.get("page"):
        factors["source_location"] = 7
    if item.get("unit"):
        factors["unit"] = 4
    if item.get("entity_property_binding", {}).get("valid") is True:
        factors["entity_property_valid"] = 7
    if item.get("semantic_anchor_name") and normalize_text(item.get("semantic_anchor_name")) == normalize_text(obj):
        factors["semantic_anchor_agrees"] = 6

    factors["extractor_confidence"] = int(round(confidence * 18))
    score = max(0, min(100, sum(factors.values())))

    # Critical rule: high model confidence alone is never sufficient for a
    # discrepancy. At least one structural binding signal is required.
    structural = bool(
        binding in STRONG_BINDINGS
        or row_status.startswith("CONFIRMED")
        or item.get("genplan_position")
        or any(token in method for token in STRUCTURED_METHOD_TOKENS)
    )
    if score >= 78 and structural:
        grade, decision = "A", "VERIFIED"
    elif score >= 62 and structural:
        grade, decision = "B", "SUPPORTED"
    elif score >= 48:
        grade, decision = "C", "HOLD"
    else:
        grade, decision = "D", "HOLD"

    comparison_eligible = decision in {"VERIFIED", "SUPPORTED"}
    mismatch_eligible = decision == "VERIFIED" or (decision == "SUPPORTED" and score >= 70)
    if not structural:
        mismatch_eligible = False
        if decision in {"VERIFIED", "SUPPORTED"}:
            decision, grade, comparison_eligible = "HOLD", "C", False
        reasons.append("Нет структурного доказательства принадлежности значения объекту.")

    return {
        "evidence_id": evidence_id(item),
        "score": score,
        "grade": grade,
        "decision": decision,
        "comparison_eligible": comparison_eligible,
        "mismatch_eligible": mismatch_eligible,
        "reasons": reasons,
        "factors": factors,
    }


def annotate_evidence_provenance(findings: list[dict[str, Any]]) -> dict[str, int]:
    stats = {"verified": 0, "supported": 0, "held": 0, "rejected": 0, "comparison_eligible": 0}
    for item in findings or []:
        if str(item.get("parameter_code") or "") in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        passport = assess_evidence(item)
        item["evidence_provenance"] = passport
        item["evidence_id"] = passport["evidence_id"]
        item["evidence_trust_score"] = passport["score"]
        item["evidence_trust_grade"] = passport["grade"]
        item["evidence_quality_decision"] = passport["decision"]
        item["evidence_comparison_eligible"] = passport["comparison_eligible"]
        item["evidence_mismatch_eligible"] = passport["mismatch_eligible"]
        decision = passport["decision"]
        if decision == "VERIFIED":
            stats["verified"] += 1
        elif decision == "SUPPORTED":
            stats["supported"] += 1
        elif decision == "REJECT":
            stats["rejected"] += 1
        else:
            stats["held"] += 1
        if passport["comparison_eligible"]:
            stats["comparison_eligible"] += 1
    return stats
