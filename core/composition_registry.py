from __future__ import annotations

from typing import Any, Iterable

from .normalization import normalize_text
from .position_rules import normalize_genplan_position


def _pos(item: dict[str, Any]) -> str:
    return normalize_genplan_position(
        item.get('genplan_position') or item.get('Позиция по ГП') or item.get('position') or '',
        allow_integer=True,
    )


def _name(item: dict[str, Any]) -> str:
    return str(item.get('value_text') or item.get('object_hint') or item.get('Наименование объекта') or item.get('name') or '').strip()


def build_composition_baseline(
    pz_findings: Iterable[dict[str, Any]],
    gp_findings: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Build the project composition from explicit structured registers only.

    This baseline is deliberately independent from generic narrative discovery,
    Object Gate and AI classification.  It prevents the UI from ending up with
    zero real project objects when the upstream registry heuristics disagree.

    Priority of names: explicit PZ complex-object table > GP explication.
    Presence in either source is sufficient for visibility.  Explicit existing
    or perspective GP rows are visible but not auto-included.
    """
    rows: dict[str, dict[str, Any]] = {}
    pz_count = 0
    gp_count = 0

    for item in pz_findings:
        if item.get('parameter_code') != 'OBJECT_ENTRY' or not item.get('pz_complex_object_register'):
            continue
        pos = _pos(item)
        name = _name(item)
        if not pos or not name:
            continue
        pz_count += 1
        rows[pos] = {
            'Позиция по ГП': pos,
            'Наименование объекта': name,
            'Статус проектирования': 'Проектируемый',
            'Источник состава': 'ПЗ / Сведения о сложном объекте',
            'В ПЗ': True,
            'В генплане': False,
            'Включить': True,
            'Подтвержденный реестр': True,
            'Количество источников': 1,
            'Количество': 1,
            'Доверие к объекту': 140,
            'composition_baseline': True,
            'composition_source_strength': 'authoritative_pz',
            'pz_document': item.get('document'),
            'pz_page': item.get('page'),
            'source_records': [{
                'kind':'PZ_COMPLEX_OBJECT_REGISTER',
                'document':item.get('document'),
                'page':item.get('page'),
                'position':pos,
            }],
        }

    for item in gp_findings:
        if not item.get('general_plan_explication'):
            continue
        pos = _pos(item)
        name = _name(item)
        if not pos or not name:
            continue
        gp_count += 1
        status = str(item.get('general_plan_design_status') or item.get('object_lifecycle_status') or 'Проектируемый')
        if status == 'Не определён':
            status = 'Проектируемый'
        existing = status in {'Существующий', 'Перспективный'}
        if pos in rows:
            row = rows[pos]
            row['В генплане'] = True
            row['Количество источников'] = 2
            row['Источник состава'] = 'ПЗ + экспликация генерального плана'
            # PZ remains the naming authority when both sources share a position.
            row['gp_name'] = name
            row['general_plan_document'] = item.get('document')
            row['general_plan_page'] = item.get('page')
            row.setdefault('source_records',[]).append({
                'kind':'GENERAL_PLAN_EXPLICATION','document':item.get('document'),
                'page':item.get('page'),'position':pos,
            })
            continue
        rows[pos] = {
            'Позиция по ГП': pos,
            'Наименование объекта': name,
            'Статус проектирования': status,
            'Источник состава': 'Экспликация генерального плана',
            'В ПЗ': False,
            'В генплане': True,
            'Включить': not existing,
            'Подтвержденный реестр': not existing,
            'Количество источников': 1,
            'Количество': 1,
            'Доверие к объекту': 125 if not existing else 85,
            'composition_baseline': True,
            'composition_source_strength': 'general_plan_explication',
            'general_plan_document': item.get('document'),
            'general_plan_page': item.get('page'),
            'source_records': [{
                'kind':'GENERAL_PLAN_EXPLICATION','document':item.get('document'),
                'page':item.get('page'),'position':pos,
            }],
        }

    result = sorted(rows.values(), key=lambda r: tuple(int(x) for x in str(r['Позиция по ГП']).split('.')))
    return result, {
        'pz_positions': pz_count,
        'general_plan_positions': gp_count,
        'baseline_positions': len(result),
        'auto_included': sum(1 for r in result if r.get('Включить')),
        'review_only': sum(1 for r in result if not r.get('Включить')),
    }


def merge_baseline_with_registry(
    baseline: Iterable[dict[str, Any]],
    registry: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Enrich baseline rows with registry metadata without allowing registry filters to erase them."""
    by_pos = {_pos(r): dict(r) for r in registry if _pos(r)}
    out: list[dict[str, Any]] = []
    for base in baseline:
        pos = _pos(base)
        merged = dict(by_pos.get(pos) or {})
        # Baseline composition fields always win over downstream heuristics.
        merged.update(base)
        out.append(merged)
    return out
