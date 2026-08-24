from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from .normalization import normalize_text
from .page_evidence_store import canonical_section, is_assignment_source


GRAPH_VERSION = "1.0-universal-project-facts"


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return normalize_text(value).lower().replace("ё", "е")


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(_txt(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:14].upper()
    return f"{prefix}-{digest}"


def _position(row: dict[str, Any]) -> str:
    return _txt(row.get("Позиция по ГП") or row.get("position") or row.get("genplan_position"))


def _entity_name(row: dict[str, Any]) -> str:
    return _txt(
        row.get("Наименование объекта") or row.get("object_name") or row.get("name")
        or row.get("project_understanding_object_name") or row.get("semantic_anchor_name")
        or row.get("object_hint") or row.get("owner") or row.get("entity_name")
    )


def _metric(row: dict[str, Any]) -> tuple[str, str]:
    code = _txt(row.get("parameter_code") or row.get("metric_code") or row.get("indicator_code") or row.get("metric"))
    name = _txt(row.get("parameter_name") or row.get("indicator") or row.get("metric_name") or code)
    return code, name


def _source(row: dict[str, Any]) -> tuple[str, Any, str]:
    document = _txt(row.get("document") or row.get("source_document") or row.get("Файл") or row.get("source"))
    page = row.get("page") or row.get("source_page") or row.get("Страница") or ""
    section = canonical_section(row.get("document_type") or row.get("section_family") or row.get("section") or document)
    return document, page, section


def _admission(row: dict[str, Any]) -> tuple[bool, str]:
    admission = _txt(row.get("fact_admission_decision")).upper()
    quality = _txt(row.get("evidence_quality_decision")).upper()
    binding = _txt(row.get("binding_status") or row.get("property_binding_status")).upper()
    integrity = _txt(row.get("row_integrity_status")).upper()
    if admission in {"HOLD", "REJECT"} or quality in {"HOLD", "REJECT", "BLOCKED"}:
        return False, admission or quality
    if integrity.startswith("BLOCKED") or row.get("comparison_excluded"):
        return False, integrity or "COMPARISON_EXCLUDED"
    if admission == "ADMIT" or quality in {"VERIFIED", "SUPPORTED"}:
        return True, admission or quality
    if binding in {"ROW_LOCKED", "POSITION_LOCKED", "EXACT_OBJECT"}:
        return True, binding
    if row.get("directed_evidence"):
        return True, "DIRECTED_EVIDENCE"
    # Candidate facts remain in a separate layer and cannot close a verdict.
    return False, admission or quality or binding or "CANDIDATE"


def _value(row: dict[str, Any]) -> Any:
    for key in ("value", "value_num", "normalized_value", "value_text"):
        if row.get(key) not in (None, ""):
            return row.get(key)
    return None


def _aliases(name: str) -> list[str]:
    low = _norm(name)
    variants = {low, re.sub(r"[^a-zа-я0-9]", "", low)}
    variants.update(part for part in re.split(r"\s*[(),/]\s*", low) if len(part) >= 4)
    return sorted(x for x in variants if x)


def build_universal_project_fact_graph(
    registry: Iterable[dict[str, Any]] | None = None,
    findings: Iterable[dict[str, Any]] | None = None,
    page_corpus: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the single evidence model used by every verification domain.

    The graph contains admitted facts and candidate facts in different layers.
    Only admitted facts may support a categorical comparison.  Raw passages are
    searchable evidence, not engineering facts.
    """
    entities: list[dict[str, Any]] = []
    entity_by_key: dict[str, dict[str, Any]] = {}
    for row in registry or []:
        name = _entity_name(row)
        position = _position(row)
        if not name:
            continue
        key = f"{position}|{_norm(name)}"
        if key in entity_by_key:
            continue
        entity = {
            "entity_id": _stable_id("ENT", position, name),
            "entity_type": _txt(row.get("Тип объекта") or row.get("object_type") or "PROJECT_OBJECT"),
            "name": name,
            "position": position,
            "aliases": _aliases(name),
            "project_scope": "IN_SCOPE",
            "source": _txt(row.get("Источник") or row.get("source") or row.get("Причины решения")),
        }
        entities.append(entity)
        entity_by_key[key] = entity

    facts: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    sources: dict[str, dict[str, Any]] = {}
    entity_alias_index: dict[str, str] = {}
    for entity in entities:
        for alias in entity["aliases"]:
            entity_alias_index.setdefault(alias, entity["entity_id"])

    for row in findings or []:
        document, page, section = _source(row)
        if is_assignment_source({"document": document, "document_type": section}):
            continue
        code, metric_name = _metric(row)
        value = _value(row)
        owner_name = _entity_name(row)
        if not (code or metric_name or value not in (None, "")):
            continue
        admitted, admission_reason = _admission(row)
        owner_norm = _norm(owner_name)
        entity_id = ""
        if owner_norm:
            for alias, candidate_id in entity_alias_index.items():
                if owner_norm == alias or owner_norm in alias or alias in owner_norm:
                    entity_id = candidate_id
                    break
        if not entity_id and owner_name and not any(token in owner_norm for token in ("площадь", "мощность", "объем", "объём", "количество")):
            entity_id = _stable_id("ENT-CAND", owner_name)
        if not entity_id and code:
            entity_id = "ENT-PROJECT"

        source_id = _stable_id("SRC", document, page, section)
        if document:
            sources.setdefault(source_id, {
                "source_id": source_id,
                "document": document,
                "page": page,
                "section": section,
                "locator": f"{document}, стр. {page}" if page not in (None, "") else document,
            })
        fact = {
            "fact_id": _stable_id("FACT", entity_id, code, value, row.get("unit"), document, page, row.get("row_text")),
            "entity_id": entity_id,
            "owner": owner_name or ("Проект" if entity_id == "ENT-PROJECT" else ""),
            "property_code": code,
            "property_name": metric_name,
            "value": value,
            "unit": _txt(row.get("unit") or row.get("units")),
            "qualifier": _txt(row.get("qualifier") or row.get("semantic_level") or row.get("scope")),
            "source_id": source_id if document else "",
            "document": document,
            "page": page,
            "section": section,
            "source_trace": _txt(row.get("source_trace") or row.get("physical_trace") or row.get("table_evidence") or row.get("context"))[:1200],
            "admitted": admitted,
            "admission_reason": admission_reason,
            "binding_status": _txt(row.get("binding_status") or row.get("property_binding_status")),
            "requirement_id": _txt(row.get("requirement_id")),
        }
        (facts if admitted else candidates).append(fact)

    passages: list[dict[str, Any]] = []
    for page in page_corpus or []:
        document = _txt(page.get("document"))
        section = canonical_section(page.get("document_type") or document)
        if not document or not section or is_assignment_source(page):
            continue
        text = re.sub(r"\s+", " ", _txt(page.get("text")))
        if not text:
            continue
        source_id = _stable_id("SRC", document, page.get("page"), section)
        sources.setdefault(source_id, {
            "source_id": source_id,
            "document": document,
            "page": page.get("page") or "",
            "section": section,
            "locator": f"{document}, стр. {page.get('page')}" if page.get("page") else document,
        })
        passages.append({
            "passage_id": _stable_id("PASS", document, page.get("page"), text[:300]),
            "source_id": source_id,
            "document": document,
            "page": page.get("page") or "",
            "section": section,
            "text": text,
            "normalized_text": _norm(text),
            "evidence_level": "SOURCE_PASSAGE",
        })

    by_property: dict[str, list[str]] = defaultdict(list)
    by_entity: dict[str, list[str]] = defaultdict(list)
    by_section: dict[str, list[str]] = defaultdict(list)
    for fact in facts:
        if fact["property_code"]:
            by_property[fact["property_code"]].append(fact["fact_id"])
        if fact["entity_id"]:
            by_entity[fact["entity_id"]].append(fact["fact_id"])
        if fact["section"]:
            by_section[fact["section"]].append(fact["fact_id"])

    edges = []
    for fact in facts:
        if fact["entity_id"]:
            edges.append({"from": fact["entity_id"], "to": fact["fact_id"], "relation": "HAS_PROPERTY"})
        if fact["source_id"]:
            edges.append({"from": fact["fact_id"], "to": fact["source_id"], "relation": "EVIDENCED_BY"})

    return {
        "version": GRAPH_VERSION,
        "entities": entities,
        "facts": facts,
        "candidate_facts": candidates,
        "sources": list(sources.values()),
        "passages": passages,
        "edges": edges,
        "indexes": {
            "by_property": dict(by_property),
            "by_entity": dict(by_entity),
            "by_section": dict(by_section),
        },
        "summary": {
            "entities": len(entities),
            "admitted_facts": len(facts),
            "candidate_facts": len(candidates),
            "sources": len(sources),
            "page_passages": len(passages),
            "facts_with_owner": sum(bool(fact["entity_id"]) for fact in facts),
            "facts_with_source": sum(bool(fact["source_id"] and fact["page"] not in (None, "")) for fact in facts),
            "by_section": dict(sorted(Counter(fact["section"] or "UNRESOLVED" for fact in facts).items())),
            "by_property": dict(Counter(fact["property_code"] or "UNRESOLVED" for fact in facts).most_common(40)),
        },
    }


def fact_lookup(graph: dict[str, Any], *, property_code: str = "", entity_id: str = "", section: str = "") -> list[dict[str, Any]]:
    rows = list(graph.get("facts") or [])
    if property_code:
        rows = [row for row in rows if _txt(row.get("property_code")).upper() == _txt(property_code).upper()]
    if entity_id:
        rows = [row for row in rows if row.get("entity_id") == entity_id]
    if section:
        wanted = canonical_section(section)
        rows = [row for row in rows if canonical_section(row.get("section")) == wanted]
    return rows

