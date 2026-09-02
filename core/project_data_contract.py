from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from datetime import date, datetime
import hashlib
import json
import math
from typing import Any, Iterable


CONTRACT_VERSION = "18.0-project-data-contract-v1"

_TEXT_FIELDS = {
    "Файл", "Тип документа", "document", "document_type", "filename",
    "object", "object_name", "object_hint", "parameter", "parameter_name",
    "parameter_code", "status", "result", "finding_type", "user_status",
    "comparison_id", "check_id", "check_code", "rule_id", "unit",
    "final_verification_kind", "verification_kind", "evidence_level",
    "cross_section_gate_state", "source_locator",
}

_LIST_FIELDS = {
    "sources", "sections", "evidence", "verification_evidence",
    "cross_section_gate_reasons", "data_owner_sections", "dependent_sections",
    "deep_evidence_reasons", "adversarial_reasons", "semantic_gate_reasons",
    "semantic_consensus_reasons", "missing_evidence_slots",
    "expected_evidence_route", "expected_sections", "blocking_reasons",
}

_DICT_FIELDS = {
    "dependency_diagnostics", "engineering_binding", "difference",
    "evidence_contract", "evidence_contract_v2", "verification_recipe",
    "semantic_judge", "semantic_critic", "cross_section_gate",
}


def _is_missing_scalar(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value) or math.isinf(value)
    return str(value).strip().casefold() in {"nan", "nat", "none", "<na>"}


def _repair(audit: dict[str, Any], kind: str, path: str, before: Any, after: Any) -> None:
    audit["repairs_by_kind"][kind] += 1
    if len(audit["repair_examples"]) < 30:
        audit["repair_examples"].append({
            "kind": kind,
            "path": path,
            "before_type": type(before).__name__,
            "after_type": type(after).__name__,
        })


def _json_value(value: Any, path: str, audit: dict[str, Any], active: set[int]) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            _repair(audit, "non_finite_number", path, value, None)
            return None
        return value
    if isinstance(value, (datetime, date)):
        rendered = value.isoformat()
        _repair(audit, "date_to_iso", path, value, rendered)
        return rendered
    if isinstance(value, bytes):
        rendered = value.decode("utf-8", errors="replace")
        _repair(audit, "bytes_to_text", path, value, rendered)
        return rendered

    marker = id(value)
    if marker in active:
        _repair(audit, "cyclic_reference", path, value, "[циклическая ссылка]")
        return "[циклическая ссылка]"

    if isinstance(value, Mapping):
        active.add(marker)
        result: dict[str, Any] = {}
        for key, item in value.items():
            text_key = str(key)
            if not isinstance(key, str):
                _repair(audit, "mapping_key_to_text", f"{path}.{text_key}", key, text_key)
            result[text_key] = _json_value(item, f"{path}.{text_key}", audit, active)
        active.discard(marker)
        return result

    if isinstance(value, (list, tuple, set)):
        active.add(marker)
        result = [
            _json_value(item, f"{path}[{index}]", audit, active)
            for index, item in enumerate(value)
        ]
        active.discard(marker)
        if not isinstance(value, list):
            _repair(audit, "sequence_to_list", path, value, result)
        return result

    # numpy/pandas scalar values expose item(); keep this optional so the core
    # contract has no dependency on either package.
    item_method = getattr(value, "item", None)
    if callable(item_method):
        try:
            scalar = item_method()
            if scalar is not value:
                normalized = _json_value(scalar, path, audit, active)
                _repair(audit, "scalar_unboxed", path, value, normalized)
                return normalized
        except Exception:
            pass

    rendered = str(value)
    _repair(audit, "unsupported_to_text", path, value, rendered)
    return rendered


def _stable_id(prefix: str, row: dict[str, Any], fields: tuple[str, ...]) -> str:
    identity = "|".join(str(row.get(field) or "").strip() for field in fields)
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:14].upper()
    return f"{prefix}-{digest}"


