from __future__ import annotations

from core.result_surface import build_project_surface_rows, build_review_surface_rows


def test_project_surface_keeps_project_understanding_continuity_finding():
    problems=[{
        "id":"PU-CONFLICT-003",
        "object":"Компрессорная",
        "parameter":"Площадь застройки",
        "status":"РАСХОЖДЕНИЕ",
        "finding_type":"PROJECT_FINDING",
        "values":"48.7 | 54.3",
        "sources":"ПЗ, ПЗУ",
    }]
    rows=build_project_surface_rows(problems, {'items':[]})
    assert len(rows)==1
    assert rows[0]["object"]=="Компрессорная"
    assert rows[0]["parameter_name"]=="Площадь застройки"


def test_review_surface_dedup_is_shared_between_ui_and_excel():
    problems=[{
        "id":"CMP-1",
        "object":"КПП",
        "parameter":"Высота",
        "finding_type":"REVIEW_QUESTION",
        "explanation":"Требуется проверка",
    }]
    plan={'items':[
        {
            "plan_id":"Q-1","verification_kind":"REVIEW_QUESTION","domain":"Задание на проектирование",
            "entity":"КПП","title":"Проверить высоту","coverage_reason":"Нужно подтверждение",
        },
        {
            "plan_id":"Q-1","verification_kind":"REVIEW_QUESTION","domain":"Задание на проектирование",
            "entity":"КПП","title":"Проверить высоту","coverage_reason":"Нужно подтверждение",
        },
    ]}
    rows=build_review_surface_rows(problems, plan)
    assert len(rows)==2
    assert {row["ID"] for row in rows} == {"CMP-1","Q-1"}
