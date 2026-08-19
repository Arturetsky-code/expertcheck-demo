
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from .normalization import normalize_text

SECTION_ALIASES={
 "ПЗ":("пз","пояснительная записка","пояснительн"),
 "ПЗУ":("пзу","пзу1","пзу2","генеральный план","генплан","схема планировочной организации"),
 "АР":("ар","ар1","ар2","архитектурные решения","архитектур"),
 "КР":("кр","кж","км","конструктивные решения","конструктив"),
 "ТХ":("тх","тх1","тх2","технологические решения","технологическ"),
 "ИОС1":("иос1","иос1.1","эс","эом","система электроснабжения","электроснаб"),
 "ИОС2":("иос2","вк","водоснабжение","водоотведение","водоснаб","водоотвед"),
 "ИОС3":("иос3","канализация"),
 "ИОС4":("иос4","ов","отопление","вентиляция","отоплен","вентиляц"),
 "ИОС5":("иос5","сс","связь","автоматизация","автоматизац"),
 "ИОС6":("иос6","газоснабжение","газоснаб"),
 "ИОС7":("иос7","технологические решения"),
 "ПОС":("пос","проект организации строительства","организац строител"),
 "ПОД":("под","проект организации работ по сносу"),
 "ПБ":("пб","пожарная безопасность","пожарн безопас"),
 "ООС":("оос","моос","овос","охрана окружающей среды","охрана окружа"),
 "ОДИ":("оди","доступность инвалидов"),
 "СМ":("см","сметная документация","сд","смет"),
 "ГОЧС":("гочс","чрезвычайные ситуации"),
 "ИГДИ":("игди","инженерно-геодезические"),
 "ИГИ":("иги","инженерно-геологические"),
 "ИГМИ":("игми","инженерно-гидрометеорологические"),
 "ИЭИ":("иэи","инженерно-экологические"),
 "ГТС":("гтс","гидротехнические сооружения","гидротех","хвостохранилищ","дамб","плотин"),
}

CHECKLIST_ROUTE_HINTS={
 "Чек-лист № 1_Гидротехника(7).xlsx":"ГТС",
 "Чек-лист № 2_Электрика(4).xlsx":"ИОС1",
 "Чек-лист № 3_Сметная документация(6).xlsx":"СМ",
 "Чек-лист № 5_Автоматизация(5).xlsx":"ИОС5",
 "Чек-лист № 6_КЖ КМ.xlsx":"КР",
 "Чек-лист № 7_МООС ОВОС.xlsx":"ООС",
 "Чек-лист № 10 ПОС.xlsx":"ПОС",
 "Чек-лист № 11 Водоснабжение.xlsx":"ИОС2",
 "Чек-лист № 12 Отопление и вентиляция.xlsx":"ИОС4",
 "Чек-лист № 13_Ген.план(20260805-134504).xlsx":"ПЗУ",
}

def canonical_section(value:str)->str:
    low=normalize_text(value)
    compact=re.sub(r"[^а-яa-z0-9.]","",low)
    words=set(re.findall(r"[а-яa-z0-9.]+",low,re.I))
    # Exact code/part notation first.
    for code in ("ИОС1","ИОС2","ИОС3","ИОС4","ИОС5","ИОС6","ИОС7","ПЗУ","АР","КР","ТХ","ПОС","ПОД","ПБ","ООС","ОДИ","СМ","ГОЧС","ИГДИ","ИГИ","ИГМИ","ИЭИ","ПЗ"):
        c=normalize_text(code)
        if compact.startswith(c.lower()) or low==c:
            return code
    for code,tokens in SECTION_ALIASES.items():
        for token in tokens:
            nt=normalize_text(token)
            if len(nt)<=3:
                if nt in words:return code
            elif nt in low:
                return code
    return str(value or "").strip() or "Не определён"

class ChecklistRoutingEngine:
    def __init__(self,checklist_engine):
        self.engine=checklist_engine

    def route(self,documents:list[dict[str,Any]])->dict[str,Any]:
        inventory={}
        for d in documents:
            raw=" ".join(str(d.get(k) or "") for k in ("Раздел","Тип документа","document_type","family","Файл"))
            code=canonical_section(raw)
            inventory.setdefault(code,[]).append(d)
        routes=[];covered=set()
        for f in self.engine.checklist_files():
            target=CHECKLIST_ROUTE_HINTS.get(f)
            if not target:
                target=canonical_section(self.engine.primary_section(f))
            docs=inventory.get(target,[])
            if docs:
                routes.append({"checklist":f,"section":target,"documents":docs,"document_count":len(docs),"reason":"Маршрутизировано по каноническому разделу"})
                covered.add(target)
        recognized={k for k in inventory if k!="Не определён"}
        uncovered=sorted(recognized-covered)
        return {
          "inventory":inventory,"routes":routes,"covered_sections":sorted(covered),
          "uncovered_sections":uncovered,
          "unknown_documents":[d for d in inventory.get("Не определён",[])],
        }