def _normalize_rows(
    values: Iterable[Any] | None,
    *,
    domain: str,
    prefix: str,
    audit: dict[str, Any],
) -> list[dict[str, Any]]:
    if values is None:
        return []
    if isinstance(values, Mapping) or isinstance(values, (str, bytes)):
        audit["fatal_issues"].append(f"{domain}: ожидался список строк.")
        values = [values]
    try:
        source_rows = list(values)
    except TypeError:
        audit["fatal_issues"].append(f"{domain}: результат не является коллекцией строк.")
        return []

    normalized: list[dict[str, Any]] = []
    for index, source in enumerate(source_rows):
        if not isinstance(source, Mapping):
            audit["fatal_issues"].append(
                f"{domain}[{index}]: строка типа {type(source).__name__} исключена."
            )
            continue
        row = _json_value(source, f"{domain}[{index}]", audit, set())
        assert isinstance(row, dict)

        for field in _TEXT_FIELDS.intersection(row):
            value = row.get(field)
            if _is_missing_scalar(value):
                if value is not None:
                    _repair(audit, "missing_text_to_none", f"{domain}[{index}].{field}", value, None)
                row[field] = None
            elif not isinstance(value, str):
                rendered = str(value).strip()
                _repair(audit, "text_field_coercion", f"{domain}[{index}].{field}", value, rendered)
                row[field] = rendered

        for field in _LIST_FIELDS.intersection(row):
            value = row.get(field)
            if value is None:
                row[field] = []
            elif not isinstance(value, list):
                repaired = [value]
                _repair(audit, "list_field_wrapped", f"{domain}[{index}].{field}", value, repaired)
                row[field] = repaired

        for field in _DICT_FIELDS.intersection(row):
            value = row.get(field)
            if value is None:
                row[field] = {}
            elif not isinstance(value, dict):
                _repair(audit, "dict_field_reset", f"{domain}[{index}].{field}", value, {})
                row[field] = {}

        if domain == "documents":
            row.setdefault("contract_id", _stable_id(prefix, row, (
                "Файл", "document", "filename", "Тип документа", "document_type",
            )))
        elif domain == "findings":
            row.setdefault("finding_id", _stable_id(prefix, row, (
                "document", "page", "parameter_code", "object_hint", "value", "unit",
            )))
        else:
            current = row.get("comparison_id") or row.get("check_id") or row.get("check_code")
            if _is_missing_scalar(current):
                row["comparison_id"] = _stable_id(prefix, row, (
                    "object", "object_name", "parameter", "parameter_name", "status", "sources",
                ))
        normalized.append(row)
    return normalized


def _identity_fingerprint(
    documents: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> str:
    payload = {
        "documents": [
            [row.get("contract_id"), row.get("Файл") or row.get("document"), row.get("Тип документа") or row.get("document_type"), row.get("Страниц") or row.get("page_count")]
            for row in documents
        ],
        "findings": [
            [row.get("finding_id"), row.get("document"), row.get("page"), row.get("parameter_code"), row.get("object_hint"), row.get("value"), row.get("unit")]
            for row in findings
        ],
        "comparisons": [
            [row.get("comparison_id") or row.get("check_id"), row.get("object") or row.get("object_name"), row.get("parameter") or row.get("parameter_name"), row.get("status"), row.get("final_verification_kind")]
            for row in comparisons
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def enforce_project_data_contract(
    documents: Iterable[Any] | None,
    findings: Iterable[Any] | None,
    comparisons: Iterable[Any] | None,
    *,
    source: str = "pipeline",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Normalize the three public result collections and return an audit record."""
    audit: dict[str, Any] = {
        "version": CONTRACT_VERSION,
        "source": source,
        "repairs_by_kind": Counter(),
        "repair_examples": [],
        "fatal_issues": [],
    }
    normalized_documents = _normalize_rows(documents, domain="documents", prefix="DOC", audit=audit)
    normalized_findings = _normalize_rows(findings, domain="findings", prefix="FND", audit=audit)
    normalized_comparisons = _normalize_rows(comparisons, domain="comparisons", prefix="CMP", audit=audit)

    repairs = sum(audit["repairs_by_kind"].values())
    audit["repairs_by_kind"] = dict(audit["repairs_by_kind"])
    audit["repairs"] = repairs
    audit["counts"] = {
        "documents": len(normalized_documents),
        "findings": len(normalized_findings),
        "comparisons": len(normalized_comparisons),
    }
    audit["result_identity_fingerprint"] = _identity_fingerprint(
        normalized_documents, normalized_findings, normalized_comparisons,
    )
    audit["status"] = (
        "FAILED" if audit["fatal_issues"] else "REPAIRED" if repairs else "PASSED"
    )
    return normalized_documents, normalized_findings, normalized_comparisons, audit
