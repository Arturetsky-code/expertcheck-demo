from __future__ import annotations

from copy import copy
from io import BytesIO
from typing import Any

from openpyxl import load_workbook


SHEET_NAME = "НТД 20.0 — исполнение"
PROOF_COLUMNS = (
    "Тип proof",
    "Состояние proof-gate",
    "Retrieval-кандидатов",
    "Semantic proof применён",
    "Verdict Judge",
    "Достоверность Judge",
    "Провайдер Judge",
    "Модель Judge",
    "Critic принял",
    "Достоверность Critic",
    "Провайдер Critic",
    "Модель Critic",
    "Независимость AI",
    "Основание независимости",
    "Выбранные evidence",
)


def _execution_rows(canonical_manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    manifest=dict(canonical_manifest or {})
    execution=dict(manifest.get("normative_execution") or {})
    return [dict(row) for row in (execution.get("rows") or []) if isinstance(row,dict)]


def _selected_trace(row: dict[str, Any], proof: dict[str, Any]) -> str:
    selected=list(proof.get("selected_evidence") or row.get("semantic_selected_evidence") or [])
    rendered=[]
    for item in selected:
        if not isinstance(item,dict):
            continue
        locator=str(item.get("source_locator") or "").strip()
        if not locator:
            document=str(item.get("document") or "").strip()
            page=item.get("page")
            locator=f"{document}, стр. {page}" if document and page not in (None,"") else document
        evidence_id=str(item.get("evidence_id") or "").strip()
        text=f"{evidence_id}: {locator}" if evidence_id and locator else evidence_id or locator
        if text and text not in rendered:
            rendered.append(text)
    return " | ".join(rendered)


def proof_export_row(row: dict[str, Any]) -> dict[str, Any]:
    proof=dict(row.get("semantic_proof") or {})
    has_semantic=bool(proof)
    return {
        "Тип proof":row.get("proof_type") or "—",
        "Состояние proof-gate":row.get("proof_state") or "—",
        "Retrieval-кандидатов":int(row.get("retrieval_candidate_count") or 0),
        "Semantic proof применён":"Да" if row.get("proof_state")=="SEMANTIC_CONSENSUS_PROOF" else "Нет",
        "Verdict Judge":proof.get("judge_verdict") or "—",
        "Достоверность Judge":proof.get("judge_confidence") if has_semantic else "—",
        "Провайдер Judge":proof.get("judge_provider") or "—",
        "Модель Judge":proof.get("judge_model") or "—",
        "Critic принял":("Да" if proof.get("critic_accept") is True else "Нет") if has_semantic else "—",
        "Достоверность Critic":proof.get("critic_confidence") if has_semantic else "—",
        "Провайдер Critic":proof.get("critic_provider") or "—",
        "Модель Critic":proof.get("critic_model") or "—",
        "Независимость AI":("Да" if proof.get("independent") is True else "Нет") if has_semantic else "—",
        "Основание независимости":proof.get("independence_reason") or "—",
        "Выбранные evidence":_selected_trace(row,proof) or "—",
    }


def enrich_normative_proof_workbook(
    payload: bytes | bytearray | None,
    canonical_manifest: dict[str, Any] | None,
) -> bytes | None:
    """Append Alpha 9 proof trace to the existing NTD execution worksheet.

    The main XLSX builder remains the source of workbook structure. This narrow
    post-processor only adds proof fields that belong to Canonical Core 20.0 and
    therefore avoids duplicating the large legacy report builder.
    """
    if payload is None:
        return None
    raw=bytes(payload)
    rows=_execution_rows(canonical_manifest)
    if not raw or not rows:
        return raw

    workbook=load_workbook(BytesIO(raw))
    if SHEET_NAME not in workbook.sheetnames:
        return raw
    sheet=workbook[SHEET_NAME]
    headers={str(cell.value or "").strip():cell.column for cell in sheet[1]}
    requirement_col=headers.get("ID требования")
    if requirement_col is None:
        return raw

    by_id={str(row.get("requirement_id") or "").strip():row for row in rows if str(row.get("requirement_id") or "").strip()}
    if not by_id:
        return raw

    start_col=sheet.max_column+1
    template=sheet.cell(row=1,column=max(1,start_col-1))
    for offset,header in enumerate(PROOF_COLUMNS):
        cell=sheet.cell(row=1,column=start_col+offset,value=header)
        if template.has_style:
            cell._style=copy(template._style)
        if template.font:
            cell.font=copy(template.font)
        if template.fill:
            cell.fill=copy(template.fill)
        if template.border:
            cell.border=copy(template.border)
        if template.alignment:
            cell.alignment=copy(template.alignment)
        sheet.column_dimensions[cell.column_letter].width=24 if header not in {"Основание независимости","Выбранные evidence"} else 42

    for row_index in range(2,sheet.max_row+1):
        requirement_id=str(sheet.cell(row=row_index,column=requirement_col).value or "").strip()
        source=by_id.get(requirement_id)
        if not source:
            continue
        values=proof_export_row(source)
        for offset,header in enumerate(PROOF_COLUMNS):
            sheet.cell(row=row_index,column=start_col+offset,value=values.get(header))

    output=BytesIO()
    workbook.save(output)
    return output.getvalue()
