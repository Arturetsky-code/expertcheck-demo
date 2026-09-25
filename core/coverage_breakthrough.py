from __future__ import annotations

from collections import Counter
import re
from typing import Any

from .assignment_verification_kernel import verify_assignment_requirement
from .normalization import normalize_text
from .requirement_contracts import SCOPE_EQUIPMENT, SCOPE_OBJECT


def _text(value: Any) -> str:
    return str(value or "").strip()


def _owner_tokens(value: Any) -> set[str]:
    stop = {"здание", "сооружение", "площадка", "комплекс", "оборудование", "система", "установка"}
    return {
        word for word in re.findall(r"[a-zа-яё0-9-]{3,}", normalize_text(value).lower())
        if word not in stop
    }


def _object_owner_match(object_name: str, fragment: str) -> bool:
    object_norm = normalize_text(object_name).lower()
    fragment_norm = normalize_text(fragment).lower()
    if not object_norm:
        return False
    if object_norm in fragment_norm:
        return True
    tokens = _owner_tokens(object_norm)
    if not tokens:
        return False
    present = sum(token in fragment_norm for token in tokens)
    return present / max(1, len(tokens)) >= 0.75


def _normalized_candidate(requirement: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any] | None:
    document = _text(candidate.get("document"))
    page = candidate.get("page")
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = None
    fragment = _text(
        candidate.get("context")
        or candidate.get("exact_clause")
        or candidate.get("source_trace")
    )
    if not document or not page or not fragment:
        return None

    contract = dict(requirement.get("evidence_contract_v2") or {})
    scope = _text(contract.get("scope") or requirement.get("requirement_scope")).upper()
    object_name = _text(requirement.get("object_name"))
    candidate_object = _text(candidate.get("object"))
    owner_match = True
    if candidate.get("owner_match") is not None:
        owner_match = candidate.get("owner_match") is True
    elif scope in {SCOPE_OBJECT, SCOPE_EQUIPMENT}:
        owner_match = _object_owner_match(object_name, fragment)

    item = dict(candidate)
    item.update({
        "document": document,
        "page": page,
        "context": fragment,
        "exact_clause": _text(candidate.get("exact_clause")) or fragment,
        "source_trace": _text(candidate.get("source_trace")) or fragment,
        "object": candidate_object or object_name,
        "owner_match": owner_match,
        "parameter_code": _text(requirement.get("parameter_code")).upper(),
        "unit": _text(candidate.get("unit") or requirement.get("unit")),
        "match_method": _text(candidate.get("match_method")) or "COVERAGE_EXECUTOR",
        "physical_trace_level": _text(candidate.get("physical_trace_level")) or "PAGE_TRACE",
        "source_locator": candidate.get("source_locator") or {
            "document": document,
            "page": page,
            "physical_trace_level": "PAGE_TRACE",
        },
    })
    if not item.get("evidence_state"):
        item["evidence_state"] = (
            "verified_candidate"
            if _text(candidate.get("evidence_kind")).upper().startswith("QUALIFIED_")
            else "candidate"
        )
    return item


def _candidate_key(item: dict[str, Any]) -> tuple[str, int, str]:
    return (
        _text(item.get("document")),
        int(item.get("page") or 0),
        normalize_text(item.get("context") or "")[:320],
    )


def attach_coverage_executor_evidence(
    requirements: list[dict[str, Any]],
    page_corpus: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bridge trusted Assignment kernels into the canonical Core25 evidence lane.

    25.0 had several useful deterministic/project-semantic checkers, but Core25
    only consumed numeric directed evidence. This bridge reuses those existing
    checkers as *retrieval/executor producers* while Core25 remains the only
    categorical proof/decision authority.
    """

    executors: Counter[str] = Counter()
    stats = {
        "requirements": len(requirements or []),
        "executor_hits": 0,
        "with_candidates": 0,
        "verified_candidates": 0,
        "new_candidates": 0,
        "executors": {},
    }

    for requirement in requirements or []:
        if not isinstance(requirement, dict):
            continue
        result = verify_assignment_requirement(requirement, page_corpus or [])
        if not isinstance(result, dict):
            continue

        executor = _text(result.get("verification_kernel") or "UNKNOWN_EXECUTOR")
        raw_candidates = list(
            result.get("verification_evidence")
            or result.get("evidence_candidates")
            or []
        )
        normalized: list[dict[str, Any]] = []
        for candidate in raw_candidates:
            if not isinstance(candidate, dict):
                continue
            item = _normalized_candidate(requirement, candidate)
            if item is not None:
                item["coverage_executor"] = executor
                normalized.append(item)

        if not normalized:
            continue

        stats["executor_hits"] += 1
        executors[executor] += 1
        existing = [
            dict(item) for item in requirement.get("directed_evidence_candidates") or []
            if isinstance(item, dict)
        ]
        seen = {_candidate_key(item) for item in existing}
        added = 0
        for item in normalized:
            key = _candidate_key(item)
            if key in seen:
                continue
            seen.add(key)
            existing.append(item)
            added += 1

        requirement["directed_evidence_candidates"] = existing
        requirement["coverage_executor"] = executor
        requirement["coverage_executor_status"] = _text(result.get("status"))
        requirement["coverage_executor_basis"] = _text(result.get("decision_basis"))
        if existing:
            stats["with_candidates"] += 1
        stats["verified_candidates"] += sum(
            _text(item.get("evidence_state")).lower() == "verified_candidate"
            for item in existing
        )
        stats["new_candidates"] += added

    stats["executors"] = dict(sorted(executors.items()))
    return stats
