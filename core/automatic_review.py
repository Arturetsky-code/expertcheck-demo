
from __future__ import annotations
from collections import Counter
import re
from pathlib import Path
from typing import Any
from .normalization import normalize_text
from .checklist_engine import ChecklistEngine
from .pp87_compliance import PP87Compliance

SECTION_ALIASES={
 "ПЗ":("пояснительн запис","раздел 1"),
 "ПЗУ":("пзу","генеральн план","схема планировочн"),
 "АР":("архитектур"),
 "КР":("конструктив","кж","км"),
 "ТХ":("технологическ"),
 "ИОС1":("иос1","электроснаб","эс","эом"),
 "ИОС2":("иос2","водоснаб","водоотвед","вк"),
 "ИОС4":("иос4","отоплен","вентиляц","ов"),
 "ПОС":("пос","организац строител"),
 "ООС":("оос","охрана окружа","овос"),
 "ПБ":("пожарн безопас"),
 "СМ":("смет"),
 "ГТС":("гтс","гидротех","хвостохранилищ","дамб","плотин"),
}

def canonical_section(value:str)->str:
    low=normalize_text(value)
    words=set(re.findall(r"[а-яa-z0-9]+",low,re.I))
    for code,tokens in SECTION_ALIASES.items():
        if low==normalize_text(code):
            return code
        for token in tokens:
            nt=normalize_text(token)
            if (len(nt)<=3 and nt in words) or (len(nt)>3 and nt in low):
                return code
    return str(value or "").strip()

class AutomaticProjectReview:
    """Builds and executes a project-specific checklist programme automatically.

    It runs deterministic/semantic-preparation stages. External AI can later enrich
    SEMANTIC items without requiring the user to map checklists to sections manually.
    """
    def __init__(self, knowledge_root:str|Path):
        root=Path(knowledge_root)
        self.checklists=ChecklistEngine(root/"checklist_catalog.json")
        self.pp87=PP87Compliance(root)

    def document_inventory(self,documents:list[dict[str,Any]])->dict[str,list[dict[str,Any]]]:
        inv={}
        for d in documents:
            raw=" ".join(str(d.get(k) or "") for k in ("Раздел","Тип документа","document_type","family","Файл"))
            code=canonical_section(raw)
            inv.setdefault(code,[]).append(d)
        return inv

    def programme(self,documents:list[dict[str,Any]],project_context:dict[str,Any]|None=None)->list[dict[str,Any]]:
        inv=self.document_inventory(documents)
        present=set(inv)
        rows=[]
        for source_file in self.checklists.checklist_files():
            primary=canonical_section(self.checklists.primary_section(source_file))
            if primary not in present:
                continue
            rows.append({
              "checklist":source_file,"section":primary,
              "document_count":len(inv.get(primary,[])),
              "reason":"Раздел обнаружен в загруженном комплекте",
              "automatic":True
            })
        # PP87 profile is recorded in the programme even when there is no corporate checklist.
        pp=self.pp87.checklist_contract(project_context or {})
        for profile in pp.get("applicable_profiles") or []:
            rows.append({
              "checklist":"ПП №87","section":profile.get("structure_ref") or profile.get("project_type"),
              "document_count":0,"reason":profile.get("label"),"automatic":True,"pp87_profile":profile
            })
        return rows

    def execute(self,documents:list[dict[str,Any]],comparisons:list[dict[str,Any]],findings:list[dict[str,Any]],
                project_context:dict[str,Any]|None=None)->dict[str,Any]:
        inv=self.document_inventory(documents)
        programme=self.programme(documents,project_context)
        all_results=[]
        runs=[]
        for p in programme:
            if p.get("checklist")=="ПП №87":
                continue
            section=p["section"]
            docs=inv.get(section,[])
            if not docs:
                continue
            results=self.checklists.evaluate_with_pp87(
                docs,comparisons,findings,source_file=p["checklist"],section=section,include_practice=False
            )
            # Headings are kept in raw result but excluded from aggregate statistics.
            for r in results:
                r["automatic_review"]=True
                r["automatic_checklist"]=p["checklist"]
                r["automatic_section"]=section
            all_results.extend(results)
            runs.append({"checklist":p["checklist"],"section":section,"results":len(results),"documents":len(docs)})
        actionable=[x for x in all_results if not x.get("is_heading")]
        # Expert-practice search is expensive and most useful for problems, not passed checks.
        # Enrich only the first actionable issues, prioritising negative and uncertain results.
        attention=[x for x in actionable if x.get("status") in {"Нет","Требует проверки","Нет данных"}]
        for r in attention[:60]:
            compiled=r.get("compiled_rule") or {}
            rule_type=compiled.get("rule_type") or ""
            fam=["MISSING_INFORMATION"] if rule_type in {"presence","mandatory_document"} else (
                ["CROSS_SECTION_MISMATCH"] if rule_type=="numeric_crosscheck" else ["INSUFFICIENT_JUSTIFICATION"]
            )
            r["expert_practice_context"]=self.checklists.expert_practice.risk_from_evidence(
                str(r.get("question") or ""),str(r.get("automatic_section") or ""),"",fam,r.get("normative_context") or []
            )
        counts=Counter(str(x.get("status") or "Нет данных") for x in actionable)
        semantic_pending=sum(1 for x in actionable if (x.get("execution_class") in {"SEMANTIC","EXPERT"} and x.get("status") in {"Требует проверки","Нет данных"}))
        return {
          "programme":programme,"runs":runs,"results":all_results,
          "summary":{
            "checklists_run":len(runs),"checks":len(actionable),
            "yes":counts.get("Да",0),"no":counts.get("Нет",0),
            "review":counts.get("Требует проверки",0),"no_data":counts.get("Нет данных",0),
            "semantic_pending_ai":semantic_pending,
            "automatic":True
          }
        }
