
from __future__ import annotations
import hashlib,re
from collections import defaultdict
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code,is_parameter_entity_name,is_service_object_candidate
from .entity_property_binding import stable_object_id
from .checklist_routing import canonical_section

AUTHORITATIVE_SECTION_WEIGHT={"ПЗ":100,"ПЗУ":96,"АР":88,"КР":88,"ТХ":92,"ИОС1":84,"ИОС2":84,"ИОС3":84,"ИОС4":84,"ИОС5":84,"ПОС":68,"ООС":60}
PARAMETER_OWNER_HINTS={
 "AREA_BUILD":{"ПЗУ","АР","ПЗ"},"AREA_TOTAL":{"АР","ПЗ"},"VOLUME_BUILD":{"АР","ПЗ"},
 "HEIGHT_BUILD":{"АР","ПЗ"},"FLOORS":{"АР","ПЗ"},"CAPACITY":{"ТХ","ПЗ"},
 "POWER_INSTALLED":{"ИОС1","ТХ","ПЗ"},"POWER_CALCULATED":{"ИОС1"},
 "VOLTAGE":{"ИОС1"},"FLOW_RATE":{"ИОС2","ТХ"},"PRESSURE":{"ИОС2","ТХ"},
 "DIAMETER":{"ИОС2","ТХ"},"LENGTH":{"ПЗУ","ИОС2","ПЗ"},"QUANTITY":{"ПЗ","ПЗУ"},
}

def _name(row:dict[str,Any])->str:
    return str(row.get("Наименование объекта") or row.get("Объект") or row.get("name") or "").strip()

def _position(row:dict[str,Any])->str:
    return str(row.get("Позиция по ГП") or row.get("Позиция") or row.get("position") or "").strip()

def _source_section(f:dict[str,Any])->str:
    return canonical_section(str(f.get("document_type") or f.get("section") or f.get("document") or ""))

def _registry_object_id(row:dict[str,Any])->str:
    return stable_object_id(_name(row),_position(row))

def build_project_object_model(registry:list[dict[str,Any]],findings:list[dict[str,Any]])->dict[str,Any]:
    """Build a conservative project ontology: object -> property -> evidence.

    A property never creates an object. Findings are attached only when an
    existing registry object can be identified with strong evidence.
    """
    objects={}
    aliases={}
    positions={}
    for row in registry or []:
        name=_name(row)
        if not name or is_parameter_entity_name(name):continue
        oid=_registry_object_id(row)
        obj={
          "object_id":oid,"name":name,"position":_position(row),
          "object_type":row.get("Тип объекта") or row.get("object_type_name") or "Инженерный объект",
          "status":row.get("Статус") or row.get("status") or "",
          "registry_confidence":row.get("Уверенность") or row.get("confidence") or 0,
          "sources":row.get("Источники") or row.get("sources") or "",
          "properties":defaultdict(list),"unresolved_evidence":[],
        }
        objects[oid]=obj
        n=normalize_text(name);aliases.setdefault(n,[]).append(oid)
        if obj["position"]:positions.setdefault(re.sub(r"\s+","",obj["position"]),[]).append(oid)

    stats={"objects":len(objects),"properties_bound":0,"properties_unresolved":0,"properties_rejected":0}
    for f in findings or []:
        code=canonical_parameter_code(f.get("parameter_code"))
        if code in {"OBJECT_ENTRY","OBJECT_CANDIDATE"}:continue
        raw_obj=str(f.get("semantic_anchor_name") or f.get("object_hint") or "").strip()
        if not raw_obj or is_parameter_entity_name(raw_obj):
            stats["properties_rejected"]+=1;continue
        binding=f.get("entity_property_binding") or {}
        if binding and binding.get("valid") is False:
            stats["properties_rejected"]+=1;continue
        candidate_ids=[]
        pos=re.sub(r"\s+","",str(f.get("semantic_anchor_position") or f.get("genplan_position") or ""))
        if pos and pos in positions:candidate_ids=list(positions[pos])
        if not candidate_ids:
            n=normalize_text(raw_obj)
            for alias,ids in aliases.items():
                if n==alias or (len(n)>=4 and (n in alias or alias in n)):
                    candidate_ids.extend(ids)
        candidate_ids=list(dict.fromkeys(candidate_ids))
        if len(candidate_ids)!=1:
            stats["properties_unresolved"]+=1
            continue
        oid=candidate_ids[0];section=_source_section(f)
        ev={
          "parameter_code":code,"parameter_name":f.get("parameter_name") or code,
          "value":f.get("value"),"value_text":f.get("value_text"),"unit":f.get("unit"),
          "section":section,"document":f.get("document"),"page":f.get("page"),
          "context":str(f.get("context") or f.get("table_evidence") or "")[:600],
          "confidence":float(f.get("core2_confidence") or f.get("confidence") or 0),
          "owner_section":section in PARAMETER_OWNER_HINTS.get(code,set()),
        }
        objects[oid]["properties"][code].append(ev)
        f["project_understanding_object_id"]=oid
        f["project_understanding_object_name"]=objects[oid]["name"]
        f["project_understanding_section"]=section
        f["project_understanding_binding"]="Подтверждено"
        stats["properties_bound"]+=1

    # Convert defaultdict and summarize property coverage/conflicts.
    rows=[]
    for obj in objects.values():
        prop_summary=[]
        clean={}
        for code,evidence in obj["properties"].items():
            clean[code]=evidence
            sections=sorted({x["section"] for x in evidence if x["section"]})
            numeric=[]
            for x in evidence:
                try:numeric.append(round(float(x["value"]),8))
                except Exception:pass
            unique=sorted(set(numeric))
            prop_summary.append({
              "parameter_code":code,"parameter_name":next((x["parameter_name"] for x in evidence if x["parameter_name"]),code),
              "evidence_count":len(evidence),"sections":sections,
              "owner_evidence":any(x["owner_section"] for x in evidence),
              "value_conflict":len(unique)>1,"values":unique[:12],
            })
        obj["properties"]=clean
        obj["property_summary"]=prop_summary
        obj["property_count"]=len(prop_summary)
        obj["evidence_count"]=sum(x["evidence_count"] for x in prop_summary)
        obj["conflict_count"]=sum(1 for x in prop_summary if x["value_conflict"])
        rows.append(obj)
    return {"objects":rows,"stats":stats}

def understanding_quality(model:dict[str,Any])->dict[str,Any]:
    objects=model.get("objects") or [];stats=model.get("stats") or {}
    bound=int(stats.get("properties_bound") or 0);unresolved=int(stats.get("properties_unresolved") or 0);rejected=int(stats.get("properties_rejected") or 0)
    denom=max(1,bound+unresolved)
    binding_precision=round(bound/denom*100,1)
    with_properties=sum(1 for x in objects if x.get("property_count"))
    conflict_objects=sum(1 for x in objects if x.get("conflict_count"))
    return {
      "objects":len(objects),"objects_with_properties":with_properties,
      "binding_precision_proxy_pct":binding_precision,
      "unresolved_properties":unresolved,"rejected_false_bindings":rejected,
      "objects_with_internal_conflicts":conflict_objects,
      "quality_status":"Высокая" if binding_precision>=90 and unresolved<=max(2,bound*.08) else "Рабочая" if binding_precision>=75 else "Требует внимания",
      "guardrail":"Неподтверждённая привязка не используется как доказательство межраздельного несоответствия."
    }
