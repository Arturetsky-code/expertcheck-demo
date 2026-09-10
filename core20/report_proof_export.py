from __future__ import annotations

from copy import copy
from io import BytesIO
from typing import Any

from openpyxl import load_workbook


SHEET_NAME = "НТД 20.0 — исполнение"
PROOF_COLUMNS = (
    "Тип доказательства",
    "Состояние доказательства",
    "Кандидатов доказательства",
    "Смысловое доказательство применено",
    "Решение проверяющей модели",
    "Достоверность проверяющей модели",
    "Провайдер проверяющей модели",
    "Проверяющая модель",
    "Контрольная модель приняла",
    "Достоверность контрольной модели",
    "Провайдер контрольной модели",
    "Контрольная модель",
    "Независимость моделей",
    "Основание независимости",
    "Выбранные доказательства",
)

PROOF_TYPE_LABELS={
    "PRESENCE":"Наличие сведений",
    "STRUCTURE":"Структура раздела",
    "SET_COMPLETENESS":"Полнота обязательного набора",
    "SEMANTIC_REQUIREMENT":"Смысловое выполнение требования",
    "GRAPHIC_CONTENT":"Содержание графической части",
    "TYPED_VALUE":"Структурированное значение",
    "CROSS_SECTION":"Межраздельная согласованность",
}
PROOF_STATE_LABELS={
    "RETAINED_FAIL_CLOSED":"Удержано исходное неопределённое состояние",
    "DETERMINISTIC_STRUCTURE_PROOF":"Структура подтверждена детерминированно",
    "ADDRESSABLE_PRESENCE_PROOF":"Наличие подтверждено адресным фрагментом",
    "PRESENCE_PROOF_NOT_ADDRESSABLE":"Адресное доказательство наличия не сформировано",
    "VISUAL_PROOF_REQUIRED":"Требуется визуальная проверка графической части",
    "SET_PROOF_CONTRACT_REQUIRED":"Требуется контракт полноты обязательного набора",
    "STRUCTURED_PROOF_REQUIRED":"Требуется структурированный доказательный контракт",
    "SEMANTIC_PROOF_REQUIRED":"Требуется независимая смысловая проверка",
    "SEMANTIC_CONSENSUS_PROOF":"Смысл подтверждён независимым консенсусом",
}
JUDGE_LABELS={
    "SUPPORTS":"Подтверждает",
    "CONTRADICTS":"Противоречит",
    "INSUFFICIENT":"Недостаточно доказательств",
    "OTHER_ENTITY":"Другой объект",
    "OTHER_METRIC":"Другой показатель",
}


def proof_type_label(value:Any)->str:
    code=str(value or "").strip().upper()
    return PROOF_TYPE_LABELS.get(code,code or "—")


def proof_state_label(value:Any)->str:
    code=str(value or "").strip().upper()
    return PROOF_STATE_LABELS.get(code,code or "—")


def judge_label(value:Any)->str:
    code=str(value or "").strip().upper()
    return JUDGE_LABELS.get(code,code or "—")


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
        "Тип доказательства":proof_type_label(row.get("proof_type")),
        "Состояние доказательства":proof_state_label(row.get("proof_state")),
        "Кандидатов доказательства":int(row.get("retrieval_candidate_count") or 0),
        "Смысловое доказательство применено":"Да" if row.get("proof_state")=="SEMANTIC_CONSENSUS_PROOF" else "Нет",
        "Решение проверяющей модели":judge_label(proof.get("judge_verdict")) if has_semantic else "—",
        "Достоверность проверяющей модели":proof.get("judge_confidence") if has_semantic else "—",
        "Провайдер проверяющей модели":proof.get("judge_provider") or "—",
        "Проверяющая модель":proof.get("judge_model") or "—",
        "Контрольная модель приняла":("Да" if proof.get("critic_accept") is True else "Нет") if has_semantic else "—",
        "Достоверность контрольной модели":proof.get("critic_confidence") if has_semantic else "—",
        "Провайдер контрольной модели":proof.get("critic_provider") or "—",
        "Контрольная модель":proof.get("critic_model") or "—",
        "Независимость моделей":("Да" if proof.get("independent") is True else "Нет") if has_semantic else "—",
        "Основание независимости":proof.get("independence_reason") or "—",
        "Выбранные доказательства":_selected_trace(row,proof) or "—",
    }


def enrich_normative_proof_workbook(
    payload: bytes | bytearray | None,
    canonical_manifest: dict[str, Any] | None,
) -> bytes | None:
    """Append Alpha 9 proof trace to the existing NTD execution worksheet."""
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
        sheet.column_dimensions[cell.column_letter].width=24 if header not in {"Основание независимости","Выбранные доказательства"} else 42

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
