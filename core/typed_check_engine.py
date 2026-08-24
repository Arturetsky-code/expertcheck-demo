from __future__ import annotations

from typing import Any

from .normalization import normalize_text


def _blob(findings: list[dict[str, Any]]) -> str:
    keys = ("context", "section_title", "table_title", "table_evidence", "structural_zone", "match_method", "value_text", "parameter_name")
    return normalize_text(" ".join(" ".join(str(f.get(k) or "") for k in keys) for f in findings))


def _finding_text(finding: dict[str, Any]) -> str:
    keys=("context","section_title","table_title","table_evidence","row_text","value_text","parameter_name")
    return normalize_text(" ".join(str(finding.get(k) or "") for k in keys))


def _source(finding: dict[str, Any]) -> str:
    document=str(finding.get('document') or finding.get('Файл') or '').strip()
    page=finding.get('page') or finding.get('Страница')
    return f"{document}, стр. {page}" if document and page not in (None,'') else document


def _direct_presence(finding: dict[str, Any]) -> bool:
    proof=str(finding.get('proof_kind') or finding.get('evidence_quality_decision') or '').upper()
    return bool(
        finding.get('direct_artifact_evidence')
        or finding.get('document_identity_verified')
        or proof in {'STRUCTURED_PRESENCE','DOCUMENT_IDENTITY'}
    )


def execute_typed_check(compiled: dict[str, Any], findings: list[dict[str, Any]], documents: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Execute only check types with defensible deterministic evidence.

    A failed text search is never converted into a negative engineering finding.
    """
    check_type = str(compiled.get("typed_check") or compiled.get("rule_type") or "")
    terms = [normalize_text(x) for x in compiled.get("evidence_terms") or [] if x]
    text = _blob(findings)
    level=str(compiled.get('verification_level') or '').upper()
    rule_type=str(compiled.get('rule_type') or '').lower()

    if rule_type=='mandatory_document':
        matches=[]
        for document in documents or []:
            name=normalize_text(' '.join(str(document.get(k) or '') for k in ('Файл','Имя файла','name','filename','Тип документа','document_type')))
            hits=[t for t in terms if len(t)>=4 and t in name]
            if hits:
                matches.append(str(document.get('Файл') or document.get('name') or document.get('filename') or 'документ'))
        if matches:
            return {"status":"Да","evidence":"Обязательный документ идентифицирован по реестру файлов: "+", ".join(matches[:4])+".","proof_kind":"DOCUMENT_IDENTITY"}
        return {"status":"Не проверено системой","evidence":"Обязательный документ не идентифицирован однозначно; отсутствие совпадения не считается отсутствием документа.","proof_kind":"UNSUPPORTED"}

    if check_type == "DRAWING_TITLE_BLOCK_CHECK":
        markers = ("основная надпись", "штамп", "обозначение", "лист", "стадия")
        for finding in findings:
            ftext=_finding_text(finding)
            hits=[m for m in markers if m in ftext]
            if len(hits)>=3 and _direct_presence(finding) and _source(finding):
                return {"status":"Да","evidence":f"В одном листе обнаружены структурные признаки основной надписи ({', '.join(hits)}). Источник: {_source(finding)}.","proof_kind":"STRUCTURED_PRESENCE"}
        return {"status": "Не проверено системой", "evidence": "Для проверки основной надписи недостаточно структурных данных листа; отсутствие текстовых признаков не считается нарушением.", "proof_kind": "UNSUPPORTED"}

    if check_type in {"DRAWING_PRESENCE_CHECK", "DOCUMENT_CONTENT_PRESENCE"}:
        # Presence evidence can close only an L1 check.  Correctness,
        # completeness and engineering compliance remain specialist/semantic
        # checks even when the same words occur in the document.
        if level!='L1_PRESENCE':
            return {"status":"Не проверено системой","evidence":"Найденный текст не доказывает правильность, полноту или соответствие инженерного решения.","proof_kind":"UNSUPPORTED"}
        candidates=[]
        for finding in findings:
            ftext=_finding_text(finding)
            hits=list(dict.fromkeys(t for t in terms if len(t)>=4 and t in ftext))
            if len(hits)<2 or not _source(finding):
                continue
            if _direct_presence(finding):
                return {"status":"Да","evidence":f"Требуемый артефакт подтверждён структурированным источником: {', '.join(hits[:6])}. Источник: {_source(finding)}.","proof_kind":"STRUCTURED_PRESENCE"}
            candidates.append((hits,finding))
        if candidates:
            hits,finding=candidates[0]
            return {"status":"Требует проверки","evidence":f"Найден текстовый кандидат: {', '.join(hits[:6])}. Источник: {_source(finding)}. Наличие требуемого артефакта автоматически не подтверждено.","proof_kind":"CANDIDATE_EVIDENCE"}
        return {"status": "Не проверено системой", "evidence": "Автоматический поиск не нашёл прямого доказательства; отсутствие не доказано.", "proof_kind": "UNSUPPORTED"}

    if check_type in {"ENGINEERING_SEMANTIC_REVIEW", "NORMATIVE_CONTENT_REVIEW", "SPECIALIST_REVIEW"}:
        hits = [t for t in terms if t and t in text]
        if hits:
            return {"status": "Требует проверки", "evidence": "Найдены связанные проектные фрагменты: " + ", ".join(hits[:6]) + ". Нужна смысловая инженерная оценка.", "proof_kind": "CANDIDATE_EVIDENCE"}
        return {"status": "Не проверено системой", "evidence": "Для данного типа проверки требуется более сильный алгоритм или специалист; отрицательный вывод не формируется.", "proof_kind": "UNSUPPORTED"}

    return None
