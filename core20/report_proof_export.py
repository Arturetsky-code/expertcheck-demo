from __future__ import annotations

from copy import copy
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

from .proof_labels import judge_label, proof_state_label, proof_type_label


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


def reconcile_project_data_contract_workbook(
    payload: bytes | bytearray | None,
    project_data_contract: dict[str, Any] | None,
) -> bytes | None:
    """Keep report-facing data-contract metrics equal to the pipeline checkpoint.

    The report builder performs a second serialization-safety normalization. Its
    repair count may be much larger because nested NaN values are sanitized for
    XLSX. That boundary audit is useful diagnostics, but it must not replace the
    project contract metric shown in the UI.
    """
    if payload is None:
        return None
    raw=bytes(payload)
    contract=dict(project_data_contract or {})
    if not raw or not contract:
        return raw

    workbook=load_workbook(BytesIO(raw))
    changed=False

    if "Резюме" in workbook.sheetnames:
        sheet=workbook["Резюме"]
        summary_values={
            "Контракт данных 18.0":contract.get("status") or "Не выполнен",
            "Исправлено значений контрактом":int(contract.get("repairs") or 0),
            "Отпечаток результата":contract.get("result_identity_fingerprint") or "—",
        }
        for row_index in range(2,sheet.max_row+1):
            label=str(sheet.cell(row=row_index,column=1).value or "").strip()
            if label in summary_values:
                sheet.cell(row=row_index,column=2,value=summary_values[label])
                changed=True

    if "Контроль данных" in workbook.sheetnames:
        sheet=workbook["Контроль данных"]
        existing={}
        for row_index in range(2,sheet.max_row+1):
            label=str(sheet.cell(row=row_index,column=1).value or "").strip()
            if label:
                existing[label]=sheet.cell(row=row_index,column=2).value

        project_values={
            "Версия контракта":contract.get("version"),
            "Статус":contract.get("status"),
            "Исправлено значений":int(contract.get("repairs") or 0),
            "Документов":(contract.get("counts") or {}).get("documents",0),
            "Находок":(contract.get("counts") or {}).get("findings",0),
            "Сверок":(contract.get("counts") or {}).get("comparisons",0),
            "Отпечаток результата":contract.get("result_identity_fingerprint"),
        }
        for row_index in range(2,sheet.max_row+1):
            label=str(sheet.cell(row=row_index,column=1).value or "").strip()
            if label in project_values:
                sheet.cell(row=row_index,column=2,value=project_values[label])
                changed=True
            elif label.startswith("Исправление:"):
                sheet.cell(row=row_index,column=1,value="Экспортное "+label.casefold())
                changed=True

        export_rows=[
            ("Экспортный контроль: статус",existing.get("Статус")),
            ("Экспортный контроль: исправлено значений",existing.get("Исправлено значений")),
            ("Экспортный контроль: отпечаток результата",existing.get("Отпечаток результата")),
        ]
        template_row=2 if sheet.max_row>=2 else 1
        for label,value in export_rows:
            if value in (None,""):
                continue
            target=sheet.max_row+1
            sheet.cell(row=target,column=1,value=label)
            sheet.cell(row=target,column=2,value=value)
            for col in (1,2):
                src=sheet.cell(row=template_row,column=col)
                dst=sheet.cell(row=target,column=col)
                if src.has_style:
                    dst._style=copy(src._style)
                if src.font:
                    dst.font=copy(src.font)
                if src.fill:
                    dst.fill=copy(src.fill)
                if src.border:
                    dst.border=copy(src.border)
                if src.alignment:
                    dst.alignment=copy(src.alignment)
            changed=True

    if not changed:
        return raw
    output=BytesIO()
    workbook.save(output)
    return output.getvalue()
