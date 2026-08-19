
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any, Iterable
from .normalization import normalize_text

REF_PATTERNS=[
    re.compile(r"\bГОСТ(?:\s+Р)?\s+[A-Za-zА-Яа-я0-9.\-/]+",re.I),
    re.compile(r"\bСП\s+\d+(?:\.\d+){1,4}(?:-\d{4})?",re.I),
    re.compile(r"\bСНиП\s+[A-Za-zА-Яа-я0-9.\-*]+",re.I),
    re.compile(r"\bФедеральн(?:ый|ого)\s+закон(?:а)?(?:\s+от\s+\d{2}\.\d{2}\.\d{4})?\s+№\s*[\d\-ФЗфз]+",re.I),
    re.compile(r"\b(?:ФЗ|Федеральный закон)\s*№?\s*\d+\s*-\s*ФЗ\b",re.I),
    re.compile(r"\bПостановлен(?:ие|ия|ию|ии|ием)\s+(?:Правительства\s+(?:Российской Федерации|РФ)\s+)?(?:от\s+\d{2}\.\d{2}\.\d{4}\s+)?№\s*\d+",re.I),
    re.compile(r"\bПриказ(?:а)?\s+[А-Яа-яA-Za-z .«»\"-]{0,80}?№\s*[\d/А-Яа-я-]+",re.I),
]

def _clean_ref(value:str)->str:
    return re.sub(r"\s+"," ",str(value or "")).strip(" .;,()")


def _reference_signature(value:str)->tuple[str,str]:
    low=normalize_text(value)
    kind=""
    if "постановлен" in low: kind="POSTANOVLENIE"
    elif re.search(r"\bсп\b",low): kind="SP"
    elif "снип" in low: kind="SNIP"
    elif "гост" in low: kind="GOST"
    elif "федеральн" in low or re.search(r"\bфз\b",low): kind="FZ"
    elif "приказ" in low: kind="ORDER"
    nums=re.findall(r"№?\s*(\d+(?:[.\-/]\d+)*(?:\s*-\s*фз)?)",low,re.I)
    number=re.sub(r"\s+","",nums[-1]) if nums else ""
    return kind,number

