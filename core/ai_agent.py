from __future__ import annotations
import json, os, re, urllib.error, urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Iterable

@dataclass
class AgentObservation:
    observation_id: str; agent: str; severity: str; title: str; explanation: str
    recommendation: str; evidence: list[dict[str, Any]]; confidence: float

@dataclass
class AgentReport:
    mode: str; readiness: int; observations: list[AgentObservation]; limitations: list[str]
    def to_dict(self):
        return {"mode":self.mode,"readiness":self.readiness,"observations":[asdict(x) for x in self.observations],"limitations":self.limitations}

def _records(value):
    if value is None:return []
    if hasattr(value,"to_dict"):
        try:return value.to_dict("records")
        except TypeError:pass
    return [x for x in value if isinstance(x,dict)] if isinstance(value,list) else []

def _first(row,names,default=""):
    for name in names:
        value=row.get(name)
        if value not in (None,"",[],{}):return value
    return default

def _status_group(value):
    text=str(value or "").upper()
    if any(x in text for x in ("КРИТ","РАСХОЖ","КОНФЛИКТ","ОШИБ")):return "high"
    if any(x in text for x in ("УТОЧ","НЕДОСТАТОЧ","НЕ НАЙД","ТРЕБУЕТ")):return "medium"
    return "low"

def build_grounded_snapshot(docs,registry,passports,comparisons,findings,*,registry_confirmed,checklist_runs=None):
    doc_rows,reg_rows,passport_rows,comparison_rows,finding_rows=map(_records,(docs,registry,passports,comparisons,findings))
    objects=[{"evidence_id":f"OBJ-{i:04d}","position":_first(r,["Позиция по ГП","position","Позиция"]),"name":_first(r,["Наименование объекта","name","Объект"]),"object_type":_first(r,["Тип объекта","object_type_name","object_type"]),"design_status":_first(r,["Статус проектирования","design_status"]),"source_count":_first(r,["Количество источников","source_count"],0),"confidence":_first(r,["Доверие к объекту","confidence"],None)} for i,r in enumerate(reg_rows,1)]
    pp=[]
    for i,r in enumerate(passport_rows,1):
        pp.append({"evidence_id":f"PASS-{i:04d}","position":r.get("position"),"name":r.get("name"),"object_type":r.get("object_type_name"),"completeness":r.get("passport_completeness"),"characteristics":[{"parameter":_first(ch,["parameter_name","parameter","Характеристика"]),"unit":_first(ch,["unit","Ед. изм."]),"status":_first(ch,["status","Статус"]),"values":_first(ch,["values_by_section","Значения по разделам"]),"confidence":ch.get("confidence")} for ch in (r.get("characteristics") or [])[:60] if isinstance(ch,dict)]})
    cmp=[{"evidence_id":f"CMP-{i:05d}","object":_first(r,["object_name","object","Объект","Наименование объекта"]),"position":_first(r,["position","Позиция","Позиция по ГП"]),"parameter":_first(r,["parameter_name","parameter","Характеристика"]),"status":_first(r,["status","Статус"]),"values":_first(r,["values_by_section","values","Значения"]),"sources":_first(r,["sources","Источники"]),"explanation":_first(r,["explanation","Пояснение"])} for i,r in enumerate(comparison_rows,1)]
    docs2=[{"evidence_id":f"DOC-{i:04d}","file":_first(r,["Файл","Имя файла","filename","name"]),"section":_first(r,["Раздел","Тип документа","document_type","family"]),"pages":_first(r,["Страниц","pages","page_count"]),"status":_first(r,["Статус","status"])} for i,r in enumerate(doc_rows,1)]
    fnd=[{"evidence_id":f"FND-{i:05d}","parameter":_first(r,["parameter_name","parameter_code","Характеристика"]),"value":_first(r,["normalized_value","value","Значение"]),"unit":_first(r,["unit","Ед. изм."]),"section":_first(r,["section","Раздел"]),"page":_first(r,["page","Страница"]),"object":_first(r,["object_name","object","Объект"]),"confidence":r.get("confidence")} for i,r in enumerate(finding_rows[:300],1)]
    return {"registry_confirmed":bool(registry_confirmed),"documents":docs2,"objects":objects,"passports":pp,"comparisons":cmp,"findings":fnd,"checklist_runs":checklist_runs or {}}

