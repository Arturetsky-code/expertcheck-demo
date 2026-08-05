from core.project_completeness import (
    PROFILE_CAPITAL, STATUS_INCLUDED, STATUS_MISSING, STATUS_PRESENT,
    build_matrix, summarize,
)

def test_detects_present_and_missing_sections():
    matrix = build_matrix(["ПЗ", "ПЗ XML", "ПЗУ1", "АР1", "ТХ1", "ПОС"], PROFILE_CAPITAL)
    by_code = {row["Код"]: row for row in matrix}
    assert by_code["ПЗ"]["Итоговый статус"] == STATUS_PRESENT
    assert by_code["ПЗУ"]["Итоговый статус"] == STATUS_PRESENT
    assert by_code["КР"]["Итоговый статус"] == STATUS_MISSING

def test_user_can_resolve_conditional_section():
    matrix = build_matrix([], PROFILE_CAPITAL, {"ЭЭ": {"status": STATUS_INCLUDED, "justification": "Решения распределены по АР, КР и ИОС"}})
    by_code = {row["Код"]: row for row in matrix}
    assert by_code["ЭЭ"]["Итоговый статус"] == STATUS_INCLUDED

def test_summary_keeps_missing_risk_after_confirmation():
    matrix = build_matrix(["ПЗ"], PROFILE_CAPITAL)
    result = summarize(matrix, user_confirmed=True, forming=False)
    assert result["missing"] > 0
    assert result["status"] == "Неполный комплект"
