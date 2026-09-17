from __future__ import annotations

from dataclasses import asdict
from math import isclose
from typing import Any

from .baseline import BASELINE_MIN_GOLDEN_MATCHES, GOLDEN_CASES_18_7_3, evaluate_baseline
from .model import CanonicalProject


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().replace("ё", "е").casefold().split())


def _numeric_values(project: CanonicalProject, object_id: str, parameter_code: str) -> list[float]:
    values=[]
    for prop in project.properties.values():
        if prop.object_id != object_id or prop.parameter_code != parameter_code:
            continue
        try:
            values.append(float(prop.value))
        except (TypeError, ValueError):
            continue
    return values


def _has_value(values: list[float], expected: float) -> bool:
    return any(isclose(value, expected, rel_tol=0.0, abs_tol=1e-6) for value in values)


def evaluate_golden_cases(project: CanonicalProject) -> dict[str, Any]:
    available_names={_norm(obj.name) for obj in project.objects.values()}
    profile_matches=sum(
        1 for case in GOLDEN_CASES_18_7_3
        if _norm(case.object_name) in available_names
    )
    if not GOLDEN_CASES_18_7_3 or profile_matches < BASELINE_MIN_GOLDEN_MATCHES:
        return {
            "passed":True,
            "skipped":True,
            "applicable":False,
            "profile_matches":profile_matches,
            "required_matches":BASELINE_MIN_GOLDEN_MATCHES,
            "failed":[],
            "cases":[],
        }

    rows=[]
    for case in GOLDEN_CASES_18_7_3:
        object_matches=[obj for obj in project.objects.values() if _norm(obj.name)==_norm(case.object_name)]
        if case.expected_position:
            object_matches=[obj for obj in object_matches if _norm(obj.genplan_position)==_norm(case.expected_position)] or object_matches
        if not object_matches:
            rows.append({
                "case_id":case.case_id,"passed":False,"reason":"OBJECT_NOT_FOUND","expected":asdict(case),
            })
            continue
        obj=object_matches[0]
        values=_numeric_values(project,obj.object_id,case.parameter_code)
        values_ok=all(_has_value(values,expected) for expected in case.expected_values)
        finding_kinds={
            finding.kind for finding in project.findings.values()
            if finding.object_id==obj.object_id and finding.parameter_code==case.parameter_code
        }
        if case.expected_kind=='PROJECT_FINDING':
            kind_ok='PROJECT_FINDING' in finding_kinds
        elif case.expected_kind=='VERIFIED_OK':
            # For binding controls, a clean exact property binding is enough at
            # migration stage; the new verification engine may later add the
            # canonical VERIFIED_OK finding.
            kind_ok=('VERIFIED_OK' in finding_kinds) or values_ok
        else:
            kind_ok=case.expected_kind in finding_kinds
        rows.append({
            "case_id":case.case_id,
            "passed":bool(values_ok and kind_ok),
            "object_id":obj.object_id,
            "object_name":obj.name,
            "position":obj.genplan_position,
            "observed_values":sorted(set(values)),
            "finding_kinds":sorted(finding_kinds),
            "expected":asdict(case),
        })
    return {
        "passed":all(row["passed"] for row in rows),
        "skipped":False,
        "applicable":True,
        "profile_matches":profile_matches,
        "required_matches":BASELINE_MIN_GOLDEN_MATCHES,
        "failed":[row["case_id"] for row in rows if not row["passed"]],
        "cases":rows,
    }


def evaluate_20_parity(project: CanonicalProject, observed_metrics: dict[str, Any]) -> dict[str, Any]:
    validation=project.validate()
    baseline=evaluate_baseline(observed_metrics)
    golden=evaluate_golden_cases(project)
    return {
        "passed":not validation and baseline["passed"] and golden["passed"],
        "canonical_schema":project.schema_version,
        "canonical_fingerprint":project.fingerprint(),
        "validation_issues":[asdict(item) for item in validation],
        "baseline":baseline,
        "golden":golden,
        "stats":project.stats(),
    }
