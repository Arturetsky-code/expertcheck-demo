from __future__ import annotations

import re
from typing import Any, Iterable

from .normalization import normalize_text
from .object_semantics import is_service_object_candidate
from .object_quality_rules import name_rejection_reasons
from .position_rules import is_date_like_position

PROJECT_TOKENS = ("проектируем", "проектом предусматри", "новое строительство", "нов. стр", "строительство", "реконструкц")
EXISTING_TOKENS = ("сущ", "существ", "действующ", "сохраняем")
PERSPECTIVE_TOKENS = ("перспект", "последующ", "резерв")
RECONSTRUCTION_TOKENS = ("реконстр", "техническое перевооруж", "модерниз")
DEMOLITION_TOKENS = ("демонт", "снос", "ликвидир")
FILEISH_RE = re.compile(r"(?:\.pdf|\.xml|\.sig|\.zip|\.docx?|\.xlsx?|раздел\s+пд|подраздел\s+пд|том\s*№?|часть\s*№?)", re.I)


def lifecycle_status(item: dict[str, Any]) -> str:
    text = normalize_text(" ".join(str(item.get(k) or "") for k in (
        "value_text", "object_hint", "context", "structural_zone", "table_evidence",
        "review_note", "match_method", "status_note", "general_plan_note", "remark",
    )))
    if any(t in text for t in DEMOLITION_TOKENS): return "Демонтируемый"
    if any(t in text for t in RECONSTRUCTION_TOKENS): return "Реконструируемый"
    if any(t in text for t in PERSPECTIVE_TOKENS): return "Перспективный"
    if any(t in text for t in EXISTING_TOKENS): return "Существующий"
    if item.get("general_plan_explication") and re.search(r"\bпроект\.?\b", text): return "Проектируемый"
    if any(t in text for t in PROJECT_TOKENS): return "Проектируемый"
    # General Plan explication is an independent object register. Preserve an
    # explicit lifecycle status extracted by GeneralPlan Intelligence. When an
    # explication page contains no markers of existing/prospective objects, the
    # engine may safely classify its rows as project objects. Otherwise the row
    # remains visible as a candidate rather than disappearing from the registry.
    if item.get("general_plan_explication"):
        gp_status = str(item.get("general_plan_design_status") or "").strip()
        if gp_status in {"Проектируемый", "Реконструируемый", "Существующий", "Перспективный"}:
            return gp_status
        if bool(item.get("general_plan_project_default")):
            return "Проектируемый"
        return "Не определён"
    return "Проектируемый" if str(item.get("document_type") or "") in {"ПЗ", "XML"} and item.get("parameter_code") == "OBJECT_ENTRY" else "Не определён"


def classify_zone(item: dict[str, Any]) -> str:
    text = normalize_text(" ".join(str(item.get(k) or "") for k in (
        "structural_zone", "context", "table_type", "table_evidence", "match_method", "parameter_name"
    )))
    if any(t in text for t in ("состав проектной документации", "ведомость документов", "содержание", "оглавление", "перечень файлов", "титульный")):
        return "DOCUMENT_SERVICE"
    if any(t in text for t in ("экспликация", "состав сложного объекта", "перечень объектов", "реестр объектов")):
        return "OBJECT_REGISTER"
    if any(t in text for t in ("таблица тэп", "технико экономические показатели", "технико-экономические показатели")):
        return "OBJECT_TEP"
    if item.get("general_plan_field") or item.get("general_plan_named_label"):
        return "DRAWING_FIELD"
    return "NARRATIVE"


