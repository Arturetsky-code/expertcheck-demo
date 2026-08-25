from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


BENCHMARK_VERSION = "1.0-external-golden-corpus"


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower().replace("ё", "е")).strip()


def load_benchmark(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Benchmark JSON must contain a cases array.")
    seen: set[str] = set()
    for index, case in enumerate(cases, 1):
        case_id = str(case.get("case_id") or "").strip()
        if not case_id or case_id in seen:
            raise ValueError(f"Case #{index} has an empty or duplicate case_id.")
        seen.add(case_id)
        if not isinstance(case.get("match") or {}, dict):
            raise ValueError(f"Case {case_id}: match must be an object.")
    return payload


def _row_blob(row: dict[str, Any]) -> str:
    keys = (
        "object", "object_name", "parameter_code", "parameter_name", "title",
        "requirement_text", "question", "status", "result", "explanation",
        "decision_basis", "sources", "document_values", "document", "section",
    )
    return _norm(" ".join(str(row.get(key) or "") for key in keys))


def _kind(row: dict[str, Any]) -> str:
    explicit = str(row.get("final_verification_kind") or row.get("verification_kind") or row.get("finding_type") or "").upper()
    if explicit:
        return explicit
    status = _norm(row.get("status") or row.get("result"))
    if any(token in status for token in ("расхожд", "конфликт", "не соответствует", "выявлено отклон")):
        return "PROJECT_FINDING"
    if "требует провер" in status:
        return "REVIEW_QUESTION"
    if any(token in status for token in ("не проверено", "недостаточно данных", "нет данных")):
        return "SYSTEM_LIMITATION"
    if any(token in status for token in ("совпадает", "соответствует", "подтвержден")):
        return "VERIFIED_OK"
    return "INFORMATIONAL"


def _addressable(row: dict[str, Any]) -> bool:
    if row.get("document") and row.get("page") not in (None, ""):
        return True
    for key in ("verification_evidence", "evidence_candidates", "deep_evidence_candidates"):
        for evidence in row.get(key) or []:
            if isinstance(evidence, dict) and evidence.get("document") and evidence.get("page") not in (None, ""):
                return True
    sources = _norm(row.get("sources"))
    return bool(sources and ("стр." in sources or "стр " in sources))


def flatten_result_rows(payload: Any) -> list[dict[str, Any]]:
    """Extract result-like rows from a normalised export or pipeline snapshot."""
    rows: list[dict[str, Any]] = []
    visited: set[int] = set()
    result_keys = {
        "comparisons", "assignment_atomic_compliance", "assignment_compliance",
        "normative_compliance_audit", "results", "items", "checks",
    }

    def walk(value: Any, active: bool = False, depth: int = 0) -> None:
        if depth > 10:
            return
        if isinstance(value, (dict, list)):
            marker = id(value)
            if marker in visited:
                return
            visited.add(marker)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and active:
                    rows.append(item)
                walk(item, active=active, depth=depth + 1)
        elif isinstance(value, dict):
            row_like = any(key in value for key in ("verification_kind", "finding_type", "status", "result")) and any(
                key in value for key in ("parameter_code", "requirement_id", "check_code", "question", "title")
            )
            if active and row_like:
                rows.append(value)
            for key, child in value.items():
                walk(child, active=active or key in result_keys, depth=depth + 1)

    walk(payload)
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        identity = str(row.get("check_code") or row.get("requirement_id") or row.get("atom_id") or row.get("plan_id") or "") + "|" + _row_blob(row)
        digest = hashlib.sha1(identity.encode("utf-8", "ignore")).hexdigest()
        if digest not in seen:
            seen.add(digest); unique.append(row)
    return unique


def match_rows(case: dict[str, Any], rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    match = case.get("match") or {}
    codes = {str(value).upper() for value in match.get("parameter_codes") or []}
    all_terms = [_norm(value) for value in match.get("all_terms") or [] if _norm(value)]
    any_terms = [_norm(value) for value in match.get("any_terms") or [] if _norm(value)]
    document_terms = [_norm(value) for value in match.get("document_terms") or [] if _norm(value)]
    result = []
    for row in rows or []:
        blob = _row_blob(row)
        code = str(row.get("parameter_code") or row.get("metric") or "").upper()
        if codes and code not in codes:
            continue
        if all_terms and not all(term in blob for term in all_terms):
            continue
        if any_terms and not any(term in blob for term in any_terms):
            continue
        if document_terms:
            document_blob = _norm(" ".join(str(row.get(key) or "") for key in ("document", "sources", "documents", "section")))
            if not any(term in document_blob for term in document_terms):
                continue
        result.append(row)
    return result


def _evaluate_phase(case: dict[str, Any], rows: list[dict[str, Any]], phase: str) -> dict[str, Any] | None:
    expected = str(case.get(f"expected_{phase}") or "").upper()
    if not expected:
        return None
    matches = match_rows(case, rows)
    findings = [row for row in matches if _kind(row) == "PROJECT_FINDING"]
    reviews = [row for row in matches if _kind(row) == "REVIEW_QUESTION"]
    addressable = any(_addressable(row) for row in findings or reviews or matches)
    if expected == "PROJECT_FINDING":
        label = "TP" if findings else "FN"
    elif expected in {"NO_PROJECT_FINDING", "VERIFIED_OK"}:
        label = "FP" if findings else "TN"
    elif expected == "REVIEW_QUESTION":
        label = "TP" if reviews else "FN"
    else:
        raise ValueError(f"Unsupported expected_{phase}={expected} in {case.get('case_id')}")
    return {
        "case_id": case.get("case_id"), "phase": phase, "category": case.get("category") or "UNCLASSIFIED",
        "expected": expected, "label": label, "matched_rows": len(matches),
        "project_findings": len(findings), "review_questions": len(reviews),
        "addressable_evidence": addressable,
        "matched_ids": [str(row.get("check_code") or row.get("requirement_id") or row.get("plan_id") or "") for row in matches[:10]],
    }


def evaluate_benchmark(
    benchmark: dict[str, Any], *, before_payload: Any = None, after_payload: Any = None,
) -> dict[str, Any]:
    before_rows = flatten_result_rows(before_payload) if before_payload is not None else []
    after_rows = flatten_result_rows(after_payload) if after_payload is not None else []
    evaluations = []
    for case in benchmark.get("cases") or []:
        if before_payload is not None:
            result = _evaluate_phase(case, before_rows, "before")
            if result: evaluations.append(result)
        if after_payload is not None:
            result = _evaluate_phase(case, after_rows, "after")
            if result: evaluations.append(result)
    counts = Counter(row["label"] for row in evaluations)
    tp, fp, fn = counts["TP"], counts["FP"], counts["FN"]
    precision = tp / max(1, tp + fp); recall = tp / max(1, tp + fn)
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    for row in evaluations:
        by_category[str(row["category"])][str(row["label"])] += 1
    return {
        "version": BENCHMARK_VERSION,
        "benchmark_id": benchmark.get("benchmark_id") or "external",
        "cases": len(benchmark.get("cases") or []),
        "evaluations": len(evaluations),
        "summary": {
            "true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": counts["TN"],
            "precision_pct": round(100 * precision, 1), "recall_pct": round(100 * recall, 1),
            "f1_pct": round(200 * precision * recall / max(1e-12, precision + recall), 1) if precision + recall else 0.0,
            "addressable_evidence_pct": round(100 * sum(row["addressable_evidence"] for row in evaluations) / max(1, len(evaluations)), 1),
        },
        "by_category": {category: dict(counts) for category, counts in sorted(by_category.items())},
        "results": evaluations,
        "policy": "Raw benchmark documents and expert remarks remain external; only schema, hashes and aggregate metrics belong to the release.",
    }


def build_corpus_manifest(root: str | Path, cache_path: str | Path | None = None) -> dict[str, Any]:
    """Hash an external corpus incrementally without copying it into ExpertCheck."""
    root = Path(root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(root)
    cache_file = Path(cache_path) if cache_path else None
    cache = {}
    if cache_file and cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8")).get("files") or {}
        except Exception:
            cache = {}
    files = {}; reused = hashed = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix(); stat = path.stat()
        signature = f"{stat.st_size}:{stat.st_mtime_ns}"
        old = cache.get(relative) or {}
        if old.get("signature") == signature and old.get("sha256"):
            digest = old["sha256"]; reused += 1
        else:
            sha = hashlib.sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
                    sha.update(chunk)
            digest = sha.hexdigest(); hashed += 1
        files[relative] = {"size": stat.st_size, "signature": signature, "sha256": digest, "suffix": path.suffix.lower()}
    manifest = {
        "version": BENCHMARK_VERSION, "root_name": root.name, "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files.values()), "hashed": hashed, "cache_reused": reused,
        "files": files,
    }
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest

