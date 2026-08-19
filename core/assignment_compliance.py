
from __future__ import annotations
import re, hashlib, math
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code, is_parameter_entity_name
from .entity_property_binding import stable_object_id

ASSIGNMENT_TYPES=("задание на проектирование","техническое задание","тз на проектирование","знп")
REQ_VERBS=("предусмотреть","предусматривается","должен","должна","должны","необходимо","требуется","обеспечить","принять","выполнить","разработать","представить")
PARAMETERS=[
 ("AREA_BUILD",("площадь застройки",),("м²","м2")),
 ("AREA_TOTAL",("общая площадь",),("м²","м2")),
 ("CAPACITY",("производительность","проектная мощность"),("т/ч","т/год","м3/ч","м³/ч")),
 ("POWER_INSTALLED",("мощность","установленная мощность"),("квт","мвт","ква")),
 ("VOLUME",("объем","объём","вместимость"),("м3","м³")),
 ("HEIGHT_BUILD",("высота",),("м",)),
 ("LENGTH",("длина","протяженность","протяжённость"),("м","км")),
 ("FLOW_RATE",("расход",),("м3/ч","м³/ч","л/с")),
 ("QUANTITY",("количество",),("шт","шт.")),
]
OBJECT_HINTS=("ктп","кпп","насосная","резервуар","дск","склад","здание","сооружение","дорога","трубопровод","водовод","дамба","хвостохранилище","карта кучного выщелачивания","цех","абк")

def _assignment_file(name:str,doc_type:str="")->bool:
    blob=normalize_text(name+" "+doc_type)
    return any(x in blob for x in ASSIGNMENT_TYPES)

def _sentences(text:str)->list[str]:
    text=re.sub(r"\s+"," ",str(text or "")).strip()
    parts=re.split(r"(?<=[.!?;])\s+|(?=\d+[.)]\s+)",text)
    return [x.strip() for x in parts if len(x.strip())>=18]


def _atomic_fragments(text:str)->list[dict[str,str]]:
    """Split assignment text into atomic, traceable requirements.

    PDF table extraction often glues several rows into one sentence. We first
    recover numbered rows, then split only on strong requirement boundaries.
    The parser intentionally prefers smaller reviewable atoms over a long
    semantic paragraph containing several unrelated obligations.
    """
    raw=str(text or "").replace("\r","\n")
    raw=re.sub(r"[ \t]+"," ",raw)
    # Preserve row numbers when they survive extraction.
    marked=re.sub(r"(?<!\d)(\d{1,3})[.)]\s+(?=[А-ЯA-Z])",r"\n@@ROW:\1@@ ",raw)
    chunks=[x.strip() for x in re.split(r"\n+",marked) if x.strip()]
    out=[]
    for chunk in chunks:
        m=re.match(r"@@ROW:(\d+)@@\s*(.*)",chunk,re.S)
        row_no=m.group(1) if m else ""
        body=(m.group(2) if m else chunk).strip()
        if len(body)<10: continue
        # Strong separators: semicolon, bullet, or a new obligation verb after
        # punctuation. Commas alone are kept to avoid destroying conditions.
        parts=re.split(r"\s*[•▪–—]\s+|;\s+|(?<=[.!?])\s+(?=(?:предусмотреть|предусматривается|должен|должна|должны|необходимо|требуется|обеспечить|принять|выполнить|разработать|представить)\b)",body,flags=re.I)
        for part in parts:
            part=re.sub(r"\s+"," ",part).strip(" .;:-")
            if len(part)<12: continue
            out.append({"row_no":row_no,"text":part})
    # Fallback for fully flattened text.
    if not out:
        out=[{"row_no":"","text":x} for x in _sentences(raw)]
    return out

def _object_name(sentence:str)->str:
    low=normalize_text(sentence)
    for token in sorted(OBJECT_HINTS,key=len,reverse=True):
        pos=low.find(token)
        if pos>=0:
            # Keep a concise source name around the recognized object.
            raw=sentence[max(0,pos-35):min(len(sentence),pos+len(token)+70)]
            # Prefer known token to avoid swallowing requirement prose.
            return token.upper() if token=="ктп" else token.capitalize()
    return ""

def _parameter(sentence:str):
    low=normalize_text(sentence)
    for code,aliases,units in PARAMETERS:
        if not any(a in low for a in aliases): continue
        m=re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(м²|м2|м³|м3|квт|мвт|ква|т/ч|т/год|м3/ч|м³/ч|л/с|км|м|шт\.?)\b",low,re.I)
        if m:
            value=float(m.group(1).replace(",","."))
            return code,value,m.group(2)
        return code,None,""
    return "",None,""