class NormativeValidityChecker:
    def __init__(self, knowledge_root:str|Path):
        root=Path(knowledge_root)
        self.path=root/"normative_validity_registry.json"
        try:self.data=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:self.data={"records":[],"official_sources":[]}
        self.records=list(self.data.get("records") or [])
        self.sources={x.get("kind"):x for x in self.data.get("official_sources") or []}

    def extract_from_text(self,text:str)->list[str]:
        out=[];seen=set()
        for pat in REF_PATTERNS:
            for m in pat.finditer(str(text or "")):
                ref=_clean_ref(m.group(0))
                key=normalize_text(ref)
                if key and key not in seen:
                    seen.add(key);out.append(ref)
        return out

    def lookup(self,reference:str)->dict[str,Any]|None:
        q=normalize_text(reference)
        if not q:return None
        qsig=_reference_signature(reference)
        ranked=[]
        for rec in self.records:
            aliases=[rec.get("reference","")]+list(rec.get("aliases") or [])
            for alias in aliases:
                a=normalize_text(alias)
                if not a:continue
                asig=_reference_signature(alias)
                score=100 if a==q else 95 if qsig[0] and qsig==asig else 85 if a in q or q in a else 0
                if score:ranked.append((score,rec));break
        if not ranked:return None
        ranked.sort(key=lambda x:x[0],reverse=True)
        return dict(ranked[0][1])

    @staticmethod
    def impact_risk(context:str)->str:
        low=normalize_text(context)
        high=("расчет","расчёт","принят","определен","определён","обоснован","требуем","проектное решение","значение","нагруз","расход","мощност","расстояни")
        medium=("согласно","в соответствии","руководств","предусмотр")
        if any(x in low for x in high):return "Высокий"
        if any(x in low for x in medium):return "Средний"
        return "Низкий"

    def check(self,reference:str,*,document:str="",page=None,context:str="")->dict[str,Any]:
        rec=self.lookup(reference)
        if rec:
            status=rec.get("status") or "Требует верификации"
            source=self.sources.get(rec.get("official_source_kind")) or {}
            return {
              "reference":reference,"canonical_id":rec.get("canonical_id"),"status":status,
              "verified_on":rec.get("verified_on",""),"verified_revision":rec.get("verified_revision",""),
              "replacement":rec.get("replacement",""),"effective_until":rec.get("effective_until",""),
              "official_source":source.get("title",""),"official_source_kind":rec.get("official_source_kind",""),
              "document":document,"page":page,"impact_risk":self.impact_risk(context),
              "context":str(context or "")[:800],"verification_basis":rec.get("status_basis",""),
              "expert_occurrences":rec.get("expert_occurrences",0),"expert_project_count":rec.get("expert_project_count",0),
              "verification_priority":rec.get("verification_priority",""),"priority_score":rec.get("priority_score",0),
              "requires_specialist":status not in {"Действует","Действует с изменениями"}
            }
        low=normalize_text(reference)
        # Legacy SNiP references are not automatically called invalid: applicability/status needs verification.
        edition_risk="Возможна устаревшая редакция" if "снип" in low else "Требует верификации"
        source_kind="MINSTROY" if any(x in low for x in ("сп ","снип","гост")) else "PRAVO"
        source=self.sources.get(source_kind) or {}
        return {
          "reference":reference,"canonical_id":"","status":edition_risk,
          "verified_on":"","verified_revision":"","replacement":"","effective_until":"",
          "official_source":source.get("title",""),"official_source_kind":source_kind,
          "document":document,"page":page,"impact_risk":self.impact_risk(context),
          "context":str(context or "")[:800],
          "verification_basis":"Документ отсутствует в кураторском реестре ExpertCheck; категоричный вывод о статусе запрещён.",
          "expert_occurrences":0,"expert_project_count":0,"verification_priority":"","priority_score":0,
          "requires_specialist":True
        }


    def audit_uploaded_pdfs(self,files,reader,limit:int=3000)->list[dict[str,Any]]:
        """Scan actual page text, including normative lists that produce no engineering finding."""
        out=[];seen=set()
        for uploaded in files or []:
            name=str(getattr(uploaded,"name","document.pdf"))
            try:
                data=uploaded.getvalue() if hasattr(uploaded,"getvalue") else uploaded.read()
                pages=reader(data,name)
            except Exception:
                continue
            for page,text in pages:
                for ref in self.extract_from_text(text):
                    # one citation per page is useful evidence; duplicate pages are suppressed.
                    key=(normalize_text(ref),name,page)
                    if key in seen:continue
                    seen.add(key)
                    # Preserve a local context around the exact reference.
                    low=normalize_text(text); q=normalize_text(ref)
                    pos=low.find(q)
                    context=text[max(0,pos-260):pos+len(ref)+420] if pos>=0 else text[:700]
                    out.append(self.check(ref,document=name,page=page,context=context))
                    if len(out)>=limit:return out
        return out

    def audit_findings(self,findings:Iterable[dict[str,Any]],limit:int=1000)->list[dict[str,Any]]:
        out=[];seen=set()
        for item in findings:
            context=" ".join(str(item.get(k) or "") for k in ("context","section_title","table_title","value_text","table_evidence"))
            for ref in self.extract_from_text(context):
                key=(normalize_text(ref),str(item.get("document") or ""),item.get("page"))
                if key in seen:continue
                seen.add(key)
                out.append(self.check(ref,document=str(item.get("document") or ""),page=item.get("page"),context=context))
                if len(out)>=limit:return out
        return out

    def summary(self,rows):
        rows=list(rows or [])
        counts={}
        for r in rows:counts[r.get("status","Требует верификации")]=counts.get(r.get("status","Требует верификации"),0)+1
        return {
          "references":len(rows),"statuses":counts,
          "high_impact_attention":sum(1 for r in rows if r.get("impact_risk")=="Высокий" and r.get("status") not in {"Действует","Действует с изменениями"}),
          "p1_attention":sum(1 for r in rows if r.get("verification_priority")=="P1" and r.get("status") not in {"Действует","Действует с изменениями"}),
          "curated_registry_records":len(self.records),
          "verified_registry_records":sum(1 for r in self.records if r.get("status") in {"Действует","Действует с изменениями","Утратил силу","Заменён"})
        }
