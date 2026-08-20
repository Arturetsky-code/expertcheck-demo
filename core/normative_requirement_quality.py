from __future__ import annotations
from typing import Any

VERIFIED_DOCUMENT_STATUSES = {"Действует", "Действует с изменениями", "Заменён", "Утратил силу"}


def requirement_quality(requirement: dict[str, Any], document_record: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assess whether a normative requirement may support a categorical conclusion.

    A rule can be useful for routing/checking even when it is not clause-verified,
    but ExpertCheck must not present it as a proven normative violation until the
    canonical document, edition and clause are all curated.
    """
    document_id = str(requirement.get("document_id") or "").strip()
    clause = str(requirement.get("paragraph") or requirement.get("clause") or "").strip()
    req_status = str(requirement.get("verification_status") or requirement.get("status") or "").strip()
    doc_status = str((document_record or {}).get("status") or "").strip()
    verified_doc = bool(document_id and document_record and doc_status in VERIFIED_DOCUMENT_STATUSES)
    explicit_clause_verified = bool(requirement.get('clause_verified') or requirement.get('verified_clause_text') or str(requirement.get('verification_status') or '').strip().lower() in {'верифицировано','verified','пункт верифицирован'})
    verified_clause = bool(clause and verified_doc and explicit_clause_verified)
    policy = str(requirement.get("conclusion_policy") or "PRELIMINARY_ONLY").upper()

    if verified_clause and policy in {"CATEGORICAL_ALLOWED", "VERIFIED_ONLY"}:
        conclusion = "CATEGORICAL_ALLOWED"
        level = "A"
    elif verified_doc:
        conclusion = "PRELIMINARY_ONLY"
        level = "B" if clause else "C"
    else:
        conclusion = "ROUTING_ONLY"
        level = "D"

    debt = []
    if not document_id: debt.append("Не задан canonical document_id")
    if document_id and not document_record: debt.append("Документ отсутствует в реестре статусов")
    if document_record and doc_status not in VERIFIED_DOCUMENT_STATUSES: debt.append("Статус/редакция документа не верифицированы")
    if not clause: debt.append("Не верифицирован конкретный пункт/статья")
    if policy == "PRELIMINARY_ONLY": debt.append("Политика правила запрещает категоричный вывод")
    return {
        "quality_level": level,
        "verified_document": verified_doc,
        "verified_clause": verified_clause,
        "conclusion_mode": conclusion,
        "verification_debt": debt,
        "requirement_verification_status": req_status,
        "document_status": doc_status,
    }