def extract_requirements(files,reader)->list[dict[str,Any]]:
    rows=[];seen=set()
    for f in files or []:
        name=str(getattr(f,"name",""))
        doc_type=str(getattr(f,"declared_document_type","") or "")
        try:
            data=f.getvalue()
            pages=reader(data,name)
        except Exception:
            continue
        first=" ".join(t for _,t in pages[:2])
        if not (_assignment_file(name,doc_type) or any(x in normalize_text(first) for x in ASSIGNMENT_TYPES)):
            continue
        for page,text in pages:
            for atom in _atomic_fragments(text):
                sentence=atom["text"]
                low=normalize_text(sentence)
                # A table row can be a direct condition (e.g. "Продолжительность смены 12 часов")
                # even without an imperative verb. Require either a verb, a numeric metric,
                # or a recognised object to keep the extraction conservative.
                obj=_object_name(sentence)
                code,value,unit=_parameter(sentence)
                has_requirement_verb=any(v in low for v in REQ_VERBS)
                if not (has_requirement_verb or (code and value is not None) or obj):
                    continue
                key=normalize_text(sentence)
                if key in seen: continue
                seen.add(key)
                rid="ASSIGN-"+hashlib.blake2b(f"{name}|{page}|{atom.get('row_no')}|{key}".encode(),digest_size=7).hexdigest().upper()
                rows.append({
                  "requirement_id":rid,"source_document":name,"page":page,
                  "source_row":atom.get("row_no") or "",
                  "requirement_text":sentence[:1500],"object_name":obj,
                  "object_id":stable_object_id(obj) if obj else "",
                  "parameter_code":canonical_parameter_code(code),"required_value":value,"unit":unit,
                  "requirement_type":"NUMERIC" if code and value is not None else "OBJECT" if obj and not has_requirement_verb else "SEMANTIC",
                  "atomic":True,
                  "confidence":0.90 if code and value is not None else 0.78 if atom.get("row_no") else 0.70 if obj else 0.60
                })
    return rows

def _norm_unit(value:str)->str:
    return normalize_text(value).replace(" ","").replace("м2","м²").replace("м3","м³")


_STOPWORDS={"предусмотреть","предусматривается","должен","должна","должны","необходимо","требуется","обеспечить","принять","выполнить","разработать","представить","проект","проектом","проектной","документации","объект","объекта","сведения","решения"}

def _semantic_tokens(text:str)->set[str]:
    low=normalize_text(text)
    words=set(re.findall(r"[а-яa-z0-9-]{4,}",low,re.I))
    return {w for w in words if w not in _STOPWORDS}

def _semantic_evidence_candidates(requirement:str,findings:list[dict[str,Any]],object_name:str="",limit:int=6)->list[dict[str,Any]]:
    q=_semantic_tokens(requirement)
    obj=normalize_text(object_name)
    ranked=[]
    for f in findings:
        blob=" ".join(str(f.get(k) or "") for k in ("context","section_title","table_title","table_evidence","value_text","parameter_name","object_hint","semantic_anchor_name"))
        tokens=_semantic_tokens(blob)
        overlap=q & tokens
        if not overlap:
            continue
        score=len(overlap)*3
        fobj=normalize_text(f.get("semantic_anchor_name") or f.get("object_hint") or "")
        if obj:
            if obj in fobj or fobj in obj:
                score+=7
            elif fobj and not is_parameter_entity_name(fobj):
                score-=2
        if f.get("page"):score+=1
        if f.get("value") is not None:score+=1
        if score>=5:
            ranked.append((score,f,sorted(overlap)))
    ranked.sort(key=lambda x:x[0],reverse=True)
    return [{
      "score":score,
      "document":f.get("document"),"page":f.get("page"),
      "object":f.get("semantic_anchor_name") or f.get("object_hint") or "",
      "parameter":f.get("parameter_name") or "",
      "value_text":f.get("value_text") or "",
      "context":str(f.get("context") or f.get("table_evidence") or "")[:500],
      "matched_terms":terms,
    } for score,f,terms in ranked[:limit]]

def _registry_object_matches(object_name:str,registry:list[dict[str,Any]])->list[dict[str,Any]]:
    q=normalize_text(object_name)
    if not q:return []
    qwords=_semantic_tokens(q)
    scored=[]
    for r in registry:
        name=str(r.get("name") or r.get("object_name") or r.get("Наименование") or "")
        n=normalize_text(name)
        if not n or is_parameter_entity_name(name):continue
        if q==n:
            score=100
        elif q in n or n in q:
            score=90
        else:
            nw=_semantic_tokens(n)
            inter=qwords&nw
            score=round(100*len(inter)/max(1,len(qwords|nw))) if inter else 0
        if score>=70:scored.append((score,r,name))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{"score":score,"name":name,"row":r} for score,r,name in scored[:5]]


