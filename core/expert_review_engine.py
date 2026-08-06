from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json
import re


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", []):
            return str(value)
    return ""


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _level(score: int) -> str:
    if score >= 70: return "Высокий"
    if score >= 40: return "Средний"
    if score > 0: return "Низкий"
    return "Недостаточно данных"


def load_risk_scenarios(path: str | Path | None = None) -> list[dict[str, Any]]:
    target = Path(path) if path else Path(__file__).resolve().parents[1] / "knowledge" / "gge_risk_scenarios.json"
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _scenario_match(blob: str, scenario: dict[str, Any]) -> tuple[int, list[str]]:
    triggers = scenario.get("triggers") or {}
    matched=[]; score=0
    status_hits=0; keyword_hits=0
    for token in triggers.get("statuses") or []:
        norm=_norm(token)
        if norm and norm in blob:
            matched.append(str(token)); status_hits += 1
    for token in triggers.get("keywords") or []:
        norm=_norm(token)
        if norm and norm in blob:
            matched.append(str(token)); keyword_hits += 1
            score += 42 if " " in norm else (6 if len(norm) <= 4 else 24)
    # A scenario must have a substantive keyword match; generic status words alone are insufficient.
    if keyword_hits == 0:
        return 0, []
    score += min(20, status_hits * 10)
    return min(100, score), matched


