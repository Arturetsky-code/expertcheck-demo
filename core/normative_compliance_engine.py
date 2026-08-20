from __future__ import annotations

from pathlib import Path
from typing import Any

from .normalization import normalize_text
from .normative_intelligence import NormativeIntelligence
from .normative_requirement_quality import requirement_quality


def _evidence_candidates(req:dict[str,Any], findings:list[dict[str,Any]], limit:int=8)->list[dict[str,Any]]:
    keywords=[normalize_text(x) for x in req.get("keywords") or [] if x]
    sections=[normalize_text(x) for x in req.get("sections") or [] if x and normalize_text(x)!="all"]
    ranked=[]
    for f in findings or []:
        section=normalize_text(f.get("document_type") or f.get("section_family") or "")
        if sections and section and not any(s in section or section in s for s in sections):
            continue
        blob=" ".join(str(f.get(k) or "") for k in ("context","section_title","table_title","table_evidence","parameter_name","value_text","object_hint","semantic_anchor_name"))
        low=normalize_text(blob)
        hits=[kw for kw in keywords if kw and kw in low]
        if not hits: continue
        score=len(hits)*4
        if f.get("page") not in (None,""):score+=1
        if f.get("evidence_id") or f.get("source_fingerprint"):score+=2
        if str(f.get("fact_admission_decision") or "").upper()=="ADMIT":score+=3
        ranked.append((score,f,hits))
    ranked.sort(key=lambda x:x[0],reverse=True)
    out=[]
    for score,f,hits in ranked[:limit]:
        out.append({
            "score":score,"evidence_id":f.get("evidence_id"),"document":f.get("document"),"page":f.get("page"),
            "object":f.get("semantic_anchor_name") or f.get("object_hint") or "","parameter":f.get("parameter_name") or "",
            "value":f.get("value_text") or f.get("value"),"context":str(f.get("context") or f.get("table_evidence") or "")[:550],
            "matched_terms":hits,
        })
    return out


class NormativeComplianceEngine:
    """Typed compliance layer over the curated normative KB.

    The engine deliberately separates knowledge coverage from project compliance:
    missing clause text is a KB limitation, not a project non-compliance.
    """
    def __init__(self, knowledge_root:str|Path):
        self.knowledge=NormativeIntelligence(knowledge_root)

    def review(self, findings:list[dict[str,Any]], *, project_type:str="", limit:int=500)->list[dict[str,Any]]:
        rows=[]
        for req in self.knowledge.requirements[:limit]:
            doc=self.knowledge.docs.get(str(req.get("document_id") or ""))
            quality=requirement_quality(req,doc)
            evidence=_evidence_candidates(req,findings,limit=8)
            check_kind=str(req.get("check_kind") or "SEMANTIC").upper()
            verified_clause=bool(quality.get("verified_clause"))
            categorical=quality.get("conclusion_mode")=="CATEGORICAL_ALLOWED"
            if not verified_clause:
                status="Нормативное требование требует верификации"
                basis="В базе есть правило маршрутизации, но отсутствует верифицированный пункт/текст нормы. Вывод о соответствии проекта запрещён."
            elif not evidence:
                status="Не проверено автоматически"
                basis="Верифицированное требование доступно, но проектные доказательства не найдены специализированным алгоритмом. Отсутствие находки не считается нарушением."
            elif check_kind in {"PRESENCE","STRUCTURE","DOCUMENT","DRAWING"}:
                status="Требует проверки"
                basis="Найдены кандидаты доказательств. Для подтверждения требуется специализированная структурная проверка соответствующего типа."
            else:
                status="Требует смысловой проверки"
                basis="Найдены релевантные доказательства; требуется сопоставление условия нормы и проектного решения."
            rows.append({
                "requirement_id":req.get("id"),"source":req.get("source"),"paragraph":req.get("paragraph") or "",
                "topic":req.get("topic") or "","requirement":req.get("requirement") or "","check_kind":check_kind,
                "verification_status":req.get("verification_status") or req.get("status") or "",
                "verified_clause":verified_clause,"categorical_conclusion_allowed":categorical,
                "status":status,"decision_basis":basis,"evidence":evidence,
                "evidence_count":len(evidence),"ai_review_ready":bool(verified_clause and evidence),
                "guardrail":"AI может интерпретировать только переданный текст требования; без верифицированного пункта нормативное нарушение не формируется.",
            })
        return rows

    @staticmethod
    def summary(rows:list[dict[str,Any]])->dict[str,int]:
        return {
            "requirements":len(rows),
            "verified_clause":sum(1 for x in rows if x.get("verified_clause")),
            "ai_review_ready":sum(1 for x in rows if x.get("ai_review_ready")),
            "requires_kb_verification":sum(1 for x in rows if x.get("status")=="Нормативное требование требует верификации"),
            "project_review":sum(1 for x in rows if x.get("status") in {"Требует проверки","Требует смысловой проверки"}),
        }
