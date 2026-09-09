from __future__ import annotations

import re
from typing import Any

from .normative_foundation import NormativeKnowledgeFoundation20, _section_key, default_foundation


ENGINE_VERSION="20.0-alpha8-normative-execution"
KIND_LABELS={
    "VERIFIED_OK":"Подтверждено",
    "PROJECT_FINDING":"Выявлено несоответствие",
    "REVIEW_QUESTION":"Вопрос специалисту",
    "SYSTEM_LIMITATION":"Не проверено системой",
}


def _norm(value:Any)->str:
    return " ".join(str(value or "").replace("ё","е").casefold().replace("\xa0"," ").split())


def _page_section(page:dict[str,Any])->str:
    return _section_key(page.get("document_type") or page.get("section") or page.get("document") or "")


def _keywords(contract:dict[str,Any])->list[str]:
    raw=[_norm(x) for x in (contract.get("keywords") or []) if _norm(x)]
    if raw:
        return raw
    words=[
        w for w in re.findall(r"[a-zа-я0-9-]{5,}",_norm(contract.get("requirement") or ""))
        if w not in {"должна","должны","должен","раздел","части","объекта","проектной","документации"}
    ]
    return list(dict.fromkeys(words[:8]))


def _fragment(text:str, hits:list[str], radius:int=240)->str:
    low=_norm(text)
    pos=min((low.find(hit) for hit in hits if hit and low.find(hit)>=0),default=-1)
    if pos<0:
        return " ".join(str(text or "").split())[:700]
    raw=" ".join(str(text or "").split())
    # Normalized and raw offsets are close enough for a diagnostic excerpt; do
    # not use the excerpt position as a legal/addressing fact.
    start=max(0,pos-radius); end=min(len(raw),pos+radius)
    return raw[start:end][:700]


class NormativeExecutionEngine20:
    """Execute only curated, current, verified-clause contracts.

    Alpha 8 is intentionally positive-evidence-first. A missing text hit never
    becomes a PROJECT_FINDING. It becomes REVIEW_QUESTION or SYSTEM_LIMITATION.
    """

    def __init__(self, foundation:NormativeKnowledgeFoundation20|None=None):
        self.foundation=foundation or default_foundation()

    def run(self,documents:list[dict[str,Any]]|None,page_corpus:list[dict[str,Any]]|None)->dict[str,Any]:
        routes=self.foundation.project_routes(documents)
        pages=[dict(x) for x in (page_corpus or []) if isinstance(x,dict)]
        rows=[]
        for contract in routes.get("rows") or []:
            if not contract.get("project_relevant") or not contract.get("automatic_contract_ready"):
                continue
            rows.append(self._execute(contract,pages))
        counts={kind:sum(1 for row in rows if row.get("kind")==kind) for kind in KIND_LABELS}
        addressed=sum(1 for row in rows if row.get("evidence_document") and row.get("evidence_page") not in (None,""))
        return {
            "version":ENGINE_VERSION,
            "contracts":len(rows),
            "addressed":addressed,
            "counts":counts,
            "verified_ok":counts["VERIFIED_OK"],
            "project_findings":counts["PROJECT_FINDING"],
            "review_questions":counts["REVIEW_QUESTION"],
            "system_limitations":counts["SYSTEM_LIMITATION"],
            "evidence_coverage_pct":round(100.0*addressed/max(1,len(rows)),1),
            "rows":rows,
            "guardrail":"Ненайденный текст не является доказательством нарушения; отрицательный нормативный вывод без отдельного доказательного контракта запрещён.",
        }

    def _execute(self,contract:dict[str,Any],pages:list[dict[str,Any]])->dict[str,Any]:
        expected={_section_key(x) for x in (contract.get("sections") or []) if _section_key(x)}
        expected.discard("all")
        candidates=[
            p for p in pages
            if not expected or _page_section(p) in expected
        ]
        base={
            "requirement_id":contract.get("requirement_id") or "",
            "document_id":contract.get("document_id") or "",
            "source":contract.get("document_title") or "",
            "paragraph":contract.get("paragraph") or "",
            "topic":contract.get("topic") or "",
            "requirement":contract.get("requirement") or "",
            "sections":contract.get("sections") or [],
            "check_kind":contract.get("check_kind") or "",
            "trust_state":contract.get("trust_state") or "",
            "source_status":contract.get("source_status") or "",
            "history_occurrences":int(contract.get("expert_occurrences") or 0),
            "history_projects":int(contract.get("expert_project_count") or 0),
            "priority_score":int(contract.get("priority_score") or 0),
        }
        if not candidates:
            return {**base,"kind":"SYSTEM_LIMITATION","state":KIND_LABELS["SYSTEM_LIMITATION"],
                "reason":"Верифицированный пункт применим по маршруту, но в цифровом корпусе нет адресных страниц ожидаемого раздела.",
                "reason_code":"NORMATIVE_SECTION_EVIDENCE_MISSING",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        words=_keywords(contract)
        ec=dict(contract.get("evidence_contract") or {})
        minimum=max(1,int(ec.get("min_keyword_hits") or 2))
        ranked=[]
        for page in candidates:
            text=_norm(page.get("text") or page.get("content") or "")
            hits=[kw for kw in words if kw and kw in text]
            if hits:
                ranked.append((len(hits),len(text),page,hits))
        ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
        if not ranked:
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Пункт НТД и профильный раздел подтверждены, но адресное положительное доказательство выполнения требования не найдено. Отсутствие совпадения не трактуется как нарушение.",
                "reason_code":"NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        score,_,page,hits=ranked[0]
        evidence={
            "evidence_document":str(page.get("document") or ""),
            "evidence_page":page.get("page"),
            "evidence_fragment":_fragment(str(page.get("text") or page.get("content") or ""),hits),
            "matched_keywords":hits,
        }
        if score < minimum:
            return {**base,**evidence,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Найден адресный кандидат доказательства, но совпадение недостаточно сильное для автоматического подтверждения.",
                "reason_code":"NORMATIVE_EVIDENCE_WEAK"}

        return {**base,**evidence,"kind":"VERIFIED_OK","state":KIND_LABELS["VERIFIED_OK"],
            "reason":"Верифицированный пункт НТД, применимый раздел и адресное положительное evidence связаны единым исполняемым контрактом.",
            "reason_code":"NORMATIVE_POSITIVE_EVIDENCE_CONFIRMED"}
