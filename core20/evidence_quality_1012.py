from __future__ import annotations

import math
import re
from typing import Any

_INSTALLED = False
_ORIGINAL_RANK = None

ENGINE_VERSION = "20.0-alpha10.1.2-evidence-quality"

_GENERIC_TOPIC_STEMS = {
    "проект", "докум", "разде", "объек", "требо", "сведе", "решен",
    "описа", "обосн", "соста", "содер", "основ", "должн", "приве",
    "преду", "мероп", "харак", "часть", "данны", "инфор",
}


def _norm(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").replace("ё", "е").casefold().split())


def _stem(token: str) -> str:
    value = re.sub(r"[^a-zа-я0-9-]+", "", _norm(token))
    if not value:
        return ""
    if len(value) <= 4:
        return value
    return value[:5]


def _meaningful_stems(value: Any) -> list[str]:
    stems: list[str] = []
    for token in re.findall(r"[a-zа-я0-9-]+", _norm(value)):
        if len(token) < 3:
            continue
        stem = _stem(token)
        if not stem or stem in _GENERIC_TOPIC_STEMS:
            continue
        if stem not in stems:
            stems.append(stem)
    return stems


def toc_diagnostics(value: Any) -> dict[str, Any]:
    """Return explainable signals for table-of-contents and index-like pages.

    Continuation pages often lose the explicit heading "Содержание" during PDF
    extraction, so dot leaders, chains of numbered headings and trailing page
    references are evaluated independently of the heading itself.
    """
    original = str(value or "").replace("\xa0", " ")
    flat = " ".join(original.split())
    low = flat.casefold().replace("ё", "е")
    if not flat:
        return {
            "is_toc": False,
            "score": 0,
            "explicit_heading": False,
            "leader_page_refs": 0,
            "numbered_entries": 0,
            "lettered_entries": 0,
            "chained_page_refs": 0,
        }

    explicit_heading = bool(re.search(r"\b(?:содержание|оглавление)\b", low[:1800]))
    leader_page_refs = len(re.findall(r"(?:\.{3,}|…{2,})\s*\d{1,3}\b", original[:6000]))
    numbered_entries = len(re.findall(
        r"(?:^|\s)\d+(?:\.\d+){0,3}\s+[a-zа-я][a-zа-я-]{3,}",
        low[:6000],
    ))
    lettered_entries = len(re.findall(r"(?:^|\s)[а-я]\)\s+[a-zа-я][a-zа-я-]{3,}", low[:6000]))
    # Typical collapsed extraction: "... мероприятия 14 7 Сведения ... 18 8 ...".
    chained_page_refs = len(re.findall(
        r"\b\d{1,3}\s+(?=\d+(?:\.\d+){0,3}\s+[a-zа-я][a-zа-я-]{3,})",
        low[:6000],
    ))
    toc_vocabulary = len(re.findall(
        r"\b(?:сведения|обоснование|описание|мероприятия|характеристика|решения|перечень)\b",
        low[:6000],
    ))

    score = 0
    if explicit_heading:
        score += 3
    if leader_page_refs >= 2:
        score += 3
    elif leader_page_refs == 1:
        score += 1
    if numbered_entries >= 5:
        score += 3
    elif numbered_entries >= 3:
        score += 1
    if lettered_entries >= 4:
        score += 2
    if chained_page_refs >= 3:
        score += 3
    elif chained_page_refs >= 1:
        score += 1
    if toc_vocabulary >= 4:
        score += 1

    is_toc = bool(
        (explicit_heading and (leader_page_refs >= 1 or numbered_entries + lettered_entries >= 3))
        or leader_page_refs >= 3
        or (numbered_entries >= 5 and chained_page_refs >= 2)
        or (numbered_entries + lettered_entries >= 6 and chained_page_refs >= 2 and toc_vocabulary >= 3)
        or score >= 7
    )
    return {
        "is_toc": is_toc,
        "score": score,
        "explicit_heading": explicit_heading,
        "leader_page_refs": leader_page_refs,
        "numbered_entries": numbered_entries,
        "lettered_entries": lettered_entries,
        "chained_page_refs": chained_page_refs,
        "toc_vocabulary": toc_vocabulary,
    }


def is_toc_or_index_page(value: Any) -> bool:
    return bool(toc_diagnostics(value).get("is_toc"))


def topic_alignment(contract: dict[str, Any], page_text: Any) -> dict[str, Any]:
    """Fail closed when a page is lexically related but topically wrong.

    The first two meaningful tokens from the curated topic act as discriminators.
    This prevents, for example, a transport-communications page from proving the
    separate "Планировочная организация" requirement merely because both contain
    generic words such as "организация" or "земельный участок".
    """
    text = _norm(page_text)
    topic_stems = _meaningful_stems(contract.get("topic") or "")
    keyword_stems: list[str] = []
    for keyword in contract.get("keywords") or []:
        for stem in _meaningful_stems(keyword):
            if stem not in keyword_stems:
                keyword_stems.append(stem)

    # Prefer the curated topic as the semantic discriminator. If the topic is too
    # generic, fall back to curated keywords. Two anchors are deliberately strict:
    # absence of proof becomes REVIEW_QUESTION, never a negative project finding.
    required_anchors = topic_stems[:2]
    if not required_anchors:
        required_anchors = keyword_stems[:2]
    if not required_anchors:
        return {
            "eligible": True,
            "required_anchors": [],
            "matched_anchors": [],
            "coverage": 1.0,
            "reason": "NO_DISCRIMINATIVE_TOPIC_ANCHORS",
        }

    matched = [stem for stem in required_anchors if stem and stem in text]
    coverage = len(matched) / max(1, len(required_anchors))
    eligible = len(matched) == len(required_anchors)
    return {
        "eligible": eligible,
        "required_anchors": required_anchors,
        "matched_anchors": matched,
        "coverage": round(coverage, 3),
        "reason": "TOPIC_ALIGNED" if eligible else "TOPIC_ANCHOR_MISMATCH",
    }


def rank_candidates_quality(
    contract: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[tuple[int, float, int, dict[str, Any], list[str]]]:
    """Apply page-quality and topic gates before evidence can reach proof."""
    global _ORIGINAL_RANK
    if _ORIGINAL_RANK is None:
        from . import normative_execution as execution
        base_rank = execution._rank_candidates
    else:
        base_rank = _ORIGINAL_RANK

    ranked = list(base_rank(contract, candidates))
    accepted: list[tuple[int, float, int, dict[str, Any], list[str]]] = []
    for score, coverage, text_len, page, hits in ranked:
        raw_text = str(page.get("text") or page.get("content") or "")
        toc = toc_diagnostics(raw_text)
        if toc.get("is_toc"):
            continue
        alignment = topic_alignment(contract, raw_text)
        if not alignment.get("eligible"):
            continue
        enriched_page = dict(page)
        enriched_page["_evidence_quality"] = "SUBSTANTIVE_TOPIC_ALIGNED"
        enriched_page["_topic_alignment"] = alignment
        enriched_page["_toc_score"] = int(toc.get("score") or 0)
        accepted.append((score, coverage, text_len, enriched_page, hits))

    accepted.sort(
        key=lambda item: (
            float((item[3].get("_topic_alignment") or {}).get("coverage") or 0),
            item[0], item[1], item[2],
        ),
        reverse=True,
    )
    return accepted


def candidate_payloads_quality(
    ranked: list[tuple[int, float, int, dict[str, Any], list[str]]],
    requirement_id: str,
    *,
    limit: int = 4,
) -> list[dict[str, Any]]:
    """Create only substantive, topic-aligned addressable evidence payloads."""
    from . import normative_execution as execution

    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for score, coverage, _, page, hits in ranked:
        raw_text = str(page.get("text") or page.get("content") or "")
        if is_toc_or_index_page(raw_text):
            continue
        alignment = dict(page.get("_topic_alignment") or {})
        if alignment and not alignment.get("eligible"):
            continue
        document = str(page.get("document") or "").strip()
        page_no = page.get("page")
        fragment = execution._fragment(raw_text, hits)
        key = (document, str(page_no), fragment[:240])
        if key in seen:
            continue
        seen.add(key)
        index = len(output) + 1
        output.append({
            "evidence_id": f"NORM-E-{requirement_id}-{index:02d}",
            "document": document,
            "page": page_no,
            "section": str(page.get("document_type") or page.get("section") or ""),
            "fragment": fragment,
            "matched_keywords": list(hits),
            "retrieval_keyword_score": score,
            "retrieval_keyword_coverage": round(coverage, 3),
            "evidence_quality": "SUBSTANTIVE_TOPIC_ALIGNED",
            "semantic_eligible": True,
            "topic_alignment_coverage": float(alignment.get("coverage") or 1.0),
            "topic_required_anchors": list(alignment.get("required_anchors") or []),
            "topic_matched_anchors": list(alignment.get("matched_anchors") or []),
        })
        if len(output) >= limit:
            break
    return output


def install_evidence_quality_1012() -> None:
    """Install Alpha 10.1.2 fail-closed normative evidence quality gates."""
    global _INSTALLED, _ORIGINAL_RANK
    if _INSTALLED:
        return
    from . import normative_execution as execution

    _ORIGINAL_RANK = execution._rank_candidates
    execution._rank_candidates = rank_candidates_quality
    execution._candidate_payloads = candidate_payloads_quality
    execution.ENGINE_VERSION = ENGINE_VERSION
    _INSTALLED = True


__all__ = [
    "ENGINE_VERSION",
    "candidate_payloads_quality",
    "install_evidence_quality_1012",
    "is_toc_or_index_page",
    "rank_candidates_quality",
    "toc_diagnostics",
    "topic_alignment",
]
