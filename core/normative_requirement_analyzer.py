from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .normalization import normalize_text
from .normative_validity import NormativeValidityChecker

MODAL_TOKENS=("должен","должна","должны","следует","необходимо","не допускается","запрещается","требуется","обеспечить","предусмотреть","предусматривается","в соответствии","согласно")
CLAUSE_TOKEN=r"(?:п\.|пункт(?:а|е|ом)?|ч\.|част[ьи]|ст\.|статья)\s*([0-9]+(?:\.[0-9]+){0,5})"


def _context_window(text:str,ref:str,radius:int=420)->str:
    raw=str(text or "")
    low=normalize_text(raw); q=normalize_text(ref); pos=low.find(q)
    if pos<0:return re.sub(r"\s+"," ",raw)[:900]
    # Keep line boundaries first; periods inside SP/GOST numbers are not sentence boundaries.
    before=raw.rfind("\n",0,pos); after=raw.find("\n",pos)
    left=max(0,before if before>=0 else pos-radius); right=min(len(raw),after if after>=0 else pos+radius)
    line=raw[left:right]
    if len(line.strip())<40:
        line=raw[max(0,pos-radius):min(len(raw),pos+len(ref)+radius)]
    return re.sub(r"\s+"," ",line).strip()[:1200]


def _extract_cited_clause(text:str,ref:str)->str:
    """Return a clause only when grammar explicitly binds it to this reference."""
    raw=re.sub(r"\s+"," ",str(text or ""))
    ref_esc=re.escape(re.sub(r"\s+"," ",str(ref or "")).strip())
    patterns=[
        re.compile(rf"{CLAUSE_TOKEN}\s*(?:[,;:]\s*)?(?:{ref_esc})",re.I),
        re.compile(rf"(?:{ref_esc})\s*[,;:]?\s*{CLAUSE_TOKEN}",re.I),
    ]
    for pat in patterns:
        m=pat.search(raw)
        if m:return str(m.group(1) or "")
    return ""


def _requirement_modality(text:str)->str:
    low=normalize_text(text)
    if "не допускается" in low or "запрещается" in low:return "Запрет"
    if any(x in low for x in ("должен","должна","должны","необходимо","требуется")):return "Обязательное требование"
    if "следует" in low:return "Предписывающее требование"
    if any(x in low for x in ("обеспечить","предусмотреть","предусматривается")):return "Проектное требование"
    if "согласно" in low or "в соответствии" in low:return "Ссылка для проверки применимости"
    return "Ссылка на НТД"


class NormativeRequirementAnalyzer:
    """Strict requirement-level layer above project reference audit.

    A citation is not a requirement. A requirement row is emitted only when a
    curated machine-readable clause exists, or the project explicitly couples a
    clause number with the cited document. This prevents bibliographies from being
    misreported as hundreds of unverified requirements.
    """
    def __init__(self,knowledge_root:str|Path):
        self.root=Path(knowledge_root); self.validity=NormativeValidityChecker(self.root)
        import json
        self.requirements=[]
        for name in ("normative_requirements_v3.json","normative_requirements_v2.json"):
            try:
                data=json.loads((self.root/name).read_text(encoding="utf-8"))
                if isinstance(data,list):self.requirements=data;break
            except Exception:pass

    def _curated_match(self,reference:str,clause:str,context:str)->dict[str,Any]|None:
        ref=normalize_text(reference); clause_n=normalize_text(clause); ctx=normalize_text(context);ranked=[]
        for req in self.requirements:
            source=normalize_text(req.get("source") or "");paragraph=normalize_text(req.get("paragraph") or "")
            if source and not (source in ref or ref in source):continue
            score=5
            if clause_n and paragraph:
                if clause_n==paragraph:score+=12
                elif clause_n in paragraph or paragraph in clause_n:score+=6
                else:continue
            elif paragraph:
                # Do not bind a concrete curated clause to a citation without a cited clause.
                continue
            score+=sum(1 for kw in req.get("keywords") or [] if normalize_text(kw) in ctx)
            if score>5:ranked.append((score,req))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return dict(ranked[0][1]) if ranked else None

    def analyze_page(self,document:str,page:int,text:str)->list[dict[str,Any]]:
        refs=self.validity.extract_from_text(text);rows=[]
        for ref in refs:
            context=_context_window(text,ref);clause=_extract_cited_clause(text,ref);curated=self._curated_match(ref,clause,context)
            # Pure bibliography/reference-list mentions belong only to Reference Audit.
            meaningful=bool(curated or clause or any(tok in normalize_text(context) for tok in MODAL_TOKENS))
            if not meaningful:continue
            validity=self.validity.check(ref,document=document,page=page,context=context)
            if curated:
                requirement_text=str(curated.get("requirement") or "")
                analysis_status="Структурированное требование доступно" if requirement_text else "Требуется верификация требования"
                requirement_id=curated.get("id") or ""
                check_kind=curated.get("check_kind") or "SEMANTIC"
                quality="VERIFIED_CLAUSE" if clause and curated.get("paragraph") else "CURATED_PRELIMINARY"
            else:
                requirement_text=""; requirement_id="";check_kind="REFERENCE_CONTEXT";quality="CLAUSE_NOT_IN_KB" if clause else "REFERENCE_ONLY"
                analysis_status="Конкретный пункт не загружен в базу — требуется верификация требования НТД" if clause else "Ссылка требует проверки применимости"
            rows.append({
              "document":document,"page":page,"reference":ref,"clause":clause,
              "project_context":context,"modality":_requirement_modality(context),
              "normative_status":validity.get("status"),"edition_status":(validity.get("edition_assessment") or {}).get("edition_status",""),
              "curated_requirement":requirement_text,"requirement_id":requirement_id,"check_kind":check_kind,
              "requirement_quality":quality,"analysis_status":analysis_status,
              "verification_priority":validity.get("verification_priority",""),"impact_risk":validity.get("impact_risk",""),
              "guardrail":"Ссылка на НТД не считается проверенным требованием без конкретного текста/пункта из верифицированной базы."
            })
        return rows

    def audit_uploaded_pdfs(self,files,reader,limit:int=1200)->list[dict[str,Any]]:
        out=[];seen=set()
        for uploaded in files or []:
            name=str(getattr(uploaded,"name","document.pdf"))
            try:pages=reader(uploaded.getvalue(),name)
            except Exception:continue
            for page,text in pages:
                for row in self.analyze_page(name,page,text):
                    key=(normalize_text(row.get("reference")),row.get("clause"),normalize_text(row.get("project_context")))
                    if key in seen:continue
                    seen.add(key);out.append(row)
                    if len(out)>=limit:return out
        return out
