from __future__ import annotations
from typing import Any
from .normalization import normalize_text
from .checklist_routing import canonical_section
from .object_semantics import canonical_parameter_code

DRAWING_SECTIONS={"АР","КР","ПЗУ","ТХ","ИОС1","ИОС2","ИОС3","ИОС4","ИОС5"}


def classify_drawing_context(item: dict[str,Any]) -> dict[str,Any]:
    section=canonical_section(str(item.get("document_type") or item.get("section") or item.get("document") or ""))
    text=normalize_text(" ".join(str(item.get(k) or "") for k in (
        "context","table_title","structural_zone","row_text","parameter_name","match_method"
    )))
    if section not in DRAWING_SECTIONS:
        return {"drawing_evidence":False,"drawing_kind":""}
    kind="drawing"
    if "экспликац" in text and "помещ" in text: kind="room_explication"
    elif "экспликац" in text: kind="explication"
    elif "план этаж" in text or "план на отм" in text: kind="floor_plan"
    elif "разрез" in text: kind="section_view"
    elif "фасад" in text: kind="facade"
    elif "генеральн" in text or "генплан" in text: kind="general_plan"
    elif "спецификац" in text: kind="specification"
    elif "схем" in text: kind="scheme"
    return {
        "drawing_evidence":True,
        "drawing_kind":kind,
        "drawing_section":section,
        "drawing_parameter_code":canonical_parameter_code(item.get("parameter_code")),
    }


def annotate_drawing_evidence(findings:list[dict[str,Any]]) -> dict[str,Any]:
    stats={"drawing_facts":0,"room_explication_facts":0,"sections":set()}
    for item in findings or []:
        info=classify_drawing_context(item)
        item.update(info)
        if info["drawing_evidence"]:
            stats["drawing_facts"]+=1
            stats["sections"].add(info["drawing_section"])
            if info["drawing_kind"]=="room_explication":
                stats["room_explication_facts"]+=1
                if canonical_parameter_code(item.get("parameter_code"))=="AREA_TOTAL":
                    item["metric_semantic_scope"]="room_area_sum"
    stats["sections"]=sorted(stats["sections"])
    return stats
