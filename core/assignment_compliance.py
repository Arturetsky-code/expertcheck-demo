
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
            for sentence in _sentences(text):
                low=normalize_text(sentence)
                if not any(v in low for v in REQ_VERBS):
                    continue
                key=normalize_text(sentence)
                if key in seen: continue
                seen.add(key)
                obj=_object_name(sentence)
                code,value,unit=_parameter(sentence)
                rid="ASSIGN-"+hashlib.blake2b(f"{name}|{page}|{key}".encode(),digest_size=7).hexdigest().upper()
                rows.append({
                  "requirement_id":rid,"source_document":name,"page":page,
                  "requirement_text":sentence[:1500],"object_name":obj,
                  "object_id":stable_object_id(obj) if obj else "",
                  "parameter_code":canonical_parameter_code(code),"required_value":value,"unit":unit,
                  "requirement_type":"NUMERIC" if code and value is not None else "OBJECT" if obj else "SEMANTIC",
                  "confidence":0.88 if code and value is not None else 0.72 if obj else 0.58
                })
    return rows

def _norm_unit(value:str)->str:
    return normalize_text(value).replace(" ","").replace("м2","м²").replace("м3","м³")

def compare_requirements(requirements:list[dict[str,Any]],findings:list[dict[str,Any]],registry:list[dict[str,Any]]|None=None)->list[dict[str,Any]]:
    registry=registry or []
    out=[]
    for req in requirements:
        obj=normalize_text(req.get("object_name") or "")
        code=canonical_parameter_code(req.get("parameter_code"))
        status="Требуется смысловая проверка";evidence=[];difference=None
        if req.get("requirement_type")=="OBJECT" and obj:
            matches=[r for r in registry if obj in normalize_text(r.get("name") or r.get("object_name") or r.get("Наименование") or "")]
            if matches:
                status="Соответствует заданию"
                evidence=[str(m.get("name") or m.get("object_name") or m.get("Наименование") or "") for m in matches[:4]]
            else:
                status="Требование не подтверждено"
        elif req.get("requirement_type")=="NUMERIC" and code:
            candidates=[]
            for f in findings:
                if canonical_parameter_code(f.get("parameter_code"))!=code: continue
                fobj=normalize_text(f.get("semantic_anchor_name") or f.get("object_hint") or "")
                if obj and obj not in fobj and fobj not in obj: continue
                if is_parameter_entity_name(fobj): continue
                val=f.get("value")
                try: val=float(val)
                except Exception: continue
                candidates.append((val,f))
            if not candidates:
                status="Требование не подтверждено"
            else:
                required=float(req["required_value"])
                same=[(v,f) for v,f in candidates if math.isclose(v,required,rel_tol=.002,abs_tol=.05)]
                if same:
                    status="Соответствует заданию"
                    evidence=[f"{f.get('document')}, стр. {f.get('page')}: {f.get('object_hint')} · {f.get('parameter_name')} — {v:g} {f.get('unit') or ''}" for v,f in same[:5]]
                else:
                    status="Выявлено отклонение"
                    difference=min(abs(v-required) for v,_ in candidates)
                    evidence=[f"{f.get('document')}, стр. {f.get('page')}: {f.get('object_hint')} · {f.get('parameter_name')} — {v:g} {f.get('unit') or ''}" for v,f in candidates[:5]]
        out.append({**req,"status":status,"evidence":evidence,"difference":difference,
                    "recommendation":"Синхронизировать проектное решение с Заданием на проектирование." if status=="Выявлено отклонение" else
                                     "Найти подтверждение требования в ПД либо проверить применимость требования специалистом." if status in {"Требование не подтверждено","Требуется смысловая проверка"} else
                                     "Дополнительное действие не требуется."})
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
