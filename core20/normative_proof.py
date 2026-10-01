from __future__ import annotations

from collections import Counter
from typing import Any


ENGINE_VERSION = "20.0-alpha9-normative-proof-multi-evidence"

PROOF_TYPES = (
    "PRESENCE",
    "STRUCTURE",
    "SET_COMPLETENESS",
    "SEMANTIC_REQUIREMENT",
    "GRAPHIC_CONTENT",
    "TYPED_VALUE",
    "CROSS_SECTION",
)


def _norm(value: Any) -> str:
    return " ".join(str(value or "").replace("ё", "е").casefold().replace("\xa0", " ").split())


def _proof_type(row: dict[str, Any]) -> str:
    """Classify how a verified clause must actually be proven.

    Retrieval and proof are intentionally separate. Requirements that ask for an
    engineering justification, consistency or multi-part content are never
    confirmed by lexical overlap alone.
    """
    check_kind = str(row.get("check_kind") or "").strip().upper()
    requirement = _norm(row.get("requirement") or "")
    rid = str(row.get("requirement_id") or "").upper()

    if check_kind == "STRUCTURE" or rid.startswith("PP87-CLAUSE-"):
        return "STRUCTURE"
    if check_kind in {"CALC", "TYPED_VALUE"}:
        return "TYPED_VALUE"
    if check_kind == "CROSS_SECTION":
        return "CROSS_SECTION"

    if "графическ" in requirement or "схема отображ" in requirement or "план земляных масс" in requirement:
        return "GRAPHIC_CONTENT"

    semantic_markers = (
        "обоснован", "обоснов", "соответств", "согласован", "обеспеч",
        "принципиальная схема", "решения по", "решений по", "доказ",
    )
    if any(marker in requirement for marker in semantic_markers):
        return "SEMANTIC_REQUIREMENT"

    set_markers = (
        "характеристики и технические показатели",
        "перечень", "состав", "комплекс", "включая", "а также",
    )
    if any(marker in requirement for marker in set_markers):
        return "SET_COMPLETENESS"

    presence_markers = (
        "должна быть приведена", "должны быть приведены сведения", "должно быть приведено описание",
        "должны быть описаны", "должно содержаться", "должна содержаться",
    )
    if any(marker in requirement for marker in presence_markers):
        return "PRESENCE"

    return "SEMANTIC_REQUIREMENT"


