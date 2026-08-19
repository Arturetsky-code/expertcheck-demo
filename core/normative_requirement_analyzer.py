
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from .normalization import normalize_text
from .normative_validity import NormativeValidityChecker

CLAUSE_RE=re.compile(r"\b(?:п\.|пункт(?:а|е|ом)?|ч\.|част[ьи]|ст\.|статья)\s*([0-9]+(?:\.[0-9]+){0,4})",re.I)
MODAL_TOKENS=("должен","должна","должны","следует","необходимо","не допускается","запрещается","требуется","обеспечить","предусмотреть","предусматривается")

def _sentence_context(text:str,ref:str)->str:
    clean=re.sub(r"\s+"," ",str(text or "")).strip()
    if not clean:return ""
    pos=normalize_text(clean).find(normalize_text(ref))
    if pos<0:return clean[:1000]
    left=max(0,clean.rfind(".",0,pos)+1)
    right=clean.find(".",pos)
    if right<0:right=min(len(clean),pos+1000)
    return clean[left:right+1].strip()[:1400]

def _requirement_modality(text:str)->str:
    low=normalize_text(text)
    if "не допускается" in low or "запрещается" in low:return "Запрет"
    if any(x in low for x in ("должен","должна","должны","необходимо","требуется")):return "Обязательное требование"
    if "следует" in low:return "Предписывающее требование"
    if any(x in low for x in ("обеспечить","предусмотреть","предусматривается")):return "Проектное требование"
    return "Ссылка на НТД"

class NormativeRequirementAnalyzer:
    """Requirement-level layer above validity checking.

    The analyzer extracts the cited clause/context and may link it to a curated
    machine-readable requirement. It never invents the text of an unseen clause.
    """
    def __init__(self,knowledge_root:str|Path):
        self.root=Path(knowledge_root)
        self.validity=NormativeValidityChecker(self.root)
        try:
            import json
            data=json.loads((self.root/"normative_requirements_v2.json").read_text(encoding="utf-8"))
            self.requirements=data if isinstance(data,list) else []
        except Exception:self.requirements=[]

    def _curated_match(self,reference:str,clause:str,context:str)->dict[str,Any]|None:
        ref=normalize_text(reference); clause=normalize_text(clause); ctx=normalize_text(context)
        ranked=[]
        for req in self.requirements:
            source=normalize_text(req.get("source") or "")
            paragraph=normalize_text(req.get("paragraph") or "")
            if source and not (source in ref or ref in source):continue
            score=5
            if clause and paragraph and (clause==paragraph or clause in paragraph or paragraph in clause):score+=8
            score+=sum(1 for kw in req.get("keywords") or [] if normalize_text(kw) in ctx)
            if score>5:ranked.append((score,req))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return dict(ranked[0][1]) if ranked else None

    def analyze_page(self,document:str,page:int,text:str)->list[dict[str,Any]]:
        refs=self.validity.extract_from_text(text)
        rows=[]
        for ref in refs:
            context=_sentence_context(text,ref)
            full=str(text or "")
            norm_full=normalize_text(full); norm_ref=normalize_text(ref)
            pos=norm_full.find(norm_ref)
            clause_window=full[max(0,pos-120):min(len(full),pos+len(ref)+300)] if pos>=0 else context
            clauses=[m.group(1) for m in CLAUSE_RE.finditer(clause_window)]
            clause=clauses[0] if clauses else ""
            curated=self._curated_match(ref,clause,context)
            validity=self.validity.check(ref,document=document,page=page,context=context)
            if curated:
                requirement_text=str(curated.get("requirement") or "")
                requirement_status=str(curated.get("legal_confidence") or curated.get("verification_status") or "")
                analysis_status="Можно проверять по структурированному требованию" if requirement_text else "Требует верификации требования"
            else:
                requirement_text=""
                requirement_status="Требование НТД не загружено в структурированную базу"
                analysis_status="Требуется верификация требования НТД"
            rows.append({
              "document":document,"page":page,"reference":ref,"clause":clause,
              "project_context":context,"modality":_requirement_modality(context),
              "normative_status":validity.get("status"),
              "edition_status":(validity.get("edition_assessment") or {}).get("edition_status",""),
              "curated_requirement":requirement_text,
              "requirement_status":requirement_status,
              "analysis_status":analysis_status,
              "verification_priority":validity.get("verification_priority",""),
              "impact_risk":validity.get("impact_risk",""),
              "guardrail":"Без официально загруженного текста пункта ExpertCheck не формирует вывод о соответствии самому требованию."
            })
        return rows

    def audit_uploaded_pdfs(self,files,reader,limit:int=2000)->list[dict[str,Any]]:
        out=[]
        for uploaded in files or []:
            name=str(getattr(uploaded,"name","document.pdf"))
            try:pages=reader(uploaded.getvalue(),name)
            except Exception:continue
            for page,text in pages:
                out.extend(self.analyze_page(name,page,text))
                if len(out)>=limit:return out[:limit]
        return out
