from __future__ import annotations

from core.cross_section_verification import qualify_cross_section_verdicts
from core.review_queue import build_review_clusters
from core.verification_coverage_187 import refresh_verification_coverage


def _sources():
    return [
        {
            "document": "ПЗ.pdf", "page": 12, "section": "ПЗ",
            "trusted_for_mismatch": True, "value": 89.9,
        },
        {
            "document": "ПЗУ.pdf", "page": 5, "section": "ПЗУ",
            "trusted_for_mismatch": True, "value": 89.9,
        },
    ]


def _comparison(status='СОВПАДАЕТ'):
    return {
        "check_code": "CORE-XSEC-AREA-TEST",
        "category": "Межраздельная сверка",
        "check_type": "Сводная межраздельная проверка",
        "status": status,
        "object": "Здание проборазделки",
        "object_id": "OBJ-4.13",
        "parameter_code": "AREA_BUILD",
        "parameter_name": "Площадь застройки",
        "unit": "м2",
        "verification_evidence": _sources(),
        "independent_trusted_sources": 2,
        "trusted_section_families": ["ПЗ", "ПЗУ"],
        "dependency_diagnostics": {"owner_present": [], "control_present": []},
        "engineering_binding": {"parameter_expected_for_object": True},
    }


def test_independent_agreement_can_close_without_owner_mapping():
    row=_comparison('СОВПАДАЕТ')
    audit=qualify_cross_section_verdicts([row])
    assert audit["passed"] == 1
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["proof_kind"] == "STRUCTURED_AGREEMENT"
    assert row["cross_section_gate"]["proof_route"] == "INDEPENDENT_AGREEMENT"
    assert row["evidence_level"] == "L5"


def test_mismatch_still_requires_owner_control_route():
    row=_comparison('ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ')
    audit=qualify_cross_section_verdicts([row])
    assert audit["blocked"] == 1
    assert row["final_verification_kind"] == "REVIEW_QUESTION"
    assert "раздел-владелец" in row["coverage_reason"]


def test_agreement_without_two_trusted_sources_remains_blocked():
    row=_comparison('СОВПАДАЕТ')
    row["verification_evidence"][1]["trusted_for_mismatch"] = False
    row["independent_trusted_sources"] = 1
    row["trusted_section_families"] = ["ПЗ"]
    audit=qualify_cross_section_verdicts([row])
    assert audit["blocked"] == 1
    assert row["final_verification_kind"] == "SYSTEM_LIMITATION"


def test_review_queue_compresses_across_objects_without_losing_ids():
    rows=[]
    for i in range(75):
        rows.append({
            "ID": f"Q-{i:03d}",
            "Контур": "Чек-листы",
            "Объект": f"Объект {i%15}",
            "Проверка": "Проверить наличие маркировки оборудования",
            "Причина": "В ожидаемых разделах не найден адресный кандидат с документом и страницей.",
            "Код причины": "NO_ADDRESSABLE_EVIDENCE",
            "Семейство проверки": "Document Evidence",
            "Ожидаемые разделы": ["ТХ"],
            "Уровень доказательства": "L2",
        })
    clusters=build_review_clusters(rows)
    assert len(clusters) == 2
    assert sum(int(row["Количество вопросов"]) for row in clusters) == 75
    assert all(int(row["Количество объектов"]) <= 15 for row in clusters)
    assert all(row["Код причины"] == "NO_ADDRESSABLE_EVIDENCE" for row in clusters)


def test_coverage_refresh_rebuilds_comparison_domain_without_pdf_or_ai():
    row=_comparison('СОВПАДАЕТ')
    docs=[{
        "snapshot_restored": True,
        "assignment_compliance": [],
        "normative_compliance_audit": [],
        "automatic_checklist_review": {"results": []},
    }]
    summary=refresh_verification_coverage(docs,[row])
    assert summary["source_pdf_required"] is False
    assert summary["ai_required"] is False
    assert summary["comparison_completed"] == 1
    assert summary["comparison_verified_ok"] == 1
    assert docs[0]["project_review_plan"]["domains"]["comparison"]["completed"] == 1



def test_independent_conflict_confirms_fact_without_claiming_correct_value():
    row=_comparison('ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ')
    row["verification_evidence"][1]["value"] = 48.7
    audit=qualify_cross_section_verdicts([row])
    assert audit["passed"] == 1
    assert row["final_verification_kind"] == "PROJECT_FINDING"
    assert row["proof_kind"] == "STRUCTURED_CONFLICT"
    assert row["cross_section_gate"]["proof_route"] == "INDEPENDENT_CONFLICT"
    assert row["conflict_confirmed"] is True
    assert row["correct_value_verified"] is False
