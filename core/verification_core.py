from __future__ import annotations
from typing import Any

OK_TOKENS=("соответствует","подтвержден","подтверждён","совпадает","да")
BAD_TOKENS=("не соответствует","выявлено отклонение","расхождение","конфликт","нет")
REVIEW_TOKENS=("требует проверки","требуется смысловая проверка","частично","готово к проверке")
LIMIT_TOKENS=("не проверено системой","нет данных","недостаточно данных","не покрыто нормативной базой")


def _status(row:dict[str,Any])->str:
    return str(row.get("status") or row.get("result") or row.get("Результат") or "").strip()


def classify_verification(row:dict[str,Any], domain:str="") -> dict[str,Any]:
    """One conservative outcome vocabulary for every verification domain.

    The classification is intentionally stricter than UI statuses: unsupported
    search failures are system limitations, not project findings.
    """
    status=_status(row)
    low=status.lower()
    proof=str(row.get("proof_kind") or row.get("evidence_quality_state") or row.get("coverage_state") or "").upper()
    evidence=row.get("evidence") or row.get("evidence_summary") or row.get("decision_basis") or ""
    has_evidence=bool(evidence) and proof not in {"UNSUPPORTED","NO_EVIDENCE","KB_GAP","EVIDENCE_GAP"}
    level=str(row.get("verification_level") or (row.get("compiled_rule") or {}).get("verification_level") or ("L2_VALUE" if proof=="STRUCTURED_VALUE" else "L3_CROSS_CHECK" if proof=="STRUCTURED_COMPARISON" else "L1_PRESENCE" if proof in {"PRESENCE","STRUCTURED_PRESENCE"} else "")).upper()
    # Precision-first checklist policy: evidence must be strong enough for the
    # semantic level of the question. Presence evidence cannot close completeness
    # or engineering-compliance checks.
    if domain == "checklist":
        adequate = {
            "L1_PRESENCE": {"PRESENCE","STRUCTURED_PRESENCE","DOCUMENT_IDENTITY","STRUCTURED_VALUE","STRUCTURED_COMPARISON"},
            "L2_VALUE": {"STRUCTURED_VALUE","STRUCTURED_COMPARISON"},
            "L3_CROSS_CHECK": {"STRUCTURED_COMPARISON"},
            "L4_COMPLETENESS": {"VERIFIED_SET_EVIDENCE","STRUCTURED_COMPLETENESS"},
            "L5_ENGINEERING_COMPLIANCE": {"VERIFIED_ENGINEERING_EVIDENCE","NORMATIVE_EVIDENCE"},
        }.get(level, set())
        if proof and proof not in adequate:
            has_evidence=False
        elif proof in adequate and proof.startswith('STRUCTURED_'):
            has_evidence=True

    # Нормативный вывод допускается только для верифицированного пункта KB.
    # Неверифицированная норма — ограничение покрытия ExpertCheck, а не проблема проекта.
    if domain == 'normative' and not bool(row.get('verified_clause')):
        return {"verification_kind":"SYSTEM_LIMITATION","verification_state":"Не проверено автоматически","verification_has_evidence":False}

    if any(t in low for t in BAD_TOKENS) and not any(t in low for t in LIMIT_TOKENS):
        if has_evidence or domain in {"assignment","comparison"}:
            kind="PROJECT_FINDING"; state="Выявлено несоответствие"
        else:
            kind="REVIEW_QUESTION"; state="Требует проверки специалистом"
    elif any(t in low for t in OK_TOKENS) and "не " not in low[:4]:
        if domain == 'checklist' and not has_evidence:
            kind='SYSTEM_LIMITATION'; state='Не проверено автоматически'
        else:
            kind="VERIFIED_OK"; state="Соответствует"
    elif any(t in low for t in LIMIT_TOKENS) or proof in {"UNSUPPORTED","NO_EVIDENCE","KB_GAP","EVIDENCE_GAP"}:
        kind="SYSTEM_LIMITATION"; state="Не проверено автоматически"
    elif any(t in low for t in REVIEW_TOKENS):
        kind="REVIEW_QUESTION" if has_evidence else "SYSTEM_LIMITATION"
        state="Требует проверки специалистом" if kind=="REVIEW_QUESTION" else "Не проверено автоматически"
    else:
        kind="INFORMATIONAL"; state=status or "Информация"
    return {"verification_kind":kind,"verification_state":state,"verification_has_evidence":has_evidence}


def annotate_rows(rows:list[dict[str,Any]], domain:str) -> list[dict[str,Any]]:
    out=[]
    for row in rows or []:
        item=dict(row); item.update(classify_verification(item,domain)); out.append(item)
    return out


def domain_summary(rows:list[dict[str,Any]], domain:str) -> dict[str,Any]:
    annotated=annotate_rows(rows,domain)
    total=len([x for x in annotated if not x.get("is_heading")])
    counts={k:sum(1 for x in annotated if x.get("verification_kind")==k and not x.get("is_heading")) for k in ("VERIFIED_OK","PROJECT_FINDING","REVIEW_QUESTION","SYSTEM_LIMITATION","INFORMATIONAL")}
    completed=counts["VERIFIED_OK"]+counts["PROJECT_FINDING"]
    return {
        "total":total,"verified_ok":counts["VERIFIED_OK"],"project_findings":counts["PROJECT_FINDING"],
        "review_questions":counts["REVIEW_QUESTION"],"system_limitations":counts["SYSTEM_LIMITATION"],
        "completed":completed,"automatic_coverage_pct":round(100*completed/max(1,total),1),
    }


def verification_label(value:Any)->str:
    return {
        'CONFIRMED':'Соответствует','ISSUE':'Выявлено несоответствие','REVIEW':'Требует проверки специалистом',
        'SYSTEM_LIMITATION':'Не проверено автоматически','UNRESOLVED':'Не завершено',
        'VERIFIED_OK':'Соответствует','PROJECT_FINDING':'Выявлено несоответствие','REVIEW_QUESTION':'Требует проверки специалистом',
    }.get(str(value or '').upper(), str(value or ''))
