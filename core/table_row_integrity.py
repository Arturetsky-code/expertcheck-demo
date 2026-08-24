
from __future__ import annotations
import math,re
from collections import defaultdict
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code

AUTHORITATIVE_METHOD_TOKENS=(
    "строка таблицы состава сложного объекта",
    "строка таблицы тэп пзу",
    "та же строка таблицы",
    "pz complex object register",
)
STRONG_BINDINGS={"ROW_LOCKED","POSITION_LOCKED","EXACT_OBJECT"}

def _num(item:dict[str,Any])->float|None:
    raw=item.get("value_num",item.get("value"))
    try:return float(str(raw).replace("\u00a0","").replace(" ","").replace(",","."))
    except Exception:return None

def _name(item:dict[str,Any])->str:
    # Crucial: row integrity is evaluated against the object's original row label,
    # never against a later semantic anchor.
    return normalize_text(item.get("object_hint") or "")

def _authoritative(item:dict[str,Any])->bool:
    binding=str(item.get("binding_status") or item.get("property_binding_status") or "").upper()
    confidence=float(item.get("core2_confidence") or item.get("confidence") or 0)
    locator=item.get('source_locator') or {}
    trace=str(item.get('physical_trace_level') or locator.get('physical_trace_level') or '').upper()
    has_row_trace=bool(
        item.get('table_row') not in (None,'') or item.get('row_index') not in (None,'')
        or item.get('row_text') or trace in {'ROW_TRACE','CELL_TRACE'}
    )
    # Method labels are parser assertions, not independent evidence.  A fact is
    # authoritative only when a strong binding and a physical row/cell trace
    # are both present.  High extractor confidence cannot replace either.
    return binding in STRONG_BINDINGS and has_row_trace and confidence>=.80

def apply_table_row_integrity_guard(findings:list[dict[str,Any]])->dict[str,int]:
    """Blocks shifted values from flattened PDF tables.

    Typical failure prevented:
      row 4.12 Module A = 23.5
      row 4.13 Building B = 89.9
    A generic sliding-window extractor may incorrectly emit Building B = 23.5.
    When the same page contains a high-confidence row-specific value for Building B,
    the generic conflicting record is blocked and cannot enter Project Understanding
    or cross-section comparisons.
    """
    authoritative=defaultdict(lambda:defaultdict(list))
    for f in findings:
        code=canonical_parameter_code(f.get("parameter_code"))
        name=_name(f);value=_num(f)
        if not code or not name or value is None or not _authoritative(f):continue
        key=(str(f.get("document") or ""),int(f.get("page") or 0),code)
        authoritative[key][name].append((value,f))

    stats={"authoritative_rows":0,"confirmed_rows":0,"blocked_shifted_values":0,"checked_generic_rows":0}
    stats["authoritative_rows"]=sum(len(rows) for group in authoritative.values() for rows in group.values())

    for f in findings:
        code=canonical_parameter_code(f.get("parameter_code"))
        name=_name(f);value=_num(f)
        if not code or not name or value is None:continue
        key=(str(f.get("document") or ""),int(f.get("page") or 0),code)
        page_map=authoritative.get(key)
        if not page_map or name not in page_map:continue

        expected=[v for v,_ in page_map[name]]
        is_match=any(math.isclose(value,v,rel_tol=.0005,abs_tol=.02) for v in expected)
        if _authoritative(f):
            f["row_integrity_status"]="CONFIRMED"
            stats["confirmed_rows"]+=1
            continue

        stats["checked_generic_rows"]+=1
        if is_match:
            f["row_integrity_status"]="CONFIRMED_BY_AUTHORITATIVE_ROW"
            # Keep as supporting evidence but lower its precedence.
            f["row_integrity_reference_values"]=expected[:8]
        else:
            f["row_integrity_status"]="BLOCKED_SHIFTED_VALUE"
            f["row_integrity_reason"]=(
                f"Значение {value:g} не совпадает со значением той же строки объекта "
                f"в надёжном табличном источнике: {', '.join(f'{x:g}' for x in expected[:8])}."
            )
            f["row_integrity_reference_values"]=expected[:8]
            f["project_understanding_binding"]="Отклонено"
            f["comparison_excluded"]=True
            stats["blocked_shifted_values"]+=1
    return stats

def is_integrity_blocked(item:dict[str,Any])->bool:
    return str(item.get("row_integrity_status") or "").startswith("BLOCKED") or bool(item.get("comparison_excluded"))
