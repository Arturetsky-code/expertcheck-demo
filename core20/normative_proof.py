from __future__ import annotations

from collections import Counter
from typing import Any


ENGINE_VERSION = "20.0-alpha9-normative-proof"

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

    Alpha 8 treated a strong lexical hit as positive evidence for every semantic
    clause. Alpha 9 separates retrieval from proof. The taxonomy is deliberately
    conservative: any requirement that asks to justify, substantiate, coordinate
    or demonstrate a multi-part engineering decision is never auto-confirmed by
    keywords alone.
    """
    check_kind = str(row.get("check_kind") or "").strip().upper()
    requirement = _norm(row.get("requirement") or "")
    topic = _norm(row.get("topic") or "")
    rid = str(row.get("requirement_id") or "").upper()

    if check_kind == "STRUCTURE" or rid.startswith("PP87-CLAUSE-"):
        return "STRUCTURE"
    if check_kind in {"CALC", "TYPED_VALUE"}:
        return "TYPED_VALUE"
    if check_kind == "CROSS_SECTION":
        return "CROSS_SECTION"

    # Text extraction is not proof of graphical content. Drawings require a
    # dedicated Drawing Intelligence / visual contract.
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

    # Direct positive-presence clauses: the normative obligation is satisfied by
    # an addressable statement/description itself, without a separate engineering
    # judgement about adequacy or consistency.
    presence_markers = (
        "должна быть приведена", "должны быть приведены сведения", "должно быть приведено описание",
        "должны быть описаны", "должно содержаться", "должна содержаться",
    )
    if any(marker in requirement for marker in presence_markers):
        return "PRESENCE"

    # Unknown semantic shapes fail closed instead of inheriting Alpha 8 keyword
    # confirmation.
    return "SEMANTIC_REQUIREMENT"


def _semantic_packet(row: dict[str, Any], proof_type: str) -> dict[str, Any] | None:
    document = str(row.get("evidence_document") or "").strip()
    page = row.get("evidence_page")
    fragment = str(row.get("evidence_fragment") or "").strip()
    if not document or page in (None, "") or not fragment:
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
        "evidence": [{
            "evidence_id": f"NORM-E-{rid}",
            "document": document,
            "page": page,
            "section": (row.get("sections") or [""])[0] if row.get("sections") else "",
            "text": fragment[:1200],
            "source_locator": f"{document}, стр. {page}",
            "matched_keywords": list(row.get("matched_keywords") or []),
        }],
        "policy": (
            "Retrieval is not proof. VERIFIED_OK requires a proof contract appropriate to proof_type. "
            "Absence of proof is never a normative PROJECT_FINDING."
        ),
    }


def _apply_gate(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    proof_type = _proof_type(result)
    result["proof_type"] = proof_type
    result["retrieval_kind"] = str(result.get("kind") or "")
    result["retrieval_state"] = str(result.get("state") or "")
    result["proof_engine_version"] = ENGINE_VERSION

    # Existing uncertainty remains uncertainty. Alpha 9 never upgrades a row
    # merely because a proof type was classified.
    if str(result.get("kind") or "").upper() != "VERIFIED_OK":
        result["proof_state"] = "RETAINED_FAIL_CLOSED"
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

    if proof_type == "GRAPHIC_CONTENT":
        result["kind"] = "SYSTEM_LIMITATION"
        result["state"] = "Не проверено системой"
        result["proof_state"] = "VISUAL_PROOF_REQUIRED"
        result["reason_code"] = "NORMATIVE_VISUAL_PROOF_REQUIRED"
        result["reason"] = (
            "Требование относится к графической части. Текстовый слой страницы не доказывает состав и содержание чертежа; "
            "до отдельного визуального контракта автоматическое подтверждение запрещено."
        )
        return result

    if proof_type == "SET_COMPLETENESS":
        result["kind"] = "REVIEW_QUESTION"
        result["state"] = "Вопрос специалисту"
        result["proof_state"] = "SET_PROOF_CONTRACT_REQUIRED"
        result["reason_code"] = "NORMATIVE_SET_COMPLETENESS_NOT_PROVEN"
        result["reason"] = (
            "Найден адресный кандидат, но требование содержит набор обязательных сведений. "
            "Пока набор не разложен на обязательные элементы, совпадение ключевых слов не является доказательством полноты."
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

    # The main Alpha 9 precision guard: engineering meaning must be judged, not
    # inferred from lexical overlap.
    result["kind"] = "REVIEW_QUESTION"
    result["state"] = "Вопрос специалисту"
    result["proof_state"] = "SEMANTIC_PROOF_REQUIRED"
    result["reason_code"] = "NORMATIVE_SEMANTIC_PROOF_REQUIRED"
    result["reason"] = (
        "Найден адресный кандидат evidence, но требование требует содержательного инженерного доказательства. "
        "Ключевые слова подтверждают только retrieval; до независимого semantic proof автоматическое VERIFIED_OK запрещено."
    )
    return result


class NormativeProofEngine20:
    """Turn Alpha 8 retrieval results into proof-appropriate verdicts.

    This engine deliberately improves precision before recall. It may demote an
    Alpha 8 VERIFIED_OK to REVIEW_QUESTION/SYSTEM_LIMITATION when the evidence
    proves only lexical relevance, not the actual normative obligation.
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
        return {
            "version": ENGINE_VERSION,
            "rows": gated,
            "contracts": len(gated),
            "retrieval_verified_ok": raw_verified,
            "verified_ok": verified,
            "review_questions": questions,
            "system_limitations": limitations,
            "project_findings": findings,
            "demoted_keyword_only": max(0, raw_verified - verified),
            "proof_type_counts": {key: proof_types.get(key, 0) for key in PROOF_TYPES},
            "semantic_queue": semantic_queue,
            "semantic_queue_total": len(semantic_queue),
            "set_completeness_queue": set_queue,
            "set_completeness_queue_total": len(set_queue),
            "principle": (
                "Retrieval is not proof: PRESENCE/STRUCTURE may be deterministic; SET/SEMANTIC/GRAPHIC/TYPED/CROSS_SECTION "
                "require their own proof contract. Missing proof never becomes a normative non-compliance."
            ),
        }
