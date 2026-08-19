from __future__ import annotations

import re
from typing import Any

from .normalization import normalize_text
from .object_identity import ObjectIdentityEngine


def normalize_position(value: Any) -> str:
    raw = re.sub(r"\s+", "", str(value or "").strip())
    raw = raw.replace(",", ".")
    return raw


def position_parent(value: Any) -> str:
    pos = normalize_position(value)
    if "." not in pos:
        return ""
    return pos.rsplit(".", 1)[0]


def position_relation(a: Any, b: Any) -> str:
    pa, pb = normalize_position(a), normalize_position(b)
    if not pa or not pb:
        return "unknown"
    if pa == pb:
        return "same"
    if position_parent(pa) == pb:
        return "child"
    if position_parent(pb) == pa:
        return "parent"
    if position_parent(pa) and position_parent(pa) == position_parent(pb):
        return "siblings"
    return "different"


def assess_scope_binding(finding: dict[str, Any], registry_name: str, registry_position: str) -> dict[str, Any]:
    """Protect parent/child/sibling objects from property leakage.

    Position is strong evidence, but it is not allowed to override a clearly
    contradictory object label. This catches cases such as 4.16 Электрощитовая
    leaking into 4.16.1 Эстакада кабельная merely because a nearby position was
    inherited by a generic extractor.
    """
    raw_name = str(finding.get("object_hint") or finding.get("semantic_anchor_name") or "").strip()
    raw_pos = normalize_position(finding.get("genplan_position") or finding.get("semantic_anchor_position"))
    reg_pos = normalize_position(registry_position)
    identity = ObjectIdentityEngine()
    name_score = identity.compare(raw_name, registry_name).score if raw_name and registry_name else 0.0
    relation = position_relation(raw_pos, reg_pos) if raw_pos and reg_pos else "unknown"

    context = normalize_text(" ".join(str(finding.get(k) or "") for k in (
        "context", "table_evidence", "row_text", "parameter_name", "value_text"
    )))
    reg_name_norm = normalize_text(registry_name)
    raw_name_norm = normalize_text(raw_name)

    reasons: list[str] = []
    decision = "ALLOW"
    score = 100

    if raw_pos and reg_pos and raw_pos != reg_pos:
        decision = "REJECT"
        score = 0
        reasons.append(f"позиция источника {raw_pos} не совпадает с позицией объекта {reg_pos}")
    elif raw_pos and reg_pos and raw_pos == reg_pos and raw_name and name_score < 0.42:
        # Exact position cannot silently trump a contradictory label.
        decision = "HOLD"
        score = 35
        reasons.append("позиция совпала, но наименование источника противоречит объекту")
    elif raw_name and registry_name and name_score < 0.50:
        decision = "HOLD"
        score = 45
        reasons.append("слабое совпадение наименования объекта")

    # Detect explicit neighbour/parent evidence in the same row/context.
    if reg_name_norm and reg_name_norm not in context and raw_name_norm and raw_name_norm in context and normalize_text(raw_name) != reg_name_norm:
        if decision == "ALLOW":
            decision = "HOLD"
            score = min(score, 55)
            reasons.append("контекст сильнее подтверждает другое наименование")

    # Parent-child positions deserve additional caution even if an upstream
    # semantic anchor rewrote the position.
    anchor_pos = normalize_position(finding.get("semantic_anchor_position"))
    original_pos = normalize_position(finding.get("original_genplan_position") or finding.get("source_position"))
    if anchor_pos and original_pos and anchor_pos != original_pos and position_relation(anchor_pos, original_pos) in {"parent", "child", "siblings"}:
        decision = "REJECT"
        score = 0
        reasons.append("обнаружено переназначение свойства между связанными позициями")

    return {
        "scope_binding_decision": decision,
        "scope_binding_score": score,
        "scope_binding_reasons": reasons or ["границы объекта не нарушены"],
        "scope_name_similarity": round(float(name_score), 3),
        "source_position": raw_pos,
        "registry_position": reg_pos,
        "position_relation": relation,
    }
