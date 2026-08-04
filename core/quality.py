from __future__ import annotations
from collections import Counter
from typing import Any


def build_quality_summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(findings)
    linked = sum(1 for item in findings if float(item.get("semantic_match_score") or 0) >= 0.80)
    table_backed = sum(1 for item in findings if item.get("table_type"))
    high_conf = sum(1 for item in findings if float(item.get("core2_confidence") or 0) >= 0.80)
    unresolved = sum(
        1 for item in findings
        if item.get("parameter_code") not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}
        and (not item.get("object_hint") or item.get("object_hint") == "Не определён")
    )
    methods = Counter(str(item.get("match_method") or "Не указан") for item in findings)
    return {
        "Всего извлечений": total,
        "Высокая уверенность": high_conf,
        "Подтверждено таблицей": table_backed,
        "Надёжно связано с объектом": linked,
        "Без привязки к объекту": unresolved,
        "Доля высокой уверенности": round(high_conf / total, 3) if total else 0.0,
        "Основные способы извлечения": dict(methods.most_common(5)),
    }