def _semantic_evidence(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Return up to four addressable retrieval candidates for semantic proof."""
    rid = str(row.get("requirement_id") or "")
    source = list(row.get("evidence_candidates") or [])
    if not source and row.get("evidence_document") and row.get("evidence_page") not in (None, ""):
        source = [{
            "evidence_id": row.get("evidence_id") or f"NORM-E-{rid}-01",
            "document": row.get("evidence_document"),
            "page": row.get("evidence_page"),
            "section": (row.get("sections") or [""])[0] if row.get("sections") else "",
            "fragment": row.get("evidence_fragment"),
            "matched_keywords": row.get("matched_keywords") or [],
            "retrieval_keyword_score": row.get("retrieval_keyword_score") or 0,
            "retrieval_keyword_coverage": row.get("retrieval_keyword_coverage") or 0,
        }]

    output=[]
    seen=set()
    for index,candidate in enumerate(source[:4],1):
        document=str(candidate.get("document") or candidate.get("evidence_document") or "").strip()
        page=candidate.get("page") if candidate.get("page") not in (None,"") else candidate.get("evidence_page")
        fragment=str(candidate.get("fragment") or candidate.get("evidence_fragment") or "").strip()
        if not document or page in (None,"") or not fragment:
            continue
        key=(document,str(page),fragment[:240])
        if key in seen:
            continue
        seen.add(key)
        evidence_id=str(candidate.get("evidence_id") or f"NORM-E-{rid}-{index:02d}")
        output.append({
            "evidence_id":evidence_id,
            "document":document,
            "page":page,
            "section":str(candidate.get("section") or ((row.get("sections") or [""])[0] if row.get("sections") else "")),
            "text":fragment[:1200],
            "source_locator":f"{document}, стр. {page}",
            "matched_keywords":list(candidate.get("matched_keywords") or []),
            "retrieval_keyword_score":candidate.get("retrieval_keyword_score") or 0,
            "retrieval_keyword_coverage":candidate.get("retrieval_keyword_coverage") or 0,
        })
    return output


def _semantic_packet(row: dict[str, Any], proof_type: str) -> dict[str, Any] | None:
    evidence=_semantic_evidence(row)
    if not evidence:
        return None
    rid = str(row.get("requirement_id") or "")
    return {
        "packet_id": f"NORM-{rid}",
        "requirement_id": rid,
        "proof_type": proof_type,
        "source": row.get("source") or row.get("document_id") or "",
        "paragraph": row.get("paragraph") or "",
        "topic": row.get("topic") or "",
        "requirement": row.get("requirement") or "",
        "sections": list(row.get("sections") or []),
        "evidence": evidence,
        "policy": (
            "Retrieval is not proof. VERIFIED_OK requires a proof contract appropriate to proof_type. "
            "Judge must cite addressable evidence that proves the whole verified requirement; absence of proof is never a normative PROJECT_FINDING."
        ),
    }


def proof_frontier_summary(
    rows: list[dict[str, Any]] | None,
    *,
    pending_requirement_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Summarise the current unresolved proof frontier without changing verdicts."""
    pending_ids = {str(value) for value in (pending_requirement_ids or set()) if str(value)}
    blockers: Counter[str] = Counter()
    semantic_sources: Counter[str] = Counter()
    semantic_sections: Counter[str] = Counter()
    semantic_evidence_buckets: Counter[str] = Counter()
    retained_reasons: Counter[str] = Counter()
    retained_sources: Counter[str] = Counter()
    retained_sections: Counter[str] = Counter()
    semantic_rows: list[dict[str, Any]] = []
    retained_rows: list[dict[str, Any]] = []
    held_total = 0
    unresolved_total = 0

    def _scope(row: dict[str, Any]) -> str:
        sections = [str(value).strip() for value in row.get("sections") or [] if str(value).strip()]
        return ", ".join(dict.fromkeys(sections)) or "Без раздела"

    def _source(row: dict[str, Any]) -> str:
        return str(row.get("source") or row.get("document_id") or "Без НТД").strip() or "Без НТД"

    def _evidence_bucket(row: dict[str, Any]) -> str:
        count = int(row.get("retrieval_candidate_count") or len(row.get("evidence_candidates") or []))
        if count <= 0:
            return "0"
        if count == 1:
            return "1"
        if count == 2:
            return "2"
        if count == 3:
            return "3"
        return "4+"

    for row in (rows or []):
        if not isinstance(row, dict):
            continue
        current_kind = str(row.get("kind") or "").upper()
        retrieval_kind = str(row.get("retrieval_kind") or "").upper()
        proof_state = str(row.get("proof_state") or "").upper()
        requirement_id = str(row.get("requirement_id") or "")

        if retrieval_kind == "VERIFIED_OK" and current_kind != "VERIFIED_OK":
            held_total += 1
        if current_kind == "VERIFIED_OK":
            continue

        unresolved_total += 1
        if proof_state == "SEMANTIC_PROOF_REQUIRED":
            if requirement_id in pending_ids or not row.get("semantic_proof"):
                blockers["SEMANTIC_PENDING"] += 1
                source = _source(row)
                scope = _scope(row)
                bucket = _evidence_bucket(row)
                semantic_sources[source] += 1
                semantic_sections[scope] += 1
                semantic_evidence_buckets[bucket] += 1
                semantic_rows.append({
                    "requirement_id": requirement_id,
                    "source": source,
                    "paragraph": str(row.get("paragraph") or ""),
                    "sections": scope,
                    "topic": str(row.get("topic") or ""),
                    "retrieval_candidate_count": int(
                        row.get("retrieval_candidate_count")
                        or len(row.get("evidence_candidates") or [])
                    ),
                })
            else:
                blockers["SEMANTIC_REVIEWED_NO_PROMOTION"] += 1
        elif proof_state == "SET_PROOF_CONTRACT_REQUIRED":
            blockers["SET_COMPLETENESS_REQUIRED"] += 1
        elif proof_state == "STRUCTURED_PROOF_REQUIRED":
            blockers["STRUCTURED_PROOF_REQUIRED"] += 1
        elif proof_state == "VISUAL_PROOF_REQUIRED":
            blockers["VISUAL_PROOF_REQUIRED"] += 1
        elif proof_state == "PRESENCE_PROOF_NOT_ADDRESSABLE":
            blockers["PRESENCE_NOT_ADDRESSABLE"] += 1
        elif proof_state == "RETAINED_FAIL_CLOSED":
            blockers["RETAINED_FAIL_CLOSED"] += 1
            reason_code = str(row.get("reason_code") or "UNSPECIFIED")
            source = _source(row)
            scope = _scope(row)
            retained_reasons[reason_code] += 1
            retained_sources[source] += 1
            retained_sections[scope] += 1
            retained_rows.append({
                "requirement_id": requirement_id,
                "reason_code": reason_code,
                "source": source,
                "paragraph": str(row.get("paragraph") or ""),
                "sections": scope,
                "topic": str(row.get("topic") or ""),
                "retrieval_candidate_count": int(
                    row.get("retrieval_candidate_count")
                    or len(row.get("evidence_candidates") or [])
                ),
                "near_misses": [
                    dict(item) for item in (row.get("retrieval_near_misses") or [])
                    if isinstance(item,dict)
                ],
                "reason": str(row.get("reason") or ""),
            })
        else:
            blockers["OTHER_UNRESOLVED"] += 1

    return {
        "held_total": held_total,
        "unresolved_total": unresolved_total,
        "blocker_counts": dict(blockers),
        "semantic_pending": {
            "total": len(semantic_rows),
            "by_source": dict(semantic_sources),
            "by_section": dict(semantic_sections),
            "by_evidence_candidates": dict(semantic_evidence_buckets),
            "rows": semantic_rows,
        },
        "retained_fail_closed": {
            "total": len(retained_rows),
            "by_reason": dict(retained_reasons),
            "by_source": dict(retained_sources),
            "by_section": dict(retained_sections),
            "rows": retained_rows,
        },
    }


def _apply_gate(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    proof_type = _proof_type(result)
    result["proof_type"] = proof_type
    result["retrieval_kind"] = str(result.get("kind") or "")
    result["retrieval_state"] = str(result.get("state") or "")
    result["retrieval_reason_code"] = str(result.get("reason_code") or "")
    result["proof_engine_version"] = ENGINE_VERSION

    retrieval_kind = str(result.get("kind") or "").upper()
    retrieval_reason = str(result.get("reason_code") or "").upper()

    graphic_text_retrieval_reasons = {
        "NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
        "NORMATIVE_EVIDENCE_WEAK",
        "NORMATIVE_SECTION_EVIDENCE_MISSING",
        "NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED",
        "NORMATIVE_STRONG_NEAR_MISS_CANDIDATE",
    }
    if (
        proof_type == "GRAPHIC_CONTENT"
        and (
            retrieval_kind == "VERIFIED_OK"
            or retrieval_reason in graphic_text_retrieval_reasons
        )
    ):
        result["kind"] = "SYSTEM_LIMITATION"
        result["state"] = "Не проверено системой"
        result["proof_state"] = "VISUAL_PROOF_REQUIRED"
        result["reason_code"] = "NORMATIVE_VISUAL_PROOF_REQUIRED"
        result["reason"] = (
            "Требование относится к графической части. Текстовый retrieval не является доказательством "
            "содержания чертежа; требование направлено в отдельный визуальный proof-контракт."
        )
        return result

    recoverable_retrieval = (
        retrieval_reason in {
            "NORMATIVE_EVIDENCE_WEAK",
            "NORMATIVE_STRONG_NEAR_MISS_CANDIDATE",
        }
        and bool(result.get("evidence_candidates"))
    )
    if retrieval_kind != "VERIFIED_OK" and not recoverable_retrieval:
        result["proof_state"] = "RETAINED_FAIL_CLOSED"
        return result

    if recoverable_retrieval:
        result["kind"] = "REVIEW_QUESTION"
        result["state"] = "Вопрос специалисту"
        result["proof_state"] = "SEMANTIC_PROOF_REQUIRED"
        result["reason_code"] = "NORMATIVE_SEMANTIC_PROOF_REQUIRED"
        result["reason"] = (
            "Retrieval нашёл адресный, но недостаточно строгий лексический кандидат. "
            "Он не может подтвердить требование напрямую и допускается только к независимой смысловой проверке."
        )
        return result

    if proof_type == "STRUCTURE":
        result["proof_state"] = "DETERMINISTIC_STRUCTURE_PROOF"
        result["reason_code"] = result.get("reason_code") or "NORMATIVE_STRUCTURE_VERIFIED"
        return result

    if proof_type == "PRESENCE":
        if result.get("evidence_document") and result.get("evidence_page") not in (None, "") and result.get("evidence_fragment"):
            result["proof_state"] = "ADDRESSABLE_PRESENCE_PROOF"
            result["reason"] = (
                "Пункт НТД верифицирован; требование относится к положительному наличию сведений, "
                "и адресный фрагмент подтверждает наличие требуемого содержания."
            )
            result["reason_code"] = "NORMATIVE_PRESENCE_PROOF_CONFIRMED"
            return result
        result["kind"] = "REVIEW_QUESTION"
        result["state"] = "Вопрос специалисту"
        result["proof_state"] = "PRESENCE_PROOF_NOT_ADDRESSABLE"
        result["reason_code"] = "NORMATIVE_PRESENCE_PROOF_NOT_ADDRESSABLE"
        result["reason"] = "Лексический кандидат найден, но адресное доказательство наличия требования не сформировано."
        return result

    if proof_type == "SET_COMPLETENESS":
        result["kind"] = "REVIEW_QUESTION"
        result["state"] = "Вопрос специалисту"
        result["proof_state"] = "SET_PROOF_CONTRACT_REQUIRED"
        result["reason_code"] = "NORMATIVE_SET_COMPLETENESS_NOT_PROVEN"
        result["reason"] = (
            "Найден адресный кандидат, но требование содержит набор обязательных сведений. "
            "Пока набор не разложен на верифицированные обязательные элементы, совпадение ключевых слов не является доказательством полноты."
        )
        return result

    if proof_type in {"TYPED_VALUE", "CROSS_SECTION"}:
        result["kind"] = "REVIEW_QUESTION"
        result["state"] = "Вопрос специалисту"
        result["proof_state"] = "STRUCTURED_PROOF_REQUIRED"
        result["reason_code"] = "NORMATIVE_STRUCTURED_PROOF_REQUIRED"
        result["reason"] = (
            "Для этого требования нужен структурированный числовой или межраздельный контракт. "
            "Текстовое совпадение не используется как подтверждение."
        )
        return result

    result["kind"] = "REVIEW_QUESTION"
    result["state"] = "Вопрос специалисту"
    result["proof_state"] = "SEMANTIC_PROOF_REQUIRED"
    result["reason_code"] = "NORMATIVE_SEMANTIC_PROOF_REQUIRED"
    result["reason"] = (
        "Найдены адресные кандидаты evidence, но требование требует содержательного инженерного доказательства. "
        "Ключевые слова подтверждают только retrieval; до независимого semantic proof автоматическое VERIFIED_OK запрещено."
    )
    return result


class NormativeProofEngine20:
    """Turn retrieval results into proof-appropriate verdicts.

    Precision has priority over recall: lexical evidence may be demoted when its
    proof type requires semantic, graphical, typed or cross-section verification.
    """

    def run(self, rows: list[dict[str, Any]] | None) -> dict[str, Any]:
        source = [dict(row) for row in (rows or []) if isinstance(row, dict)]
        gated = [_apply_gate(row) for row in source]
        raw_verified = sum(str(row.get("kind") or "").upper() == "VERIFIED_OK" for row in source)
        verified = sum(str(row.get("kind") or "").upper() == "VERIFIED_OK" for row in gated)
        questions = sum(str(row.get("kind") or "").upper() == "REVIEW_QUESTION" for row in gated)
        limitations = sum(str(row.get("kind") or "").upper() == "SYSTEM_LIMITATION" for row in gated)
        findings = sum(str(row.get("kind") or "").upper() == "PROJECT_FINDING" for row in gated)
        proof_types = Counter(str(row.get("proof_type") or "") for row in gated)
        semantic_queue = [
            packet for row in gated
            if row.get("proof_state") == "SEMANTIC_PROOF_REQUIRED"
            for packet in [_semantic_packet(row, str(row.get("proof_type") or "SEMANTIC_REQUIREMENT"))]
            if packet is not None
        ]
        set_queue = [
            packet for row in gated
            if row.get("proof_state") == "SET_PROOF_CONTRACT_REQUIRED"
            for packet in [_semantic_packet(row, str(row.get("proof_type") or "SET_COMPLETENESS"))]
            if packet is not None
        ]
        initial_demoted = max(0, raw_verified - verified)
        frontier = proof_frontier_summary(
            gated,
            pending_requirement_ids={
                str(packet.get("requirement_id") or "")
                for packet in semantic_queue
                if str(packet.get("requirement_id") or "")
            },
        )
        return {
            "version": ENGINE_VERSION,
            "rows": gated,
            "contracts": len(gated),
            "retrieval_verified_ok": raw_verified,
            "verified_ok": verified,
            "review_questions": questions,
            "system_limitations": limitations,
            "project_findings": findings,
            "demoted_keyword_only": initial_demoted,
            "demoted_keyword_only_initial": initial_demoted,
            "demoted_keyword_only_remaining": frontier["held_total"],
            "proof_frontier": frontier,
            "proof_type_counts": {key: proof_types.get(key, 0) for key in PROOF_TYPES},
            "semantic_queue": semantic_queue,
            "semantic_queue_total": len(semantic_queue),
            "semantic_queue_evidence": sum(len(packet.get("evidence") or []) for packet in semantic_queue),
            "set_completeness_queue": set_queue,
            "set_completeness_queue_total": len(set_queue),
            "principle": (
                "Retrieval is not proof: PRESENCE/STRUCTURE may be deterministic; SET/SEMANTIC/GRAPHIC/TYPED/CROSS_SECTION "
                "require their own proof contract. Missing proof never becomes a normative non-compliance."
            ),
        }
