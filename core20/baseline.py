from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BaselineMetric:
    key: str
    expected: float
    policy: str = "AT_LEAST"
    description: str = ""


@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    object_name: str
    parameter_code: str
    expected_kind: str
    expected_values: tuple[float, ...] = ()
    expected_position: str = ""
    notes: str = ""


def _load_profile() -> dict[str,Any]:
    root=Path(__file__).resolve().parents[1]
    path=root/"knowledge"/"control_baseline_18_7_3.json"
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}


_PROFILE=_load_profile()
BASELINE_ID=str(_PROFILE.get("baseline_id") or "18.7.3-control")
BASELINE_MIN_GOLDEN_MATCHES=int(
    ((_PROFILE.get("applicability") or {}).get("minimum_golden_object_matches") or 1)
)

BASELINE_18_7_3: dict[str,BaselineMetric] = {}
for key,row in (_PROFILE.get("metrics") or {}).items():
    if not isinstance(row,dict):
        continue
    try:
        expected=float(row.get("expected"))
    except (TypeError,ValueError):
        continue
    BASELINE_18_7_3[str(key)]=BaselineMetric(
        str(key),
        expected,
        str(row.get("policy") or "AT_LEAST"),
        str(row.get("description") or ""),
    )

_cases=[]
for row in _PROFILE.get("golden_cases") or []:
    if not isinstance(row,dict):
        continue
    values=[]
    for value in row.get("expected_values") or []:
        try:
            values.append(float(value))
        except (TypeError,ValueError):
            pass
    _cases.append(GoldenCase(
        case_id=str(row.get("case_id") or ""),
        object_name=str(row.get("object_name") or ""),
        parameter_code=str(row.get("parameter_code") or ""),
        expected_kind=str(row.get("expected_kind") or ""),
        expected_values=tuple(values),
        expected_position=str(row.get("expected_position") or ""),
        notes=str(row.get("notes") or ""),
    ))
GOLDEN_CASES_18_7_3: tuple[GoldenCase,...]=tuple(_cases)


def evaluate_baseline(observed: dict[str,Any]) -> dict[str,Any]:
    checks=[]
    for key,metric in BASELINE_18_7_3.items():
        raw=observed.get(key)
        try:
            value=float(raw)
        except (TypeError,ValueError):
            checks.append({
                "key":key,"passed":False,"expected":metric.expected,"observed":raw,
                "policy":metric.policy,"description":metric.description,"reason":"MISSING_OR_NON_NUMERIC",
            })
            continue
        if metric.policy=="EXACT":
            passed=value==metric.expected
        elif metric.policy=="AT_MOST":
            passed=value<=metric.expected
        else:
            passed=value>=metric.expected
        checks.append({
            "key":key,"passed":passed,"expected":metric.expected,"observed":value,
            "policy":metric.policy,"description":metric.description,
        })
    return {
        "baseline":BASELINE_ID,
        "passed":all(item["passed"] for item in checks),
        "failed":[item["key"] for item in checks if not item["passed"]],
        "checks":checks,
    }