def run_local_agents(snapshot):
    observations=[];seq=1
    def add(agent,severity,title,explanation,recommendation,evidence,confidence):
        nonlocal seq
        observations.append(AgentObservation(f"AI-{seq:04d}",agent,severity,title,explanation,recommendation,evidence,confidence));seq+=1
    if not snapshot.get("registry_confirmed"):
        add("Object Analyst","high","Состав объектов не подтверждён","ИИ-анализ не считает автоматический перечень объектов достоверным до прохождения Quality Gate.","Проверьте кандидатов в разделе «Объекты» и подтвердите эталонный реестр.",[],1.0)
    for obj in snapshot.get("objects") or []:
        name=str(obj.get("name") or "").strip();source_count=obj.get("source_count") or 0;confidence=obj.get("confidence")
        if re.search(r"\.(pdf|xml|sig|zip|dwg|xlsx?)\b",name,re.I) or re.search(r"\b(раздел|подраздел|том|часть|ведомость|содержание|пояснительная записка)\b",name,re.I):
            add("Object Analyst","high","В подтверждённом реестре обнаружена служебная сущность",f"Позиция «{name}» похожа на файл, раздел или служебную строку, а не на объект проектирования.","Исключите позицию из реестра и используйте её как регрессионный пример для фильтрации.",[obj],0.98)
        elif not obj.get("position") and int(source_count or 0)<2:
            add("Object Analyst","medium","Объект имеет слабое подтверждение",f"Объект «{name or 'без наименования'}» не имеет позиции и подтверждён менее чем двумя источниками.","Проверьте, является ли сущность самостоятельным объектом, оборудованием или текстовым упоминанием.",[obj],0.86)
        elif confidence is not None:
            try:
                n=float(str(confidence).replace(',','.').replace('%',''));n=n/100 if n>1 else n
                if n<0.65:add("Object Analyst","medium","Низкая уверенность в объекте",f"Для объекта «{name}» уровень доверия ниже рекомендуемого порога.","Проверьте происхождение объекта и его статус проектирования.",[obj],0.9)
            except (TypeError,ValueError):pass
    for passport in snapshot.get("passports") or []:
        try:c=float(passport.get("completeness") or 0)
        except (TypeError,ValueError):c=0
        if c and c<50:add("Project Analyst","medium","Цифровой паспорт заполнен недостаточно",f"Паспорт объекта «{passport.get('name') or 'без наименования'}» заполнен на {c:.0f}%.","Проверьте наличие профильных разделов и привязку ожидаемых ТЭП к этому объекту.",[passport],0.93)
    grouped={}
    for comparison in snapshot.get("comparisons") or []:
        key=(str(comparison.get("object") or ""),str(comparison.get("parameter") or ""));grouped.setdefault(key,[]).append(comparison);severity=_status_group(comparison.get("status"))
        if severity in {"high","medium"}:add("CrossCheck Analyst",severity,f"{comparison.get('object') or 'Объект'} · {comparison.get('parameter') or 'характеристика'}",str(comparison.get("explanation") or comparison.get("status") or "Результат требует инженерной проверки."),"Подтвердите привязку объекта, строки таблицы, единицы измерения и редакции документа.",[comparison],0.9 if severity=="high" else 0.82)
    for key,rows in grouped.items():
        if len(rows)>1 and len({json.dumps(x.get("values"),ensure_ascii=False,sort_keys=True,default=str) for x in rows})>1:add("CrossCheck Analyst","medium","Для одной характеристики сформировано несколько наборов значений",f"У объекта «{key[0]}» по характеристике «{key[1]}» имеются неоднозначные результаты сопоставления.","Проверьте дубли объектов, позиции генплана и границы строк таблиц до формирования замечания.",rows[:4],0.85)
    high=sum(x.severity=="high" for x in observations);medium=sum(x.severity=="medium" for x in observations)
    readiness=max(0,min(100,100-high*12-medium*4-(0 if snapshot.get("registry_confirmed") else 25)))
    return AgentReport("local-grounded",readiness,observations,["Локальные агенты анализируют только структурированные результаты Core и не перечитывают исходный PDF.","Агент не изменяет реестр, ТЭП, статусы чек-листов или замечания без решения пользователя."])

