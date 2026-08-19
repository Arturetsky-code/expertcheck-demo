
from __future__ import annotations
import hashlib,re
from typing import Any
from .normalization import normalize_text
from .object_semantics import is_parameter_entity_name, canonical_parameter_code

def stable_object_id(name:str,position:str="")->str:
    pos=re.sub(r"\s+","",str(position or ""))
    if pos:
        return "OBJ-POS-"+re.sub(r"[^0-9A-Za-zА-Яа-я]+","-",pos).strip("-").upper()[:32]
    key=normalize_text(name)
    return "OBJ-"+hashlib.blake2b(key.encode("utf-8"),digest_size=6).hexdigest().upper()

def binding_key(object_id:str,parameter_code:str,scope:str="default")->str:
    return f"{object_id}|{canonical_parameter_code(parameter_code)}|{scope or 'default'}"

def validate_entity_property(object_name:str,parameter_name:str="",parameter_code:str="",position:str="")->dict[str,Any]:
    name=re.sub(r"\s+"," ",str(object_name or "")).strip(" .;:-")
    if not name or name=="Не определён":
        return {"valid":False,"reason":"объект не определён","object_id":""}
    if is_parameter_entity_name(name):
        return {"valid":False,"reason":"наименование является ТЭП/характеристикой, а не объектом","object_id":""}
    if parameter_name and normalize_text(name)==normalize_text(parameter_name):
        return {"valid":False,"reason":"объект совпадает с наименованием показателя","object_id":""}
    return {
      "valid":True,"reason":"объект и показатель разделены",
      "object_id":stable_object_id(name,position),
      "object_name":name,
      "parameter_code":canonical_parameter_code(parameter_code),
      "parameter_name":parameter_name,
    }

def annotate_findings(findings:list[dict[str,Any]])->dict[str,int]:
    stats={"bound":0,"rejected_parameter_as_object":0,"unbound":0}
    for item in findings:
        if str(item.get("parameter_code") or "") in {"OBJECT_ENTRY","OBJECT_CANDIDATE"}:
            continue
        name=str(item.get("semantic_anchor_name") or item.get("object_hint") or "")
        check=validate_entity_property(
            name,str(item.get("parameter_name") or ""),str(item.get("parameter_code") or ""),
            str(item.get("genplan_position") or "")
        )
        item["entity_property_binding"]=check
        item["object_id"]=check.get("object_id","")
        if check["valid"]:
            item["binding_key"]=binding_key(check["object_id"],item.get("parameter_code"),item.get("comparison_scope","default"))
            stats["bound"]+=1
        elif "ТЭП" in check["reason"] or "показателя" in check["reason"]:
            stats["rejected_parameter_as_object"]+=1
        else:
            stats["unbound"]+=1
    return stats