def _enrich(risk: dict[str, Any], scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    blob=_norm(" ".join(str(risk.get(k) or "") for k in ("category","object","parameter","finding","possible_remark","sources")))
    best=None; best_score=0; best_tokens=[]
    for scenario in scenarios:
        score,tokens=_scenario_match(blob,scenario)
        if score>best_score:
            best,best_score,best_tokens=scenario,score,tokens
    if not best or best_score < 22:
        risk.update({"scenario_id":"","scenario_title":"","recurrence":0,"analog_projects":[],"knowledge_match_score":0,"matched_signals":[]})
        return risk
    recurrence=int(best.get("recurrence") or 0)
    base=max(int(risk.get("score") or 0), int(best.get("severity") or 0))
    evidence_bonus=8 if risk.get("sources") else 0
    recurrence_bonus=min(12, recurrence*2)
    risk["score"]=min(100,base+evidence_bonus+recurrence_bonus)
    risk["level"]=_level(risk["score"])
    risk["knowledge_category"]=best.get("category") or ""
    if risk.get("origin") == "CrossCheck Engine":
        risk["category"]=best.get("category") or risk.get("category")
    risk["scenario_id"]=best.get("scenario_id")
    risk["scenario_title"]=best.get("title")
    risk["recurrence"]=recurrence
    risk["analog_projects"]=best.get("analogs") or []
    risk["knowledge_match_score"]=best_score
    risk["matched_signals"]=best_tokens
    risk["possible_remark"]=best.get("possible_remark") or risk.get("possible_remark")
    risk["recommendation"]=best.get("recommendation") or risk.get("recommendation")
    return risk


def _possible_remark(kind: str, object_name: str, parameter: str) -> str:
    obj=object_name or "объекту"
    if kind=="object_gap": return f"Не обеспечено соответствие состава проектируемых объектов между разделами проектной документации по позиции «{obj}»."
    if kind=="mismatch": return f"Не обеспечена согласованность технико-экономического показателя «{parameter}» по объекту «{obj}» между разделами проектной документации."
    if kind=="insufficient": return f"Не представлены достаточные и однозначные сведения по показателю «{parameter}» объекта «{obj}» для подтверждения принятого проектного решения."
    if kind=="checklist": return f"Не подтверждено выполнение контрольного требования по пункту «{parameter}»."
    return "Требуется дополнительная проверка согласованности и полноты проектных решений."


def build_expert_risks(comparisons:list[dict[str,Any]],object_rows:list[dict[str,Any]]|None=None,checklist_results:list[dict[str,Any]]|None=None,scenario_path:str|Path|None=None)->list[dict[str,Any]]:
    risks=[]; object_rows=object_rows or []; checklist_results=checklist_results or []
    scenarios=load_risk_scenarios(scenario_path)
    for index,row in enumerate(comparisons):
        status=_text(row,"status","Статус","result","Результат").lower()
        if not any(t in status for t in ("расхожд","конфликт","недостат","требует","отсутств","не подтвержд","нет данных")): continue
        obj=_text(row,"object","Объект","object_name")
        parameter=_text(row,"parameter_name","parameter","Параметр","parameter_code") or "показатель"
        priority=_text(row,"priority","Приоритет") or "Средний"
        kind="mismatch" if any(t in status for t in ("расхожд","конфликт")) else "insufficient"
        score=int(row.get("engineering_risk_score") or 0) or (52 if kind=="mismatch" else 34)
        if priority.lower().startswith("выс"): score+=18
        elif priority.lower().startswith("низ"): score-=8
        sources=row.get("sources") or row.get("Источники") or row.get("sections") or row.get("document_values") or ""
        risk={"risk_id":_text(row,"comparison_id","rule_id","check_code") or f"R-CMP-{index+1:04d}","level":_level(min(100,score)),"score":min(100,score),"category":"Межраздельная согласованность" if kind=="mismatch" else "Полнота и доказательность","object":obj,"parameter":parameter,"finding":_text(row,"explanation","Пояснение") or f"Результат проверки: {_text(row,'status','Статус','result','Результат')}","possible_remark":_possible_remark(kind,obj,parameter),"recommendation":"Проверить исходные страницы и унифицировать сведения во всех связанных разделах." if kind=="mismatch" else "Дополнить сведения либо подтвердить показатель однозначным источником с указанием объекта и страницы.","sources":sources,"origin":"CrossCheck Engine","evidence_strength":"Высокая" if sources else "Средняя"}
        risks.append(_enrich(risk,scenarios))
    for index,row in enumerate(object_rows):
        included=bool(row.get("Включить в состав проекта",row.get("include",False)))
        decision=_text(row,"Решение Object Intelligence","object_intelligence_decision","decision").lower()
        status=_text(row,"Статус проектирования","design_status","status").lower()
        name=_text(row,"Наименование","Объект","name","value_text")
        if included and decision in {"review","blocked","context"}:
            risk={"risk_id":f"R-OBJ-{index+1:04d}","level":"Средний","score":68 if decision=="blocked" else 48,"category":"Состав проекта","object":name,"parameter":"Принадлежность к составу проекта","finding":f"Позиция включена пользователем, хотя решение Core: {decision or 'не определено'}; статус: {status or 'не определён'}.","possible_remark":_possible_remark("object_gap",name,""),"recommendation":"Проверить официальный источник: состав сложного объекта, XML или экспликацию генплана.","sources":row.get("Основание включения") or row.get("Канонический источник") or "","origin":"Project Engine","evidence_strength":"Средняя"}
            risks.append(_enrich(risk,scenarios))
    for index,row in enumerate(checklist_results):
        status=_text(row,"status","Соответствие","result").lower()
        if status not in {"нет","частично","требует проверки","нет данных","не соответствует"}: continue
        item_no=_text(row,"item_no","Позиция","position"); question=_text(row,"question","Вопрос","Позиция по чек-листу")
        risk={"risk_id":f"R-CHK-{index+1:04d}","level":"Средний" if status in {"нет","не соответствует"} else "Низкий","score":58 if status in {"нет","не соответствует"} else 32,"category":"Чек-лист раздела","object":"","parameter":f"{item_no} {question}".strip(),"finding":_text(row,"evidence","Обоснование") or f"Результат пункта: {status}","possible_remark":_possible_remark("checklist","",f"{item_no} {question}".strip()),"recommendation":"Открыть доказательства по пункту, дополнить раздел и повторно запустить проверку чек-листа.","sources":_text(row,"sources","Источники"),"origin":"Checklist Engine","evidence_strength":"Средняя"}
        risks.append(_enrich(risk,scenarios))
    unique={}
    for risk in risks:
        key=(risk.get("scenario_id") or risk["category"],risk["object"].lower(),risk["parameter"].lower())
        if key not in unique or int(risk["score"])>int(unique[key]["score"]): unique[key]=risk
    return sorted(unique.values(),key=lambda x:(-int(x["score"]),x["category"],x["object"]))


def summarize_risks(risks:list[dict[str,Any]])->dict[str,Any]:
    counts=Counter(str(x.get("level") or "Недостаточно данных") for x in risks)
    return {"total":len(risks),"high":counts.get("Высокий",0),"medium":counts.get("Средний",0),"low":counts.get("Низкий",0),"categories":dict(Counter(str(x.get("category") or "Прочее") for x in risks)),"matched_knowledge":sum(1 for x in risks if x.get("scenario_id"))}
