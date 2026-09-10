from __future__ import annotations

import re
from typing import Any

from .parameter_contracts import (
    canonical_contract,
    equipment_terms,
    norm,
    structured_values,
)


def _section_matches(section: str, routes: list[str]) -> bool:
    if not routes:
        return True
    low=norm(section)
    return any(norm(route) in low or low in norm(route) for route in routes if norm(route))


def _context(text: str, anchor: str, radius: int=320) -> str:
    clean=re.sub(r"\s+"," ",str(text or "")).strip()
    low=norm(clean)
    pos=low.find(norm(anchor))
    if pos<0:
        return clean[:radius*2]
    return clean[max(0,pos-radius):pos+radius*2][:1200]


def route_typed_requirement_evidence(
    *,
    requirement_text: str,
    parameter_code: str,
    required_unit: str,
    expected_sections: list[str],
    page_corpus: list[dict[str,Any]],
    max_rows: int=6,
) -> list[dict[str,Any]]:
    """Find deterministic, parameter-anchored evidence in an existing page corpus.

    This router never emits a verdict. It only promotes a page fragment when the
    same typed parameter and an explicit compatible value/unit can be extracted.
    """
    contract=canonical_contract(parameter_code)
    if not contract:
        return []

    req_entities=equipment_terms(requirement_text)
    ranked=[]
    for page in page_corpus or []:
        if not isinstance(page,dict):
            continue
        section=str(page.get("document_type") or page.get("section") or page.get("document") or "")
        if not _section_matches(section,expected_sections):
            continue
        text=str(page.get("text") or "")
        low=norm(text)
        anchors=[anchor for anchor in contract.anchors if norm(anchor) in low]
        if not anchors:
            continue

        for anchor in anchors:
            snippet=_context(text,anchor)
            if req_entities and not (req_entities & equipment_terms(snippet)):
                continue
            facts=structured_values(
                parameter_code=parameter_code,
                requirement_text=requirement_text,
                required_unit=required_unit,
                evidence_fragment=snippet,
                evidence_meta={},
            )
            if not facts:
                continue
            for fact in facts:
                score=70
                if req_entities:
                    score+=12
                if expected_sections:
                    score+=8
                if any(x in norm(snippet) for x in ("проектом","предусмотр","принят","установлен","составляет")):
                    score+=5
                ranked.append((score,{
                    "evidence_kind":"CANONICAL_TYPED_PARAMETER_PASSAGE",
                    "evidence_state":"verified_candidate",
                    "document":page.get("document") or page.get("document_name") or "",
                    "document_type":page.get("document_type") or page.get("section") or "",
                    "page":page.get("page"),
                    "context":snippet,
                    "typed_parameter_code":str(parameter_code or "").upper(),
                    "project_parameter_code":str(parameter_code or "").upper(),
                    "project_value":fact.get("value"),
                    "project_unit":fact.get("unit"),
                    "semantic_level":fact.get("semantic_level") or "",
                    "binding":fact.get("binding") or "PARAMETER_ANCHOR",
                    "score":min(100,score),
                    "source_kind":"CANONICAL_PAGE_CORPUS_ROUTER",
                    "structured":True,
                }))

    ranked.sort(key=lambda x:x[0],reverse=True)
    out=[]
    seen=set()
    for _,row in ranked:
        key=(
            row.get("document"),row.get("page"),row.get("typed_parameter_code"),
            row.get("project_value"),row.get("project_unit"),
        )
        if key in seen:
            continue
        seen.add(key);out.append(row)
        if len(out)>=max_rows:
            break
    return out
