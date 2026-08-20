
from __future__ import annotations
from collections import Counter
import re
from pathlib import Path
from typing import Any
from .normalization import normalize_text
from .checklist_engine import ChecklistEngine
from .pp87_compliance import PP87Compliance
from .checklist_routing import ChecklistRoutingEngine, canonical_section
from .checklist_verification import qualify_checklist_results

class AutomaticProjectReview:
    """Builds and executes a project-specific checklist programme automatically.

    It runs deterministic/semantic-preparation stages. External AI can later enrich
    SEMANTIC items without requiring the user to map checklists to sections manually.
    """
    def __init__(self, knowledge_root:str|Path):
        root=Path(knowledge_root)
        self.checklists=ChecklistEngine(root/"checklist_catalog.json")
        self.pp87=PP87Compliance(root)
        self.router=ChecklistRoutingEngine(self.checklists)

    def document_inventory(self,documents:list[dict[str,Any]])->dict[str,list[dict[str,Any]]]:
        return self.router.route(documents)["inventory"]

    def programme(self,documents:list[dict[str,Any]],project_context:dict[str,Any]|None=None)->list[dict[str,Any]]:
        routing=self.router.route(documents)
        inv=routing["inventory"]
        rows=[]
        for route in routing["routes"]:
            rows.append({
              "checklist":route["checklist"],"section":route["section"],
              "document_count":route["document_count"],
              "reason":route["reason"],"automatic":True
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
        all_results=qualify_checklist_results(all_results)
        actionable=[x for x in all_results if not x.get("is_heading")]
        # Expert-practice search is expensive and most useful for problems, not passed checks.
        # Enrich only the first actionable issues, prioritising negative and uncertain results.
        attention=[x for x in actionable if x.get("status") in {"Нет","Требует проверки","Нет данных","Не проверено системой"}]
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
        semantic_pending=sum(1 for x in actionable if (x.get("execution_class") in {"SEMANTIC","EXPERT"} and x.get("status") in {"Требует проверки","Нет данных","Не проверено системой"}))
        routing=self.router.route(documents)
        return {
          "programme":programme,"runs":runs,"results":all_results,
          "routing":{
            "covered_sections":routing["covered_sections"],
            "uncovered_sections":routing["uncovered_sections"],
            "unknown_document_count":len(routing["unknown_documents"])
          },
          "summary":{
            "checklists_run":len(runs),"checks":len(actionable),
            "yes":counts.get("Да",0),"no":counts.get("Нет",0),
            "review":counts.get("Требует проверки",0),"no_data":counts.get("Нет данных",0),"unsupported":counts.get("Не проверено системой",0),
            "semantic_pending_ai":semantic_pending,
            "verified_completed":sum(1 for x in actionable if x.get("verification_kind") in {"VERIFIED_OK","PROJECT_FINDING"}),
            "system_limitations":sum(1 for x in actionable if x.get("verification_kind")=="SYSTEM_LIMITATION"),
            "review_questions":sum(1 for x in actionable if x.get("verification_kind")=="REVIEW_QUESTION"),
            "automatic_coverage_pct":round(100*sum(1 for x in actionable if x.get("verification_kind") in {"VERIFIED_OK","PROJECT_FINDING"})/max(1,len(actionable)),1),
            "automatic":True
          }
        }
