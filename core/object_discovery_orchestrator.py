from __future__ import annotations

from typing import Any, Iterable

from .normalization import normalize_text
from .position_rules import normalize_genplan_position


def _row_key(row: dict[str, Any]) -> str:
    pos = normalize_genplan_position(row.get('Позиция по ГП') or row.get('position') or '', allow_integer=True)
    name = normalize_text(row.get('Наименование объекта') or row.get('name') or '')
    return f'{pos}|{name}'


def _gp_record_from_finding(item: dict[str, Any]) -> dict[str, Any]:
    pos = normalize_genplan_position(item.get('genplan_position') or '', allow_integer=True)
    name = str(item.get('value_text') or item.get('object_hint') or '').strip()
    life = str(item.get('object_lifecycle_status') or item.get('general_plan_design_status') or 'Не определён')
    projected = life in {'Проектируемый', 'Реконструируемый'}
    source_count = 1
    return {
        'Позиция по ГП': pos,
        'Родительская позиция': '.'.join(pos.split('.')[:-1]) if pos and '.' in pos else '',
        'Наименование объекта': name,
        'Количество': 1,
        'В ПЗ': False,
        'В генплане': True,
        'В разделах ПД': False,
        'В XML': False,
        'Количество источников': source_count,
        'Статус консолидации': 'Есть на генплане — требуется подтверждение в ПЗ',
        'Конфликты': '',
        'Уверенность консолидации': float(item.get('confidence') or 0.94),
        'Способ идентификации': 'general_plan_seed',
        'Источник принятого наименования': 'Генплан',
        'Уверенность наименования': float(item.get('confidence') or 0.94),
        'Статус количества': 'Не указано — принято 1',
        'Источник количества': 'Генплан',
        'Уверенность количества': 0.45,
        'Статус проектирования': life,
        'Доверие к объекту': 100 if projected else 85,
        'Подтвержденный реестр': projected,
        'general_plan_seed': True,
        'general_plan_page': item.get('page'),
        'general_plan_document': item.get('document'),
    }


def ensure_general_plan_registry_visibility(
    trusted: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    gp_findings: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Guarantee that high-quality explication rows survive later filters.

    The general plan is an independent evidence channel. A row from an explication
    must never disappear merely because PZ/XML confirmation has not yet been found.
    Explicit projected/reconstructed rows are placed in the trusted set; rows with
    unknown lifecycle remain visible as candidates for user confirmation.
    """
    trusted_out = [dict(x) for x in trusted]
    candidate_out = [dict(x) for x in candidates]
    keys = {_row_key(x) for x in trusted_out + candidate_out}
    positioned_names = {normalize_text(x.get('Наименование объекта') or '') for x in trusted_out + candidate_out if normalize_genplan_position(x.get('Позиция по ГП') or '', allow_integer=True)}
    added_trusted = 0
    added_candidates = 0
    for item in gp_findings:
        if not item.get('general_plan_explication'):
            continue
        pos = normalize_genplan_position(item.get('genplan_position') or '', allow_integer=True)
        name = str(item.get('value_text') or item.get('object_hint') or '').strip()
        if not pos or not name:
            continue
        row = _gp_record_from_finding(item)
        key = _row_key(row)
        norm_name = normalize_text(row.get('Наименование объекта') or '')
        # If the same name already exists without a position, prefer the precise
        # general-plan position and remove the weaker duplicate.
        trusted_out = [x for x in trusted_out if not (not normalize_genplan_position(x.get('Позиция по ГП') or '', allow_integer=True) and normalize_text(x.get('Наименование объекта') or '') == norm_name)]
        candidate_out = [x for x in candidate_out if not (not normalize_genplan_position(x.get('Позиция по ГП') or '', allow_integer=True) and normalize_text(x.get('Наименование объекта') or '') == norm_name)]
        keys = {_row_key(x) for x in trusted_out + candidate_out}
        if key in keys:
            continue
        life = str(row.get('Статус проектирования') or '')
        if life in {'Проектируемый', 'Реконструируемый'}:
            trusted_out.append(row)
            added_trusted += 1
        else:
            candidate_out.append(row)
            added_candidates += 1
        keys.add(key)
    return trusted_out, candidate_out, {
        'general_plan_seed_trusted': added_trusted,
        'general_plan_seed_candidates': added_candidates,
    }


def needs_object_recovery(
    trusted: Iterable[dict[str, Any]],
    candidates: Iterable[dict[str, Any]],
    gp_findings: Iterable[dict[str, Any]],
) -> bool:
    trusted_count = len(list(trusted))
    candidate_count = len(list(candidates))
    gp_count = sum(1 for x in gp_findings if x.get('general_plan_explication'))
    if trusted_count == 0:
        return True
    if gp_count >= 4 and trusted_count < max(2, int(gp_count * 0.25)):
        return True
    return trusted_count + candidate_count == 0
