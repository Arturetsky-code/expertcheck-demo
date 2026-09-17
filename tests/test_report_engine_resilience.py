import io

from openpyxl import load_workbook

from core.report_engine import build_structured_report
from studio.data import structured_excel_report


def test_report_generation_accepts_non_string_finding_fields():
    comparison = {
        "comparison_id": "CMP-REPORT-NON-STRING",
        "finding_type": "REVIEW_QUESTION",
        "user_status": float("nan"),
        "object": 101,
        "parameter_name": float("nan"),
        "status": "Требует проверки",
        "applicability_proven": True,
    }

    report = build_structured_report("Проект", [{}], [comparison])

    assert len(report["problems"]) == 1
    assert report["problems"][0]["object"] == "101"
    assert report["problems"][0]["parameter"] == "Проверка"
    assert report["problems"][0]["status"] == "Требует проверки"


def test_report_generation_deduplicates_mixed_scalar_types_without_crashing():
    base = {
        "finding_type": "PROJECT_FINDING",
        "user_status": 422,
        "object": 7,
        "parameter_name": 12,
        "explicit_contradiction": True,
    }

    report = build_structured_report(
        "Проект",
        [{}],
        [dict(base, comparison_id="CMP-1"), dict(base, comparison_id="CMP-2")],
    )

    assert len(report["problems"]) == 1
    assert report["problems"][0]["object"] == "7"
    assert report["problems"][0]["parameter"] == "12"
    assert report["problems"][0]["status"] == "422"


def test_technical_report_accepts_mixed_cross_section_gate_reasons():
    document = {
        "Файл": "ТХ.pdf",
        "Тип документа": "ТХ",
        "Страниц": 1,
        "assignment_compliance": [],
        "normative_compliance_audit": [],
        "automatic_checklist_review": {"results": []},
        "project_review_plan": {},
        "coverage_matrix": {},
        "semantic_evidence_engine": {},
        "report_quality_gate": {"status": "PASSED", "issues": []},
    }
    comparison = {
        "comparison_id": "CMP-MIXED-GATE-REASONS",
        "object": "Технологический комплекс",
        "parameter_name": "Производительность",
        "status": "Требует проверки",
        "cross_section_gate_state": "BLOCKED",
        "cross_section_gate_reasons": [
            "Не найден контрольный раздел.",
            None,
            422,
            {"code": "MISSING_OWNER", "reason": "Не найден раздел-владелец."},
            ["вложенная", "диагностика"],
        ],
    }

    payload = structured_excel_report(
        "Проект", "ExpertCheck 17.1 Proof", [document], [], [comparison],
        report_kind="technical", checklist_results=[],
    )

    workbook = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
    rows = list(workbook["Тех_сверки"].iter_rows(values_only=True))
    exported = dict(zip(rows[0], rows[1]))
    reasons = exported["gate_reasons"]
    assert "Не найден контрольный раздел" in reasons
    assert "422" in reasons
    assert "MISSING_OWNER" in reasons
    assert "вложенная" in reasons



def test_exported_cross_section_metrics_reconcile_with_confirmed_finding():
    document = {
        "Файл": "ПЗ.pdf",
        "Тип документа": "ПЗ",
        "Страниц": 50,
        "consolidated_registry": [{"name":"Компрессорная"}],
        "assignment_compliance": [],
        "normative_compliance_audit": [],
        "automatic_checklist_review": {"results": []},
        # Deliberately stale plan: report boundary must rebuild it.
        "project_review_plan": {
            "domains": {
                "comparison": {
                    "total": 1, "completed": 0, "issue": 0,
                    "verified_ok": 0, "project_findings": 0,
                    "review_questions": 1, "system_limitations": 0,
                    "informational": 0, "coverage_pct": 0,
                }
            }
        },
        "coverage_matrix": {},
        "semantic_evidence_engine": {},
        "report_quality_gate": {"status": "PASSED", "issues": []},
        "completeness_user_confirmed": True,
    }
    comparison = {
        "check_code":"CORE-XSEC-AREA_BUILD-TEST",
        "object":"Компрессорная",
        "object_id":"OBJ-1",
        "parameter_code":"AREA_BUILD",
        "parameter_name":"Площадь застройки",
        "unit":"m2",
        "status":"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ",
        "document_values":"ПЗ: 54.3 m2 | ПЗУ: 48.7 m2",
        "verification_evidence":[
            {
                "document":"ПЗ.pdf","page":45,"section":"ПЗ",
                "object_id":"OBJ-1","parameter_code":"AREA_BUILD",
                "value":54.3,"unit":"m2","trusted_for_mismatch":True,
            },
            {
                "document":"ПЗУ.pdf","page":18,"section":"ПЗУ",
                "object_id":"OBJ-1","parameter_code":"AREA_BUILD",
                "value":48.7,"unit":"m2","trusted_for_mismatch":True,
            },
        ],
        "source_records":[],
        "trusted_section_families":["ПЗ","ПЗУ"],
        "independent_trusted_sources":2,
    }

    payload = structured_excel_report(
        "Проект", "ExpertCheck 20.0 Alpha 6.2", [document], [], [comparison],
        report_kind="manager", checklist_results=[],
    )
    workbook = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
    rows = list(workbook["Резюме"].iter_rows(values_only=True))
    summary = {row[0]: row[1] for row in rows if row and row[0]}
    assert summary["Подтверждённых несоответствий проекта"] == 1
    assert summary["Межраздельная сверка: завершено"] == 1
    assert summary["Межраздельная сверка: несоответствий"] == 1
    assert summary["Контроль согласованности отчёта"] == "Пройден"