def compare_requirements(requirements:list[dict[str,Any]],findings:list[dict[str,Any]],registry:list[dict[str,Any]]|None=None)->list[dict[str,Any]]:
    """Conservative compliance evaluation.

    Automatic compliance is allowed only for strong structured evidence.
    Semantic resemblance is evidence for review, never proof of compliance.
    """
    registry=registry or []
    out=[]
    for req in requirements:
        obj=str(req.get("object_name") or "")
        obj_norm=normalize_text(obj)
        code=canonical_parameter_code(req.get("parameter_code"))
        status="Требуется смысловая проверка"
        evidence=[]
        evidence_candidates=[]
        difference=None
        match_confidence=0.0
        decision_basis=""

        if req.get("requirement_type")=="OBJECT" and obj:
            matches=_registry_object_matches(obj,registry)
            if matches and matches[0]["score"]>=90:
                status="Соответствует заданию"
                match_confidence=min(.98,matches[0]["score"]/100)
                evidence=[m["name"] for m in matches[:4]]
                decision_basis="Объект подтверждён реестром проекта с высокой степенью совпадения."
            elif matches:
                status="Требование не подтверждено"
                match_confidence=matches[0]["score"]/100
                evidence=[m["name"] for m in matches[:4]]
                decision_basis="Найдены только похожие объекты; автоматическое подтверждение запрещено."
            else:
                status="Требование не подтверждено"
                decision_basis="Объект не найден в подтверждённом реестре проекта."

        elif req.get("requirement_type")=="NUMERIC" and code:
            candidates=[]
            for f in findings:
                if canonical_parameter_code(f.get("parameter_code"))!=code: continue
                fobj=str(f.get("semantic_anchor_name") or f.get("object_hint") or "")
                fnorm=normalize_text(fobj)
                if not fnorm or is_parameter_entity_name(fobj): continue
                # Numeric compliance requires explicit same-object binding.
                if obj_norm and not (obj_norm==fnorm or obj_norm in fnorm or fnorm in obj_norm):
                    continue
                binding=f.get("entity_property_binding") or {}
                if binding and binding.get("valid") is False:
                    continue
                try: val=float(f.get("value"))
                except Exception: continue
                candidates.append((val,f))
            if not candidates:
                status="Требование не подтверждено"
                decision_basis="Не найдено структурированное значение для того же объекта и показателя."
            else:
                required=float(req["required_value"])
                same=[(v,f) for v,f in candidates if math.isclose(v,required,rel_tol=.002,abs_tol=.05)]
                if same:
                    status="Соответствует заданию"
                    match_confidence=.96
                    evidence=[f"{f.get('document')}, стр. {f.get('page')}: {fobj if (fobj:=str(f.get('semantic_anchor_name') or f.get('object_hint') or '')) else obj} · {f.get('parameter_name')} — {v:g} {f.get('unit') or ''}" for v,f in same[:5]]
                    decision_basis="Совпало структурированное числовое значение для того же объекта и показателя."
                else:
                    status="Выявлено отклонение"
                    match_confidence=.92
                    difference=min(abs(v-required) for v,_ in candidates)
                    evidence=[f"{f.get('document')}, стр. {f.get('page')}: {str(f.get('semantic_anchor_name') or f.get('object_hint') or obj)} · {f.get('parameter_name')} — {v:g} {f.get('unit') or ''}" for v,f in candidates[:5]]
                    decision_basis="Для того же объекта/показателя найдены иные числовые значения."

        else:
            evidence_candidates=_semantic_evidence_candidates(str(req.get("requirement_text") or ""),findings,obj,limit=6)
            # Similar text is not compliance. It merely prepares evidence for AI/specialist review.
            if evidence_candidates:
                status="Требуется смысловая проверка"
                match_confidence=min(.75,(evidence_candidates[0]["score"] or 0)/20)
                evidence=[f"{x.get('document')}, стр. {x.get('page')}: {x.get('context') or x.get('value_text')}" for x in evidence_candidates[:4]]
                decision_basis="Найдены смыслово связанные фрагменты, но они не доказывают выполнение требования."
            else:
                status="Требование не подтверждено"
                decision_basis="Связанные проектные доказательства не найдены."

        out.append({
          **req,"status":status,"evidence":evidence,"evidence_candidates":evidence_candidates,
          "difference":difference,"match_confidence":round(match_confidence,2),
          "decision_basis":decision_basis,
          "recommendation":
            "Синхронизировать проектное решение с Заданием на проектирование." if status=="Выявлено отклонение" else
            "Проверить применимость требования и подтвердить его выполнение конкретным проектным решением." if status in {"Требование не подтверждено","Требуется смысловая проверка"} else
            "Дополнительное действие не требуется."
        })
    return out


def summary(rows:list[dict[str,Any]])->dict[str,int]:
    result={"total":len(rows),"compliant":0,"deviation":0,"unconfirmed":0,"semantic":0}
    for r in rows:
        s=r.get("status")
        if s=="Соответствует заданию":result["compliant"]+=1
        elif s=="Выявлено отклонение":result["deviation"]+=1
        elif s=="Требование не подтверждено":result["unconfirmed"]+=1
        else:result["semantic"]+=1
    return result
