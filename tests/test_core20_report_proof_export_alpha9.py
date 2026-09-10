from io import BytesIO

from openpyxl import Workbook, load_workbook

from core20.report_proof_export import enrich_normative_proof_workbook


def _workbook_bytes():
    wb=Workbook()
    ws=wb.active
    ws.title="НТД 20.0 — исполнение"
    ws.append(["ID требования","НТД","Результат"])
    ws.append(["PP87-X-SEM","ПП РФ №87","Подтверждено"])
    out=BytesIO(); wb.save(out); return out.getvalue()


def _manifest():
    return {
        "normative_execution":{
            "rows":[{
                "requirement_id":"PP87-X-SEM",
                "proof_type":"SEMANTIC_REQUIREMENT",
                "proof_state":"SEMANTIC_CONSENSUS_PROOF",
                "retrieval_candidate_count":2,
                "semantic_proof":{
                    "judge_verdict":"SUPPORTS",
                    "judge_confidence":0.96,
                    "judge_provider":"Groq",
                    "judge_model":"model-a",
                    "critic_accept":True,
                    "critic_confidence":0.91,
                    "critic_provider":"Gemini",
                    "critic_model":"model-b",
                    "independent":True,
                    "independence_reason":"Провайдеры и модели различаются.",
                    "selected_evidence":[
                        {"evidence_id":"NORM-E-1","document":"ПЗУ.pdf","page":10,"source_locator":"ПЗУ.pdf, стр. 10"},
                        {"evidence_id":"NORM-E-2","document":"ПЗУ.pdf","page":11,"source_locator":"ПЗУ.pdf, стр. 11"},
                    ],
                },
            }]
        }
    }


def test_alpha9_export_appends_proof_and_judge_critic_trace():
    enriched=enrich_normative_proof_workbook(_workbook_bytes(),_manifest())
    wb=load_workbook(BytesIO(enriched),data_only=True)
    ws=wb["НТД 20.0 — исполнение"]
    headers={cell.value:cell.column for cell in ws[1]}
    assert "Тип доказательства" in headers
    assert "Состояние доказательства" in headers
    assert "Решение проверяющей модели" in headers
    assert "Контрольная модель приняла" in headers
    assert "Выбранные доказательства" in headers
    assert ws.cell(2,headers["Тип доказательства"]).value=="Смысловое выполнение требования"
    assert ws.cell(2,headers["Смысловое доказательство применено"]).value=="Да"
    assert ws.cell(2,headers["Решение проверяющей модели"]).value=="Подтверждает"
    assert ws.cell(2,headers["Контрольная модель приняла"]).value=="Да"
    trace=ws.cell(2,headers["Выбранные доказательства"]).value
    assert "ПЗУ.pdf, стр. 10" in trace
    assert "ПЗУ.pdf, стр. 11" in trace


def test_alpha9_export_is_noop_when_execution_sheet_absent():
    wb=Workbook(); wb.active.title="Резюме"
    out=BytesIO(); wb.save(out)
    original=out.getvalue()
    enriched=enrich_normative_proof_workbook(original,_manifest())
    assert enriched==original
