from __future__ import annotations

import hashlib
from typing import Any, Iterable


def stable_report_id(prefix: str, row: dict[str, Any]) -> str:
    raw_id = row.get('id') or row.get('check_id') or row.get('plan_id') or row.get('risk_id')
    candidate = str(raw_id or '').strip()
    if candidate.lower() not in {'', 'nan', 'none', '—'}:
        return candidate
    identity = '|'.join(str(row.get(key) or '').strip() for key in (
        'object','parameter','status','sources','explanation','finding_type',
        'domain','title','Контур','Проверка','Объект','Причина',
    ))
    digest = hashlib.sha1(identity.encode('utf-8')).hexdigest()[:12].upper()
    return f'{prefix}-{digest}'


def build_review_surface_rows(
    comparison_problems: Iterable[dict[str, Any]],
    review_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in comparison_problems or []:
        if str(item.get('finding_type') or '').upper() != 'REVIEW_QUESTION':
            continue
        rows.append({
            'ID': stable_report_id('CMP', dict(item)),
            'Контур': 'Межраздельная сверка',
            'Объект': item.get('object') or '—',
            'Проверка': item.get('parameter') or item.get('parameter_name') or '—',
            'Причина': item.get('explanation') or item.get('global_finding_reason') or '',
            'Код причины': item.get('coverage_reason_code') or 'CROSS_SECTION_REVIEW',
            'Семейство проверки': item.get('checker_family') or 'Детерминированная межраздельная сверка',
            'Недостающие доказательства': 'Уточнить доверенные источники и актуальность разделов',
            'Ожидаемые разделы': item.get('sources') or '—',
            'Уровень доказательства': item.get('evidence_level') or '—',
        })
    for item in (review_plan.get('items') or []):
        if str(item.get('verification_kind') or '').upper() != 'REVIEW_QUESTION':
            continue
        route = item.get('expected_evidence_route') or item.get('expected_sections') or []
        if isinstance(route, (list, tuple, set)):
            route = ', '.join(str(value) for value in route if str(value).strip())
        missing = item.get('missing_evidence_slots') or []
        if isinstance(missing, (list, tuple, set)):
            missing = ', '.join(str(value) for value in missing if str(value).strip())
        rows.append({
            'ID': stable_report_id('Q', dict(item)),
            'Контур': item.get('domain') or 'Не определён',
            'Объект': item.get('entity') or '—',
            'Проверка': item.get('title') or '—',
            'Причина': item.get('coverage_reason') or 'Требуется предметное решение специалиста.',
            'Код причины': item.get('coverage_reason_code') or 'SPECIALIST_JUDGEMENT',
            'Семейство проверки': item.get('checker_family') or '—',
            'Недостающие доказательства': missing or '—',
            'Ожидаемые разделы': route or '—',
            'Уровень доказательства': item.get('evidence_level') or 'L0',
        })
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in rows:
        key = (
            str(item.get('Контур') or ''),
            str(item.get('ID') or ''),
            str(item.get('Проверка') or ''),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _normalize_finding_parameter(object_name: Any, parameter: Any) -> str:
    obj = str(object_name or "").strip().casefold()
    text = str(parameter or "").strip().casefold()
    # Review-plan titles may prepend the object name to an already object-scoped
    # parameter, e.g. "Компрессорная: Площадь застройки". Continuity findings
    # keep only "Площадь застройки". They are the same engineering problem.
    if obj:
        for sep in (":", "—", "-", "·"):
            prefix = f"{obj}{sep}"
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        if text.startswith(obj + " "):
            text = text[len(obj):].strip()
    return " ".join(text.replace("ё", "е").split())


def build_project_surface_rows(
    report_problems: Iterable[dict[str, Any]],
    review_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in report_problems or []:
        if str(item.get('finding_type') or '').upper() != 'PROJECT_FINDING':
            continue
        rows.append({
            'ID': stable_report_id('PF', dict(item)),
            'object': item.get('object') or '—',
            'parameter_name': item.get('parameter') or '—',
            'status': item.get('status') or 'Несоответствие',
            'explanation': item.get('explanation') or '',
            'values': item.get('values') or '',
            'sources': item.get('sources') or '',
        })
    for item in (review_plan.get('items') or []):
        if str(item.get('verification_kind') or '').upper() != 'PROJECT_FINDING':
            continue
        rows.append({
            'ID': stable_report_id('PF', dict(item)),
            'object': item.get('entity') or item.get('domain') or '—',
            'parameter_name': item.get('title') or '—',
            'status': item.get('verification_state') or 'Несоответствие',
            'explanation': item.get('coverage_reason') or item.get('recommendation') or '',
            'values': '',
            'sources': item.get('expected_evidence_route') or '',
        })
    deduped: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for item in rows:
        object_key = " ".join(str(item.get('object') or '').casefold().replace("ё", "е").split())
        parameter_key = _normalize_finding_parameter(item.get('object'), item.get('parameter_name'))
        key = (object_key, parameter_key)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = item
            deduped.append(item)
            continue
        # Prefer/merge the richer continuity payload rather than counting the
        # same project defect twice.
        for field in ("values", "sources", "explanation"):
            current = str(existing.get(field) or "").strip()
            candidate = str(item.get(field) or "").strip()
            if len(candidate) > len(current):
                existing[field] = item.get(field)
        if str(existing.get("status") or "").strip() in {"", "Несоответствие"}:
            existing["status"] = item.get("status") or existing.get("status")
    return deduped
