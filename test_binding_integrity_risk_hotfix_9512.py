
from pathlib import Path
from core.table_row_integrity import apply_table_row_integrity_guard
from core.expert_review_engine import build_expert_risks

def test_shifted_neighbor_value_is_blocked():
    findings=[
      {"document":"ПЗ.pdf","page":45,"parameter_code":"AREA_BUILD","parameter_name":"Площадь застройки",
       "value":23.5,"unit":"м2","object_hint":"Модуль обеспыливания","genplan_position":"4.12","confidence":.985,
       "match_method":"строка таблицы состава сложного объекта"},
      {"document":"ПЗ.pdf","page":45,"parameter_code":"AREA_BUILD","parameter_name":"Площадь застройки",
       "value":89.9,"unit":"м2","object_hint":"Здание проборазделки","genplan_position":"4.13","confidence":.985,
       "match_method":"строка таблицы состава сложного объекта"},
      # Typical flattened-text off-by-one error:
      {"document":"ПЗ.pdf","page":45,"parameter_code":"AREA_BUILD","parameter_name":"Площадь застройки",
       "value":23.5,"unit":"м2","object_hint":"Здание проборазделки","confidence":.934,
       "match_method":"структурная строка ТЭП"},
    ]
    audit=apply_table_row_integrity_guard(findings)
    bad=findings[-1]
    assert audit["blocked_shifted_values"]==1
    assert bad["row_integrity_status"]=="BLOCKED_SHIFTED_VALUE"
    assert bad["comparison_excluded"] is True
    assert bad["row_integrity_reference_values"]==[89.9]

def test_matching_duplicate_can_remain_supporting_evidence():
    findings=[
      {"document":"ПЗ.pdf","page":45,"parameter_code":"AREA_BUILD","value":89.9,"object_hint":"Здание проборазделки",
       "confidence":.985,"match_method":"строка таблицы состава сложного объекта"},
      {"document":"ПЗ.pdf","page":45,"parameter_code":"AREA_BUILD","value":89.9,"object_hint":"Здание проборазделки",
       "confidence":.80,"match_method":"структурная строка ТЭП"},
    ]
    apply_table_row_integrity_guard(findings)
    assert findings[1]["row_integrity_status"]=="CONFIRMED_BY_AUTHORITATIVE_ROW"
    assert not findings[1].get("comparison_excluded")

def test_float_string_risk_score_does_not_crash():
    comparisons=[{
      "object":"КПП","parameter_name":"Площадь застройки","parameter_code":"AREA_BUILD",
      "status":"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ","engineering_risk_score":"71.0",
      "priority":"Высокий","sources":"ПЗ, стр. 1 | ПЗУ, стр. 2"
    }]
    rows=build_expert_risks(comparisons,[],[],documents=[])
    assert rows
    assert isinstance(rows[0]["score"],int)

def test_comma_float_risk_score_does_not_crash():
    comparisons=[{
      "object":"КТП","parameter_name":"Мощность","parameter_code":"POWER_INSTALLED",
      "status":"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ","engineering_risk_score":"52,5",
      "priority":"Средний","sources":"ПЗ | ИОС1"
    }]
    rows=build_expert_risks(comparisons,[],[],documents=[])
    assert rows
    assert isinstance(rows[0]["score"],int)
