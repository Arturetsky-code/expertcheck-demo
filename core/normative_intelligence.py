
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code

class NormativeIntelligence:
    """Evidence-first normative retrieval and applicability engine.

    It never turns an unverified reference into a categorical legal conclusion.
    """
    def __init__(self, knowledge_root: str|Path):
        root=Path(knowledge_root)
        self.requirements=self._load(root/"normative_requirements_v2.json")
        if not self.requirements:
            self.requirements=self._load(root/"normative_requirements_v1.json")
        self.documents=self._load(root/"normative_documents_registry.json")
        self.docs={str(x.get("document_id")):x for x in self.documents}

    @staticmethod
    def _load(path:Path):
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data,list) else []
        except Exception:
            return []

    def applicability(self, req:dict[str,Any], context:dict[str,Any]) -> tuple[bool,float,list[str]]:
        score=0.0; why=[]
        obj=normalize_text(context.get("object_type") or "")
        section=normalize_text(context.get("section") or "")
        project=normalize_text(context.get("project_type") or "")
        text=normalize_text(context.get("text") or context.get("question") or "")
        app=req.get("applicability") or {}
        object_types=[normalize_text(x) for x in app.get("object_types") or []]
        sections=[normalize_text(x) for x in req.get("sections") or []]
        project_types=[normalize_text(x) for x in app.get("project_types") or []]
        if object_types:
            if obj and any(x in obj or obj in x for x in object_types): score+=4; why.append("тип объекта")
            elif obj: return False,0,["тип объекта не соответствует"]
        if project_types:
            if project and any(x in project or project in x for x in project_types): score+=3; why.append("тип проекта")
            elif project: return False,0,["тип проекта не соответствует"]
        if sections and section and any(x in section or section in x for x in sections):
            score+=2; why.append("раздел ПД")
        for kw in req.get("keywords") or []:
            if normalize_text(kw) in text: score+=1
        return True,min(1.0,score/8.0),why

    def search(self, *, question:str="", parameter_codes=None, section:str="", object_type:str="", project_type:str="", limit:int=8):
        codes={canonical_parameter_code(x) for x in (parameter_codes or []) if x}
        context={"question":question,"text":question,"section":section,"object_type":object_type,"project_type":project_type}
        ranked=[]
        for req in self.requirements:
            applicable,app_score,why=self.applicability(req,context)
            if not applicable: continue
            score=app_score*5
            req_codes={canonical_parameter_code(x) for x in req.get("parameter_codes") or []}
            if codes and codes.intersection(req_codes): score+=7
            low=normalize_text(question)
            score+=sum(1 for kw in req.get("keywords") or [] if normalize_text(kw) in low)
            if score:
                item=dict(req)
                item["applicability_score"]=round(app_score,2)
                item["applicability_basis"]=why
                item["legal_confidence"]=self.legal_confidence(item)
                ranked.append((score,item))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return [x[1] for x in ranked[:limit]]

    def legal_confidence(self, req:dict[str,Any]) -> str:
        status=normalize_text(req.get("verification_status") or req.get("status") or "")
        paragraph=str(req.get("paragraph") or "").strip()
        source=str(req.get("source") or "").strip()
        if "верифиц" in status and "невериф" not in status and paragraph and source:
            return "Верифицированное нормативное основание"
        if paragraph and source:
            return "Предварительное нормативное основание"
        return "Требует верификации НТД"

    def evidence_chain(self, req:dict[str,Any], project_evidence:list[dict[str,Any]]|None=None) -> dict[str,Any]:
        evidence=project_evidence or []
        return {
            "source":req.get("source"),
            "paragraph":req.get("paragraph"),
            "requirement":req.get("requirement"),
            "applicability":req.get("applicability") or {},
            "project_evidence":evidence,
            "evidence_count":len(evidence),
            "conclusion_policy":"Не формировать категоричный вывод без верифицированного НТД и достаточных проектных доказательств.",
            "legal_confidence":self.legal_confidence(req),
        }

    def summary(self):
        verified=sum(1 for x in self.requirements if self.legal_confidence(x)=="Верифицированное нормативное основание")
        return {"documents":len(self.documents),"requirements":len(self.requirements),"verified_requirements":verified}
