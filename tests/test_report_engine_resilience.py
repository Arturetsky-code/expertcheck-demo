from core.report_engine import build_structured_report


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
