from __future__ import annotations

import math
import re
from typing import Any, Iterable

from .normalization import normalize_text


_RESPONSIBILITY_CLASS_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё0-9])к\s*с\s*[-–—]?\s*([1-3])(?=$|[^0-9])",
    re.I,
)
_GAMMA_DIRECT_RE = re.compile(
    r"(?:γ|Γ|гамм[аы]?)(?:\s*[_\-]?\s*n)?\s*[=:]?\s*(0[.,]\d+|1(?:[.,]\d+)?)",
    re.I,
)
_GAMMA_WORD_RE = re.compile(
    r"коэффициент\w*\s+(?:надежност|надёжност)\w*(?:\s+по\s+ответственност\w*)?.{0,80}?"
    r"(0[.,]\d+|1(?:[.,]\d+)?)",
    re.I | re.S,
)
_GENERIC_NAME_TOKENS = {
    "объект", "здание", "сооружение", "площадка", "комплекс", "система",
    "установка", "проектируемый", "проектируемая", "проектируемое", "поз",
}


def _norm(value: Any) -> str:
    return normalize_text(value).lower().replace("ё", "е")


def _position_pattern(position: str) -> re.Pattern[str] | None:
    pos = str(position or "").strip().replace(",", ".")
    if not re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){1,5}", pos):
        return None
    escaped = re.escape(pos)
    return re.compile(rf"(?<![\d.]){escaped}(?![\d.])")


def _name_tokens(name: str) -> list[str]:
    words = [
        word for word in re.findall(r"[a-zа-я0-9-]{4,}", _norm(name), re.I)
        if word not in _GENERIC_NAME_TOKENS
    ]
    return list(dict.fromkeys(words))


def _owner_present(name: str, text: str) -> bool:
    name_norm = _norm(name)
    text_norm = _norm(text)
    if name_norm and name_norm in text_norm:
        return True
    tokens = _name_tokens(name)
    if not tokens:
        return False
    hits = sum(token in text_norm for token in tokens)
    minimum = 1 if len(tokens) == 1 else 2
    return hits >= minimum and hits / len(tokens) >= 0.60


_ANY_POSITION_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){1,5})(?![\d.])")


def _attribute_value_sets(text: str) -> tuple[set[str], set[float]]:
    classes = {
        f"КС-{match.group(1)}"
        for match in _RESPONSIBILITY_CLASS_RE.finditer(str(text or ""))
    }
    gammas: set[float] = set()
    for regex in (_GAMMA_DIRECT_RE, _GAMMA_WORD_RE):
        for match in regex.finditer(str(text or "")):
            try:
                value = float(match.group(1).replace(",", "."))
            except ValueError:
                continue
            if 0.5 <= value <= 1.5:
                gammas.add(round(value, 3))
    return classes, gammas


def _record_is_unambiguous(text: str) -> bool:
    classes, gammas = _attribute_value_sets(text)
    return len(classes) <= 1 and len(gammas) <= 1


def _looks_like_position_only_line(line: str) -> bool:
    compact = " ".join(str(line or "").split()).replace(",", ".")
    compact = re.sub(r"^(?:поз\.?\s*)", "", compact, flags=re.I).strip()
    return bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){1,5}", compact))


def _has_columnar_position_block(text: str) -> bool:
    """Detect PDF table extraction where positions are emitted as a column.

    Two or more consecutive position-only lines mean row semantics are no
    longer preserved in plain text. Local record binding must then be disabled
    and only the stricter page-vector mapper may align attributes.
    """
    run = 0
    for line in (line.strip() for line in str(text or "").splitlines()):
        if not line:
            continue
        if _looks_like_position_only_line(line):
            run += 1
            if run >= 2:
                return True
        else:
            run = 0
    return False