def evidence_score(item: dict[str, Any]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    if item.get("hard_object_gate_blocked") or item.get("structure_guard_blocked"):
        return -1000, [str(item.get("hard_object_gate_reason") or item.get("structure_guard_reason") or "заблокировано Object Gate")]
    service, service_reasons = is_service_object_candidate(item)
    raw = str(item.get("value_text") or item.get("object_hint") or "")
    if service or FILEISH_RE.search(raw):
        return -100, service_reasons or ["служебная строка или имя файла"]
    zone = classify_zone(item)
    score = 0
    if zone == "OBJECT_REGISTER": score += 100; reasons.append("официальная объектная таблица")
    if item.get("general_plan_explication"): score += 100; reasons.append("экспликация генплана")
    if item.get("general_plan_field"): score += 80; reasons.append("позиция на поле генплана")
    if item.get("source_kind") == "xml" and item.get("parameter_code") == "OBJECT_ENTRY": score += 95; reasons.append("объектный узел XML")
    if zone == "OBJECT_TEP": score += 75; reasons.append("объектная строка ТЭП")
    if item.get("parameter_code") == "OBJECT_ENTRY" and str(item.get("document_type") or "") == "ПЗ": score += 70; reasons.append("реестр объектов ПЗ")
    if str(item.get("genplan_position") or "").strip(): score += 30; reasons.append("позиция по генплану")
    if zone == "NARRATIVE": score += 10; reasons.append("текстовое упоминание")
    return score, reasons


def annotate_findings(findings: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    audit=[]
    for idx,item in enumerate(findings):
        if str(item.get("parameter_code") or "") not in {"OBJECT_ENTRY","OBJECT_CANDIDATE"}: continue
        score,reasons=evidence_score(item)
        life=lifecycle_status(item)
        item["trusted_zone"]=classify_zone(item)
        item["object_lifecycle_status"]=life
        item["object_trust_score"]=score
        item["object_trust_reasons"]=reasons
        audit.append({"candidate_id":idx,"name":item.get("value_text") or item.get("object_hint"),"document":item.get("document"),"page":item.get("page"),"zone":item["trusted_zone"],"lifecycle":life,"score":score,"decision":"trusted" if score>=80 and life in {"Проектируемый","Реконструируемый"} else "candidate","reasons":"; ".join(reasons)})
    return audit


def filter_registry(records: list[dict[str, Any]], findings: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence_by_pos: dict[str,list[dict[str,Any]]] = {}
    evidence_by_name: dict[str,list[dict[str,Any]]] = {}
    for item in findings:
        if str(item.get("parameter_code") or "") not in {"OBJECT_ENTRY","OBJECT_CANDIDATE"}: continue
        pos=str(item.get("genplan_position") or "").strip()
        name=normalize_text(item.get("value_text") or item.get("object_hint") or "")
        if pos: evidence_by_pos.setdefault(pos,[]).append(item)
        if name: evidence_by_name.setdefault(name,[]).append(item)
    trusted=[]; candidates=[]
    for row in records:
        pos=str(row.get("Позиция по ГП") or row.get("Позиция") or "").strip()
        name=normalize_text(row.get("Наименование объекта") or row.get("Объект") or "")
        ev=evidence_by_pos.get(pos,[]) if pos else evidence_by_name.get(name,[])
        max_score=max([int(x.get("object_trust_score") or -100) for x in ev] or [-100])
        lives={str(x.get("object_lifecycle_status") or "Не определён") for x in ev}
        life="Проектируемый" if "Проектируемый" in lives else ("Реконструируемый" if "Реконструируемый" in lives else next(iter(lives),"Не определён"))
        raw_name = str(row.get("Наименование объекта") or row.get("Объект") or "")
        registry_reasons = name_rejection_reasons(raw_name)
        service=bool(FILEISH_RE.search(raw_name) or registry_reasons)
        if pos and is_date_like_position(pos):
            service = True
            registry_reasons = list(registry_reasons) + ["позиция похожа на календарную дату"]
        hard_blocked=any(bool(x.get("hard_object_gate_blocked") or x.get("structure_guard_blocked")) for x in ev) and not any(int(x.get("object_trust_score") or -1000) >= 80 for x in ev)
        confirmed_sources=int(row.get("Количество источников") or row.get("Подтверждений") or 0)
        gp_explication = any(bool(x.get("general_plan_explication")) for x in ev)
        explicit_project = life in {"Проектируемый","Реконструируемый"}
        # General-plan rows must never be lost merely because lifecycle text was
        # absent. Unknown GP-only rows remain candidates; cross-confirmed rows are
        # trusted once another independent source confirms the same object.
        is_trusted=(not service and not hard_blocked and (
            (explicit_project and (max_score>=80 or (max_score>=60 and confirmed_sources>=2)))
            or (gp_explication and confirmed_sources>=2 and max_score>=80 and life not in {"Существующий","Перспективный"})
        ))
        row=dict(row); row["Статус проектирования"]=life; row["Доверие к объекту"]=max_score; row["Подтвержденный реестр"]=is_trusted
        if registry_reasons:
            row["Причина исключения из подтвержденного реестра"] = "; ".join(registry_reasons)
        (trusted if is_trusted else candidates).append(row)
    return trusted,candidates
