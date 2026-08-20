from __future__ import annotations
from typing import Any
from .verification_core import annotate_rows, domain_summary

DOMAIN_LABELS={"assignment":"Задание на проектирование","normative":"НТД","checklist":"Чек-листы","comparison":"Межраздельная сверка"}


def _assignment_plan(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for r in annotate_rows(rows,"assignment"):
        out.append({
            "plan_id":r.get("requirement_id") or f"ASSIGN-{len(out)+1:03d}","domain":"assignment",
            "check":r.get("requirement_text") or r.get("requirement") or "Требование Задания",
            "scope":r.get("requirement_scope") or (r.get("evidence_contract_v2") or {}).get("scope"),
            "method":(r.get("evidence_contract_v2") or {}).get("check_method") or r.get("requirement_type"),
            "expected_sections":(r.get("evidence_contract_v2") or {}).get("expected_sections") or [],
            "verification_kind":r.get("verification_kind"),"verification_state":r.get("verification_state"),
            "source_id":r.get("requirement_id"),
        })
    return out


def _normative_plan(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for r in annotate_rows(rows,"normative"):
        out.append({
            "plan_id":r.get("requirement_id") or f"NORM-{len(out)+1:03d}","domain":"normative",
            "check":f"{r.get('source') or r.get('reference') or 'НТД'} {r.get('paragraph') or r.get('clause') or ''}".strip(),
            "scope":r.get("topic") or "Проект","method":r.get("check_kind") or "SEMANTIC",
            "expected_sections":(r.get("evidence_contract") or {}).get("sections") or [],
            "verification_kind":r.get("verification_kind"),"verification_state":r.get("verification_state"),
            "source_id":r.get("requirement_id"),
        })
    return out


def _checklist_plan(review:dict[str,Any])->list[dict[str,Any]]:
    rows=list((review or {}).get("results") or [])
    out=[]
    for r in annotate_rows(rows,"checklist"):
        if r.get("is_heading"): continue
        out.append({
            "plan_id":f"CL-{len(out)+1:04d}","domain":"checklist",
            "check":r.get("question") or "Пункт чек-листа","scope":r.get("automatic_section") or r.get("section") or "Раздел",
            "method":r.get("typed_check") or r.get("execution_class") or "SPECIALIST",
            "expected_sections":[r.get("automatic_section")] if r.get("automatic_section") else [],
            "verification_kind":r.get("verification_kind"),"verification_state":r.get("verification_state"),
            "source_id":r.get("item_no") or r.get("position"),
        })
    return out


def build_review_plan(*,assignment_rows:list[dict[str,Any]]|None=None,normative_rows:list[dict[str,Any]]|None=None,checklist_review:dict[str,Any]|None=None,comparisons:list[dict[str,Any]]|None=None)->dict[str,Any]:
    assignment_rows=assignment_rows or []; normative_rows=normative_rows or []; checklist_review=checklist_review or {}
    plan=_assignment_plan(assignment_rows)+_normative_plan(normative_rows)+_checklist_plan(checklist_review)
    summaries={
        "assignment":domain_summary(assignment_rows,"assignment"),
        "normative":domain_summary(normative_rows,"normative"),
        "checklist":domain_summary(list(checklist_review.get("results") or []),"checklist"),
    }
    for key,value in summaries.items(): value["label"]=DOMAIN_LABELS[key]
    return {
        "version":"1.0","principle":"Сначала план проверки → затем целевое доказательство → затем квалифицированный вывод",
        "domains":summaries,"checks":plan,"checks_total":len(plan),
        "completed":sum(x.get("completed",0) for x in summaries.values()),
        "project_findings":sum(x.get("project_findings",0) for x in summaries.values()),
        "review_questions":sum(x.get("review_questions",0) for x in summaries.values()),
        "system_limitations":sum(x.get("system_limitations",0) for x in summaries.values()),
    }
