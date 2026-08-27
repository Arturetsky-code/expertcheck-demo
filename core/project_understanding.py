
from __future__ import annotations
import hashlib,re
from collections import defaultdict
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code,is_parameter_entity_name,is_service_object_candidate
from .entity_property_binding import stable_object_id
from .checklist_routing import canonical_section
from .table_row_integrity import is_integrity_blocked
from .object_scope_guard import assess_scope_binding
from .fact_admission import assess_fact_admission

AUTHORITATIVE_SECTION_WEIGHT={"ПЗ":100,"ПЗУ":96,"АР":88,"КР":88,"ТХ":92,"ИОС1":84,"ИОС2":84,"ИОС3":84,"ИОС4":84,"ИОС5":84,"ПОС":68,"ООС":60}
PARAMETER_OWNER_HINTS={
 "AREA_BUILD":{"ПЗУ","АР","ПЗ"},"AREA_TOTAL":{"АР","ПЗ"},"VOLUME_BUILD":{"АР","ПЗ"},
 "HEIGHT_BUILD":{"АР","ПЗ"},"FLOORS":{"АР","ПЗ"},"CAPACITY":{"ТХ","ПЗ"},
 "POWER_INSTALLED":{"ИОС1","ТХ","ПЗ"},"POWER_CALCULATED":{"ИОС1"},
 "VOLTAGE":{"ИОС1"},"FLOW_RATE":{"ИОС2","ТХ"},"PRESSURE":{"ИОС2","ТХ"},
 "DIAMETER":{"ИОС2","ТХ"},"LENGTH":{"ПЗУ","ИОС2","ПЗ"},"QUANTITY":{"ПЗ","ПЗУ"},
 "MOISTURE":{"ТХ","ПЗ"},"BULK_DENSITY":{"ТХ","ПЗ"},
}

def _name(row:dict[str,Any])->str:
    return str(row.get("Наименование объекта") or row.get("Объект") or row.get("name") or "").strip()

def _position(row:dict[str,Any])->str:
    return str(row.get("Позиция по ГП") or row.get("Позиция") or row.get("position") or "").strip()

def _source_section(f:dict[str,Any])->str:
    return canonical_section(str(f.get("document_type") or f.get("section") or f.get("document") or ""))

def _registry_object_id(row:dict[str,Any])->str:
    return stable_object_id(_name(row),_position(row))


