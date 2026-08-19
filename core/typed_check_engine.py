from __future__ import annotations

from typing import Any

from .normalization import normalize_text


def _blob(findings: list[dict[str, Any]]) -> str:
    keys = ("context", "section_title", "table_title", "table_evidence", "structural_zone", "match_method", "value_text", "parameter_name")
    return normalize_text(" ".join(" ".join(str(f.get(k) or "") for k in keys) for f in findings))


def execute_typed_check(compiled: dict[str, Any], findings: list[dict[str, Any]], documents: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Execute only check types with defensible deterministic evidence.

    A failed text search is never converted into a negative engineering finding.
    """
    check_type = str(compiled.get("typed_check") or compiled.get("rule_type") or "")
    terms = [normalize_text(x) for x in compiled.get("evidence_terms") or [] if x]
    text = _blob(findings)

    if check_type == "DRAWING_TITLE_BLOCK_CHECK":
        markers = ("основная надпись", "штамп", "обозначение", "лист", "стадия")
        hits = [m for m in markers if m in text]
        if len(hits) >= 3:
            return {"status": "Да", "evidence": "Обнаружены структурные признаки основной надписи: " + ", ".join(hits) + ".", "proof_kind": "STRUCTURED_PRESENCE"}
        return {"status": "Не проверено системой", "evidence": "Для проверки основной надписи недостаточно структурных данных листа; отсутствие текстовых признаков не считается нарушением.", "proof_kind": "UNSUPPORTED"}

    if check_type in {"DRAWING_PRESENCE_CHECK", "DOCUMENT_CONTENT_PRESENCE"}:
        hits = [t for t in terms if t and t in text]
        if hits:
            return {"status": "Да", "evidence": "Найдены прямые признаки требуемого содержания: " + ", ".join(hits[:6]) + ".", "proof_kind": "PRESENCE"}
        return {"status": "Не проверено системой", "evidence": "Автоматический поиск не нашёл прямого доказательства; отсутствие не доказано.", "proof_kind": "UNSUPPORTED"}

    if check_type in {"ENGINEERING_SEMANTIC_REVIEW", "NORMATIVE_CONTENT_REVIEW", "SPECIALIST_REVIEW"}:
        hits = [t for t in terms if t and t in text]
        if hits:
            return {"status": "Требует проверки", "evidence": "Найдены связанные проектные фрагменты: " + ", ".join(hits[:6]) + ". Нужна смысловая инженерная оценка.", "proof_kind": "CANDIDATE_EVIDENCE"}
        return {"status": "Не проверено системой", "evidence": "Для данного типа проверки требуется более сильный алгоритм или специалист; отрицательный вывод не формируется.", "proof_kind": "UNSUPPORTED"}

    return None