def _snapshot_for_model(snapshot,max_chars=60000):
    text=json.dumps(snapshot,ensure_ascii=False,default=str,separators=(",",":"))
    if len(text)<=max_chars:return text
    reduced=dict(snapshot);reduced["findings"]=(reduced.get("findings") or [])[:80];reduced["comparisons"]=(reduced.get("comparisons") or [])[:120];reduced["passports"]=(reduced.get("passports") or [])[:80]
    return json.dumps(reduced,ensure_ascii=False,default=str,separators=(",",":"))[:max_chars]

def openai_available(api_key=None):return bool(api_key or os.getenv("OPENAI_API_KEY"))

def ask_openai_grounded(snapshot,question,*,api_key=None,model="gpt-5-mini",timeout=90):
    key=api_key or os.getenv("OPENAI_API_KEY")
    if not key:raise RuntimeError("OPENAI_API_KEY не настроен")
    payload={"model":model,"store":False,"instructions":"Ты — инженерный агент ExpertCheck. Отвечай только по переданной структурированной модели проекта. Не выдумывай сведения. Каждое утверждение сопровождай evidence_id. Не изменяй результаты Core. При неоднозначности требуй подтверждения инженера. Ответ на русском языке.","input":f"МОДЕЛЬ ПРОЕКТА:\n{_snapshot_for_model(snapshot)}\n\nВОПРОС:\n{question}"}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:data=json.loads(response.read().decode())
    except urllib.error.HTTPError as e:raise RuntimeError(f"OpenAI API: HTTP {e.code}: {e.read().decode(errors='replace')[:800]}") from e
    except urllib.error.URLError as e:raise RuntimeError(f"OpenAI API недоступен: {e.reason}") from e
    if data.get("output_text"):return str(data["output_text"])
    chunks=[c["text"] for item in data.get("output") or [] for c in item.get("content") or [] if c.get("type")=="output_text" and c.get("text")]
    if not chunks:raise RuntimeError("OpenAI API вернул ответ без текста")
    return "\n".join(chunks)

def answer_locally(snapshot,question):
    q=question.lower()
    if any(x in q for x in ("лишн","не объект","файл","перечень объект")):
        suspects=[f"- {o['evidence_id']}: {o.get('name')}" for o in snapshot.get("objects") or [] if re.search(r"\.(pdf|xml|sig|zip|xlsx?)\b|\b(раздел|подраздел|том|ведомость|содержание)\b",str(o.get("name") or ""),re.I)]
        return "Подозрительные позиции в подтверждённом реестре:\n"+("\n".join(suspects) if suspects else "не обнаружены по формальным признакам.")
    if any(x in q for x in ("расхожд","требует внимания","проблем")):
        rows=[x for x in snapshot.get("comparisons") or [] if _status_group(x.get("status")) in {"high","medium"}]
        return "\n".join(f"- {x['evidence_id']}: {x.get('object') or 'Объект'} · {x.get('parameter') or 'характеристика'} — {x.get('status')}" for x in rows[:20]) if rows else "В структурированных результатах нет расхождений или результатов с недостаточным подтверждением."
    if any(x in q for x in ("объект","реестр")):
        rows=snapshot.get("objects") or []
        return f"В подтверждённом реестре {len(rows)} позиций.\n"+"\n".join(f"- {x['evidence_id']}: {x.get('position') or '—'} · {x.get('name') or 'без наименования'}" for x in rows[:30])
    return "Локальный режим показывает реестр, подозрительные позиции и результаты, требующие внимания. Для свободного диалога настройте OPENAI_API_KEY."