def _registry_source_lineage(row:dict[str,Any])->tuple[str,list[dict[str,Any]],str]:
    records=[dict(x) for x in (row.get('source_records') or []) if isinstance(x,dict)]
    for kind,doc_key,page_key in (
        ('PZ_COMPLEX_OBJECT_REGISTER','pz_document','pz_page'),
        ('GENERAL_PLAN_EXPLICATION','general_plan_document','general_plan_page'),
    ):
        document=row.get(doc_key)
        if document and not any(str(x.get('document') or '')==str(document) for x in records):
            records.append({'kind':kind,'document':document,'page':row.get(page_key),'position':_position(row)})
    labels=[]
    raw=row.get('Источники') or row.get('sources') or ''
    if isinstance(raw,(list,tuple,set)):
        labels.extend(str(x).strip() for x in raw if str(x).strip())
    elif str(raw).strip():
        labels.append(str(raw).strip())
    for record in records:
        document=str(record.get('document') or '').strip()
        page=record.get('page')
        if document:
            labels.append(f"{document}, стр. {page}" if page not in (None,'') else document)
    labels=list(dict.fromkeys(x for x in labels if x and normalize_text(x)!='модель понимания проекта'))
    physical=any(str(x.get('document') or '').strip() for x in records)
    status='VERIFIED_SOURCE' if physical else ('DESCRIBED_SOURCE' if labels else 'UNRESOLVED_SOURCE')
    return '; '.join(labels),records,status

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
        sources,source_records,source_lineage_status=_registry_source_lineage(row)
        obj={
          "object_id":oid,"name":name,"position":_position(row),
          "object_type":row.get("Тип объекта") or row.get("object_type_name") or "Инженерный объект",
          "status":row.get("Статус") or row.get("status") or "",
          "registry_confidence":row.get("Уверенность") or row.get("confidence") or 0,
          "sources":sources,
          "source_records":source_records,
          "source_lineage_status":source_lineage_status,
          "properties":defaultdict(list),"unresolved_evidence":[],
        }
        objects[oid]=obj
        n=normalize_text(name);aliases.setdefault(n,[]).append(oid)
        if obj["position"]:positions.setdefault(re.sub(r"\s+","",obj["position"]),[]).append(oid)

    stats={"objects":len(objects),"properties_bound":0,"properties_unresolved":0,"properties_rejected":0}
    for f in findings or []:
        code=canonical_parameter_code(f.get("parameter_code"))
        if code in {"OBJECT_ENTRY","OBJECT_CANDIDATE"}:continue
        if is_integrity_blocked(f):
            stats["properties_rejected"]+=1
            continue
        binding_status=str(f.get("binding_status") or f.get("property_binding_status") or "").upper()
        row_locked=binding_status in {"ROW_LOCKED","POSITION_LOCKED","EXACT_OBJECT"} or str(f.get("row_integrity_status") or "").startswith("CONFIRMED")
        # A row-bound property owns its original object label. Semantic anchoring
        # is allowed only for non-tabular/loose evidence.
        original_owner=str(f.get("object_hint") or "").strip()
        semantic_owner=str(f.get("semantic_anchor_name") or "").strip()
        # Fact Lineage Integrity Gate: a fact that was extracted without an owner
        # cannot silently acquire one during assembly. Semantic recovery is allowed
        # only when the upstream stage explicitly marked the anchor as verified.
        lineage_verified=bool(f.get("semantic_anchor_verified") or f.get("owner_recovery_verified") or f.get("binding_status") in {"ROW_LOCKED","POSITION_LOCKED","EXACT_OBJECT"})
        if row_locked:
            raw_obj=original_owner
        elif original_owner:
            raw_obj=semantic_owner or original_owner
        elif semantic_owner and lineage_verified:
            raw_obj=semantic_owner
        else:
            raw_obj=""
            if semantic_owner:
                f["fact_lineage_decision"]="HOLD"
                f["fact_lineage_reason"]="Исходный факт не имел владельца; поздняя семантическая привязка не подтверждена независимым доказательством."
        if not raw_obj or is_parameter_entity_name(raw_obj):
            stats["properties_rejected"]+=1
            f["project_understanding_binding"]="Отклонено: не подтверждена линия владельца факта"
            continue
        binding=f.get("entity_property_binding") or {}
        if binding and binding.get("valid") is False:
            stats["properties_rejected"]+=1;continue
        candidate_ids=[]
        pos_source=f.get("genplan_position") if row_locked else (f.get("semantic_anchor_position") or f.get("genplan_position"))
        pos=re.sub(r"\s+","",str(pos_source or ""))
        if pos and pos in positions:candidate_ids=list(positions[pos])
        if not candidate_ids:
            n=normalize_text(raw_obj)
            for alias,ids in aliases.items():
                if n==alias or (len(n)>=4 and (n in alias or alias in n)):
                    candidate_ids.extend(ids)
        candidate_ids=list(dict.fromkeys(candidate_ids))
        if len(candidate_ids)!=1:
            stats["properties_unresolved"]+=1
            f["project_understanding_binding"]="Недостаточно данных"
            continue
        oid=candidate_ids[0];section=_source_section(f)
        scope_guard=assess_scope_binding(f,objects[oid]["name"],objects[oid]["position"])
        f.update(scope_guard)
        admission=assess_fact_admission(f)
        f.update(admission)
        if admission["fact_admission_decision"] == "REJECT":
            stats["properties_rejected"]+=1
            f["project_understanding_binding"]="Отклонено: границы объекта" if scope_guard.get("scope_binding_decision")=="REJECT" else "Отклонено: Fact Admission Gate"
            continue
        if admission["fact_admission_decision"] != "ADMIT":
            stats["properties_unresolved"]+=1
            f["project_understanding_binding"]="Требует проверки границ объекта" if scope_guard.get("scope_binding_decision")=="HOLD" else "Требует подтверждения инженерного факта"
            continue
        ev={
          "parameter_code":code,"parameter_name":f.get("parameter_name") or code,
          "value":f.get("value"),"value_text":f.get("value_text"),"unit":f.get("unit"),
          "section":section,"document":f.get("document"),"page":f.get("page"),
          "context":str(f.get("context") or f.get("table_evidence") or "")[:600],
          "confidence":float(f.get("core2_confidence") or f.get("confidence") or 0),
          "evidence_id":f.get("evidence_id"),
          "evidence_trust_score":f.get("evidence_trust_score"),
          "evidence_trust_grade":f.get("evidence_trust_grade"),
          "evidence_quality_decision":f.get("evidence_quality_decision"),
          "row_integrity_status":f.get("row_integrity_status"),
          "binding_status":f.get("binding_status") or f.get("property_binding_status"),
          "match_method":f.get("match_method"),
          "genplan_position":f.get("genplan_position"),
          "owner_section":section in PARAMETER_OWNER_HINTS.get(code,set()),
          "scope_binding_score":scope_guard.get("scope_binding_score"),
          "scope_binding_decision":scope_guard.get("scope_binding_decision"),
          "scope_binding_reasons":scope_guard.get("scope_binding_reasons"),
          "fact_admission_score":admission.get("fact_admission_score"),
          "fact_admission_decision":admission.get("fact_admission_decision"),
          "fact_admission_reasons":admission.get("fact_admission_reasons"),
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
            section_values: dict[str, list[str]] = defaultdict(list)
            for x in evidence:
                try:
                    value = round(float(x["value"]), 8)
                    numeric.append(value)
                    rendered = f"{value:g} {str(x.get('unit') or '').strip()}".strip()
                    section = str(x.get("section") or "Раздел не определён")
                    if rendered not in section_values[section]:
                        section_values[section].append(rendered)
                except Exception:pass
            unique=sorted(set(numeric))
            prop_summary.append({
              "parameter_code":code,"parameter_name":next((x["parameter_name"] for x in evidence if x["parameter_name"]),code),
              "evidence_count":len(evidence),"sections":sections,
              "owner_evidence":any(x["owner_section"] for x in evidence),
              "value_conflict":len(unique)>1,"values":unique[:12],
              "values_by_section":[
                  {"section": section, "values": values}
                  for section, values in sorted(section_values.items())
              ],
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
