from __future__ import annotations
from typing import Any

VERIFICATION_KINDS={"VERIFIED_OK","PROJECT_FINDING","REVIEW_QUESTION","SYSTEM_LIMITATION","INFORMATIONAL"}
KIND_STATES={
    "VERIFIED_OK":"Соответствует",
    "PROJECT_FINDING":"Выявлено несоответствие",
    "REVIEW_QUESTION":"Требует проверки специалистом",
    "SYSTEM_LIMITATION":"Не проверено автоматически",
    "INFORMATIONAL":"Информация",
}

# Status parsing is deliberately fail-closed.  In particular, a phrase such as
# "Предварительно подтверждено AI" must never become VERIFIED_OK merely because
# it contains the substring "подтвержден".
OK_STATUSES={"соответствует","соответствует заданию","подтверждено","подтвержден","подтверждён","совпадает","да"}
BAD_STATUSES={"нет","не соответствует"}
BAD_TOKENS=("не соответствует","выявлено отклонение","расхождение","конфликт")
REVIEW_TOKENS=("требует проверки","требуется смысловая проверка","частично","готово к проверке")
PROVISIONAL_TOKENS=("предварительно","кандидат в доказательства","ai-кандидат","ai кандидат")
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
    # A final adjudicated verdict is the only supported override.  We do not
    # trust a previously derived ``verification_kind`` because old versions may
    # have produced it with permissive substring matching.
    explicit=str(row.get("final_verification_kind") or "").upper()
    if explicit in VERIFICATION_KINDS:
        return {
            "verification_kind":explicit,
            "verification_state":str(row.get("final_verification_state") or KIND_STATES[explicit]),
            "verification_has_evidence":has_evidence,
        }

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
    elif domain == 'assignment':
        strong_assignment_proof={
            'VERIFIED_EVIDENCE','VERIFIED_SET_EVIDENCE','STRUCTURED_VALUE',
            'STRUCTURED_COMPARISON','VERIFIED_ENGINEERING_EVIDENCE',
        }
        if low in OK_STATUSES and proof not in strong_assignment_proof:
            has_evidence=False

    # Нормативный вывод допускается только для верифицированного пункта KB.
    # Неверифицированная норма — ограничение покрытия ExpertCheck, а не проблема проекта.
    if domain == 'normative' and not bool(row.get('verified_clause')):
        return {"verification_kind":"SYSTEM_LIMITATION","verification_state":"Не проверено автоматически","verification_has_evidence":False}

    if any(t in low for t in PROVISIONAL_TOKENS):
        kind="REVIEW_QUESTION" if has_evidence else "SYSTEM_LIMITATION"
        state=KIND_STATES[kind]
    elif (low in BAD_STATUSES or any(t in low for t in BAD_TOKENS)) and not any(t in low for t in LIMIT_TOKENS):
        if has_evidence or domain in {"assignment","comparison"}:
            kind="PROJECT_FINDING"; state="Выявлено несоответствие"
        else:
            kind="REVIEW_QUESTION"; state="Требует проверки специалистом"
    elif low in OK_STATUSES:
        if domain in {'checklist','assignment'} and not has_evidence:
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
    active=[x for x in annotated if not x.get("is_heading")]
    evidence_ready=sum(str(x.get("evidence_level") or "") in {"L3","L4","L5"} for x in active)
    semantic_consensus=sum(
        str(x.get("semantic_consensus_state") or "").upper()=="PASSED"
        or int(x.get("semantic_consensus_completed") or 0)>0
        for x in active
    )
    return {
        "total":total,"verified_ok":counts["VERIFIED_OK"],"project_findings":counts["PROJECT_FINDING"],
        "review_questions":counts["REVIEW_QUESTION"],"system_limitations":counts["SYSTEM_LIMITATION"],
        "informational":counts["INFORMATIONAL"],
        "completed":completed,"automatic_coverage_pct":round(100*completed/max(1,total),1),
        "evidence_ready":evidence_ready,"evidence_coverage_pct":round(100*evidence_ready/max(1,total),1),
        "semantic_consensus_completed":semantic_consensus,
        "evidence_level_distribution":{
            level:sum(str(x.get("evidence_level") or "L0")==level for x in active)
            for level in ("L0","L1","L2","L3","L4","L5")
        },
    }


def verification_label(value:Any)->str:
    return {
        'CONFIRMED':'Соответствует','ISSUE':'Выявлено несоответствие','REVIEW':'Требует проверки специалистом',
        'SYSTEM_LIMITATION':'Не проверено автоматически','UNRESOLVED':'Не завершено',
        'VERIFIED_OK':'Соответствует','PROJECT_FINDING':'Выявлено несоответствие','REVIEW_QUESTION':'Требует проверки специалистом',
    }.get(str(value or '').upper(), str(value or ''))