def _position_record(text: str, *, position: str, object_name: str) -> str:
    """Return the smallest position-bound record that also contains the owner.

    Prefer line records. When PDF extraction flattens a table to one long line,
    fall back to the span from the exact position to the next distinct dotted
    position. Attribute ambiguity inside that local record is fail-closed.
    """
    raw = str(text or "")
    pattern = _position_pattern(position)
    if not raw or pattern is None:
        return ""
    if _has_columnar_position_block(raw):
        return ""

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) > 1:
        for index, line in enumerate(lines):
            if not pattern.search(line):
                continue
            bucket = [line]
            for nxt in lines[index + 1:index + 5]:
                other_positions = [
                    m.group(1).replace(",", ".")
                    for m in _ANY_POSITION_RE.finditer(nxt)
                ]
                if other_positions and any(p != position for p in other_positions):
                    break
                bucket.append(nxt)
                candidate = " ".join(bucket)
                if _owner_present(object_name, candidate):
                    attrs = extract_identification_attributes(candidate)
                    if attrs and _record_is_unambiguous(candidate):
                        return candidate

    flat = re.sub(r"\s+", " ", raw).strip()
    matches = list(pattern.finditer(flat))
    for match in matches:
        end = len(flat)
        for other in _ANY_POSITION_RE.finditer(flat, match.end()):
            if other.group(1).replace(",", ".") != position:
                end = other.start()
                break
        candidate = flat[match.start():min(end, match.start() + 1200)]
        if not _owner_present(object_name, candidate):
            continue
        if not _record_is_unambiguous(candidate):
            continue
        if extract_identification_attributes(candidate):
            return candidate
    return ""


def extract_identification_attributes(text: str) -> dict[str, Any]:
    raw = str(text or "")
    result: dict[str, Any] = {}

    class_match = _RESPONSIBILITY_CLASS_RE.search(raw)
    if class_match:
        result["responsibility_class"] = f"КС-{class_match.group(1)}"

    gamma_match = _GAMMA_DIRECT_RE.search(raw) or _GAMMA_WORD_RE.search(raw)
    if gamma_match:
        try:
            gamma = float(gamma_match.group(1).replace(",", "."))
        except ValueError:
            gamma = None
        if gamma is not None and 0.5 <= gamma <= 1.5:
            result["reliability_coefficient"] = gamma

    return result


def identity_context(
    text: str,
    *,
    position: str,
    object_name: str,
    radius: int = 700,
) -> str:
    """Return an exact position/owner record, never a broad neighbour window.

    The radius argument is retained for API compatibility but intentionally
    ignored. Identification attributes must be bound to the same local record
    as the exact GP position and object owner.
    """
    del radius
    return _position_record(text, position=position, object_name=object_name)

def _responsibility_class_sequence(text: str) -> list[str]:
    return [
        f"КС-{match.group(1)}"
        for match in _RESPONSIBILITY_CLASS_RE.finditer(str(text or ""))
    ]


def _reliability_coefficient_sequence(text: str) -> list[float]:
    matches = list(_GAMMA_DIRECT_RE.finditer(str(text or "")))
    if not matches:
        matches = list(_GAMMA_WORD_RE.finditer(str(text or "")))
    values: list[float] = []
    for match in matches:
        try:
            value = float(match.group(1).replace(",", "."))
        except ValueError:
            continue
        if 0.5 <= value <= 1.5:
            values.append(value)
    return values


def _page_mapping_is_addressable(
    items: list[dict[str, Any]],
    page_text: str,
) -> bool:
    """Require every expected row to be independently addressable on the page."""
    for item in items:
        position = str(item.get("position") or item.get("genplan_position") or "").strip()
        name = str(item.get("name") or item.get("object_name") or "").strip()
        pattern = _position_pattern(position)
        if not position or not name or pattern is None:
            return False
        if len(list(pattern.finditer(page_text))) != 1:
            return False
        if not _owner_present(name, page_text):
            return False
    return True


def _vector_alignment_safe(
    items: list[dict[str, Any]],
    values: list[Any],
    field: str,
) -> bool:
    if len(values) != len(items) or not values:
        return False
    # If every row carries the same value, row order is irrelevant.
    normalized = {str(value) for value in values}
    if len(normalized) == 1:
        return True
    # Otherwise require at least one exact local-record anchor at the same index.
    anchored = False
    for index, item in enumerate(items):
        existing = item.get(field)
        if existing in (None, ""):
            continue
        anchored = True
        if field == "reliability_coefficient":
            try:
                if not math.isclose(float(existing), float(values[index]), rel_tol=0.0, abs_tol=0.001):
                    return False
            except (TypeError, ValueError):
                return False
        elif str(existing).strip().upper() != str(values[index]).strip().upper():
            return False
    return anchored


def enrich_expected_objects_from_pages(
    expected_objects: Iterable[dict[str, Any]],
    pages: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    page_rows = [dict(page) for page in pages or () if isinstance(page, dict)]
    enriched = [dict(raw) for raw in expected_objects or ()]
    changed_indices: set[int] = set()

    # Stage 1: exact position + owner local-record evidence.
    for index, item in enumerate(enriched):
        if item.get("responsibility_class") and item.get("reliability_coefficient") is not None:
            continue
        position = str(item.get("position") or item.get("genplan_position") or "").strip()
        name = str(item.get("name") or item.get("object_name") or "").strip()
        if not position or not name:
            continue
        source_page = item.get("page")
        candidate_pages = [
            page for page in page_rows
            if source_page in (None, "", 0) or page.get("page") == source_page
        ] or page_rows
        best_attrs: dict[str, Any] = {}
        for page in candidate_pages:
            context = identity_context(str(page.get("text") or ""), position=position, object_name=name)
            if not context:
                continue
            attrs = extract_identification_attributes(context)
            if len(attrs) > len(best_attrs):
                best_attrs = attrs
            if len(best_attrs) >= 2:
                break
        before = (item.get("responsibility_class"), item.get("reliability_coefficient"))
        if best_attrs.get("responsibility_class"):
            item["responsibility_class"] = best_attrs["responsibility_class"]
        if best_attrs.get("reliability_coefficient") is not None:
            item["reliability_coefficient"] = best_attrs["reliability_coefficient"]
        after = (item.get("responsibility_class"), item.get("reliability_coefficient"))
        if after != before:
            item["identification_attributes_addressable"] = True
            item["identification_mapping_method"] = "LOCAL_POSITION_RECORD"
            changed_indices.add(index)

    # Stage 2: fail-closed columnar PDF fallback. Values are mapped by row order
    # only when page cardinality is exact and alignment is independently safe.
    groups: dict[int, list[int]] = {}
    for index, item in enumerate(enriched):
        try:
            page_no = int(item.get("page"))
        except (TypeError, ValueError):
            continue
        groups.setdefault(page_no, []).append(index)
    page_by_number = {}
    for page in page_rows:
        try:
            page_by_number[int(page.get("page"))] = str(page.get("text") or "")
        except (TypeError, ValueError):
            continue

    for page_no, indices in groups.items():
        page_text = page_by_number.get(page_no, "")
        items = [enriched[index] for index in indices]
        if not page_text or not _page_mapping_is_addressable(items, page_text):
            continue

        classes = _responsibility_class_sequence(page_text)
        if _vector_alignment_safe(items, classes, "responsibility_class"):
            for index, value in zip(indices, classes):
                item = enriched[index]
                if not item.get("responsibility_class"):
                    item["responsibility_class"] = value
                    item["identification_attributes_addressable"] = True
                    item["identification_mapping_method"] = "COLUMNAR_PAGE_VECTOR"
                    changed_indices.add(index)

        gammas = _reliability_coefficient_sequence(page_text)
        if _vector_alignment_safe(items, gammas, "reliability_coefficient"):
            for index, value in zip(indices, gammas):
                item = enriched[index]
                if item.get("reliability_coefficient") is None:
                    item["reliability_coefficient"] = value
                    item["identification_attributes_addressable"] = True
                    item["identification_mapping_method"] = "COLUMNAR_PAGE_VECTOR"
                    changed_indices.add(index)

    return enriched, len(changed_indices)

def enrich_identification_requirements(
    requirements: list[dict[str, Any]],
    assignment_pages: Iterable[dict[str, Any]],
) -> dict[str, int]:
    pages = [dict(page) for page in assignment_pages or () if isinstance(page, dict)]
    stats = {
        "requirements": 0,
        "objects": 0,
        "objects_enriched": 0,
        "with_responsibility_class": 0,
        "with_reliability_coefficient": 0,
    }

    for requirement in requirements or []:
        if not isinstance(requirement, dict):
            continue
        if str(requirement.get("requirement_type") or "").upper() != "SET_COMPARISON":
            continue
        title = _norm(requirement.get("source_row_title"))
        if "идентификацион" not in title:
            continue

        expected = [
            dict(item) for item in requirement.get("expected_objects") or []
            if isinstance(item, dict)
        ]
        if not expected:
            continue

        stats["requirements"] += 1
        stats["objects"] += len(expected)
        enriched, changed = enrich_expected_objects_from_pages(expected, pages)
        requirement["expected_objects"] = enriched
        requirement["identification_attribute_contract"] = True
        stats["objects_enriched"] += changed
        stats["with_responsibility_class"] += sum(
            bool(item.get("responsibility_class")) for item in enriched
        )
        stats["with_reliability_coefficient"] += sum(
            item.get("reliability_coefficient") is not None for item in enriched
        )

    return stats


def _exact_normalized_name_positions(name: str, normalized_page: str) -> list[int]:
    normalized_name = " ".join(_norm(name).split())
    if not normalized_name:
        return []
    return [match.start() for match in re.finditer(re.escape(normalized_name), normalized_page)]


def _project_columnar_responsibility_evidence(
    expected_objects: list[dict[str, Any]],
    project_pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return strict row-vector mismatches from canonical KR identification tables.

    This fallback is deliberately fail-closed. It is used only when plain-text
    extraction has separated positions, owners and responsibility classes into
    page-level columns. A page is admissible only when exact positions and exact
    full owner names are unique, their orders agree, and the responsibility-class
    vector has exactly the same cardinality as the matched rows.
    """
    evidence: list[dict[str, Any]] = []

    for page in project_pages:
        document_type = str(page.get("document_type") or "").strip().upper()
        if not document_type.startswith("КР"):
            continue

        raw = str(page.get("text") or "")
        if not raw:
            continue
        normalized = " ".join(_norm(raw).split())
        if not (
            "класс сооружен" in normalized
            or "класс ответствен" in normalized
            or "ответственност" in normalized
        ):
            continue

        matched: list[tuple[int, int, dict[str, Any]]] = []
        for item in expected_objects:
            position = str(item.get("position") or item.get("genplan_position") or "").strip()
            name = str(item.get("name") or item.get("object_name") or "").strip()
            pattern = _position_pattern(position)
            if not position or not name or pattern is None:
                continue

            position_occurrences = list(pattern.finditer(raw.replace(",", ".")))
            if len(position_occurrences) != 1:
                continue
            owner_occurrences = _exact_normalized_name_positions(name, normalized)
            if len(owner_occurrences) != 1:
                continue

            matched.append((position_occurrences[0].start(), owner_occurrences[0], item))

        if len(matched) < 2:
            continue

        matched.sort(key=lambda row: row[0])
        owner_sorted = sorted(matched, key=lambda row: row[1])
        position_order = [
            str(row[2].get("position") or row[2].get("genplan_position") or "").strip()
            for row in matched
        ]
        owner_order = [
            str(row[2].get("position") or row[2].get("genplan_position") or "").strip()
            for row in owner_sorted
        ]
        if owner_order != position_order:
            continue

        classes = _responsibility_class_sequence(raw)
        if len(classes) != len(matched):
            continue

        for index, (_, _, item) in enumerate(matched):
            if item.get("identification_attributes_addressable") is not True:
                continue
            required_class = str(item.get("responsibility_class") or "").strip().upper()
            if not required_class:
                continue
            observed_class = str(classes[index] or "").strip().upper()
            if not observed_class or observed_class == required_class:
                continue

            position = str(item.get("position") or item.get("genplan_position") or "").strip()
            object_name = str(item.get("name") or item.get("object_name") or "").strip()
            evidence.append({
                "evidence_kind": "IDENTIFICATION_ATTRIBUTE_COMPARISON",
                "evidence_state": "verified_candidate",
                "document": page.get("document"),
                "document_type": page.get("document_type"),
                "page": page.get("page"),
                "source_kind": "STRUCTURED_ROW",
                "context": (
                    f"Структурированная строка идентификационной таблицы: "
                    f"поз. {position}; {object_name}; {observed_class}."
                ),
                "score": 100,
                "object": object_name,
                "position": position,
                "exact_position_match": True,
                "owner_match": True,
                "verified_difference": True,
                "mismatch_fields": ["responsibility_class"],
                "required_responsibility_class": required_class,
                "observed_responsibility_class": observed_class,
                "required_reliability_coefficient": item.get("reliability_coefficient"),
                "observed_reliability_coefficient": None,
                "identification_mapping_method": "PROJECT_COLUMNAR_PAGE_VECTOR",
                "columnar_row_count": len(matched),
                "columnar_class_count": len(classes),
            })

    return evidence


def compare_identification_attributes(
    requirement: dict[str, Any],
    project_pages: Iterable[dict[str, Any]],
) -> dict[str, Any] | None:
    if str(requirement.get("requirement_type") or "").upper() != "SET_COMPARISON":
        return None
    title = _norm(requirement.get("source_row_title"))
    if "идентификацион" not in title:
        return None

    all_expected = [
        dict(item) for item in requirement.get("expected_objects") or []
        if isinstance(item, dict)
    ]
    expected = [
        item for item in all_expected
        if (
            item.get("responsibility_class")
            or item.get("reliability_coefficient") is not None
        )
    ]
    if not expected:
        return None

    pages = [dict(page) for page in project_pages or () if isinstance(page, dict)]
    evidence: list[dict[str, Any]] = _project_columnar_responsibility_evidence(
        all_expected, pages
    )

    for item in expected:
        position = str(item.get("position") or item.get("genplan_position") or "").strip()
        object_name = str(item.get("name") or item.get("object_name") or "").strip()
        if not position or not object_name:
            continue

        required_class = str(item.get("responsibility_class") or "").strip().upper()
        try:
            required_gamma = (
                float(item.get("reliability_coefficient"))
                if item.get("reliability_coefficient") is not None
                else None
            )
        except (TypeError, ValueError):
            required_gamma = None

        for page in pages:
            context = identity_context(
                str(page.get("text") or ""),
                position=position,
                object_name=object_name,
            )
            if not context:
                continue
            observed = extract_identification_attributes(context)
            observed_class = str(observed.get("responsibility_class") or "").strip().upper()
            observed_gamma = observed.get("reliability_coefficient")

            mismatch_fields: list[str] = []
            if required_class and observed_class and required_class != observed_class:
                mismatch_fields.append("responsibility_class")
            if (
                required_gamma is not None
                and observed_gamma is not None
                and not math.isclose(required_gamma, float(observed_gamma), rel_tol=0.0, abs_tol=0.001)
            ):
                mismatch_fields.append("reliability_coefficient")

            if not mismatch_fields:
                continue

            evidence.append({
                "evidence_kind": "IDENTIFICATION_ATTRIBUTE_COMPARISON",
                "evidence_state": "verified_candidate",
                "document": page.get("document"),
                "document_type": page.get("document_type"),
                "page": page.get("page"),
                "context": context,
                "score": 100,
                "object": object_name,
                "position": position,
                "exact_position_match": True,
                "owner_match": True,
                "verified_difference": True,
                "mismatch_fields": mismatch_fields,
                "required_responsibility_class": required_class,
                "observed_responsibility_class": observed_class,
                "required_reliability_coefficient": required_gamma,
                "observed_reliability_coefficient": observed_gamma,
            })
            break

    if not evidence:
        return None

    return {
        "status": "Выявлено отклонение",
        "evidence": [
            f"{row.get('document')}, стр. {row.get('page')}: {row.get('context')}"
            for row in evidence
        ],
        "evidence_candidates": evidence,
        "verification_evidence": evidence,
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE",
        "match_confidence": 1.0,
        "difference": "; ".join(
            f"{row.get('position')}: {', '.join(row.get('mismatch_fields') or [])}"
            for row in evidence
        ),
        "decision_basis": (
            "По точной позиции по генплану и наименованию объекта найдено адресное "
            "несовпадение идентификационных характеристик Задания и проектной документации."
        ),
        "verification_kernel": "IDENTIFICATION_ATTRIBUTE_COMPARISON_EXECUTOR",
    }
