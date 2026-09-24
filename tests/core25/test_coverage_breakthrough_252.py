from __future__ import annotations

from core25.runtime_bridge import run_assignment_runtime


def _base(requirement_type: str, text: str, evidence: dict) -> dict:
    return {
        "requirement_id": "REQ-1",
        "requirement_text": text,
        "requirement_type": requirement_type,
        "requirement_scope": "DOCUMENT_SPECIFIC",
        "expected_sections": ["ПЗ"],
        "directed_evidence_candidates": [evidence],
    }


def test_negative_applicability_can_close_through_core25():
    req = _base(
        "PROHIBITION_OR_NOT_REQUIRED",
        "Разработка отдельного решения не требуется.",
        {
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_NEGATIVE_APPLICABILITY",
            "negative_assertion": True,
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 18,
            "context": "Для данного объекта разработка отдельного решения не требуется.",
            "score": 96,
        },
    )
    payload = run_assignment_runtime([req])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["proof_state"] == "PROVEN_MATCH"
    assert row["core25_reason_code"] == "NEGATIVE_APPLICABILITY_CONFIRMED"
    assert row["verification_evidence"][0]["page"] == 18


def test_factual_normative_assertion_can_close_but_reference_only_cannot():
    verified = _base(
        "NORMATIVE_COMPLIANCE",
        "Климатический район принять по СП 131.13330.2020.",
        {
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_NORMATIVE_ASSERTION",
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 21,
            "context": "По СП 131.13330.2020 площадка относится к климатическому району IВ.",
            "matched_normative_refs": ["сп 131.13330.2020"],
            "matched_terms": ["климатическ", "район"],
            "score": 95,
        },
    )
    payload = run_assignment_runtime([verified])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_reason_code"] == "FACTUAL_NORMATIVE_ASSERTION_CONFIRMED"

    weak = dict(verified)
    weak["requirement_id"] = "REQ-2"
    weak["directed_evidence_candidates"] = [{
        **verified["directed_evidence_candidates"][0],
        "evidence_kind": "NORMATIVE_REFERENCE_CANDIDATE",
        "matched_terms": [],
    }]
    payload = run_assignment_runtime([weak])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "REVIEW_QUESTION"
    assert row["proof_state"] == "INSUFFICIENT"


def test_site_presence_scope_is_not_forced_to_unbound():
    req = {
        "requirement_id": "REQ-FENCE",
        "requirement_text": "Предусмотреть металлическое ограждение части площадки ДСК.",
        "requirement_type": "PRESENCE_REQUIREMENT",
        "requirement_scope": "SITE_SPECIFIC",
        "expected_sections": ["ПЗУ"],
        "directed_evidence_candidates": [{
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_PROJECT_PASSAGE",
            "document": "Раздел ПД №2_ПЗУ.pdf",
            "document_type": "ПЗУ",
            "page": 27,
            "context": "Территория площадки ДСК ограждается металлическими панелями по столбам.",
            "score": 94,
        }],
    }
    payload = run_assignment_runtime([req])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_reason_code"] == "ASSIGNMENT_PRESENCE_CONFIRMED"


def test_unverified_candidate_never_becomes_core25_proof():
    req = _base(
        "PROHIBITION_OR_NOT_REQUIRED",
        "Разработка отдельного решения не требуется.",
        {
            "evidence_state": "candidate",
            "evidence_kind": "QUALIFIED_NEGATIVE_APPLICABILITY",
            "negative_assertion": True,
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 18,
            "context": "Разработка отдельного решения не требуется.",
            "score": 96,
        },
    )
    payload = run_assignment_runtime([req])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "REVIEW_QUESTION"


def test_unresolved_negative_requirement_is_safe_project_global_and_closes():
    req = {
        "requirement_id": "REQ-NEG-UNRESOLVED",
        "requirement_text": "Разработка отдельного раздела не требуется.",
        "requirement_type": "PROHIBITION_OR_NOT_REQUIRED",
        "requirement_scope": "UNRESOLVED",
        "directed_evidence_candidates": [{
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_NEGATIVE_APPLICABILITY",
            "negative_assertion": True,
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 18,
            "context": "Разработка отдельного раздела не требуется.",
            "score": 97,
        }],
    }
    row = run_assignment_runtime([req])["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_admission_stage"] == "PROVEN"
    assert row["core25_binding_counts"]["BOUND"] == 1


def test_exact_requirement_owner_wins_over_duplicate_registry_alias_ids():
    req = {
        "requirement_id": "REQ-DSK-CAPACITY",
        "requirement_text": "Установить ДСК суммарной производительностью 500 т/ч.",
        "requirement_type": "VALUE_COMPARISON",
        "requirement_scope": "OBJECT_SPECIFIC",
        "object_id": "REQ-DSK-ID",
        "object_name": "ДСК",
        "parameter_code": "CAPACITY",
        "required_value": 500,
        "unit": "т/ч",
        "expected_sections": ["ТХ"],
        "directed_evidence_candidates": [{
            "evidence_state": "verified_candidate",
            "evidence_kind": "DIRECTED_VALUE",
            "document": "Раздел ПД №6_ТХ1.pdf",
            "document_type": "ТХ",
            "page": 20,
            "context": "ДСК принят суммарной производительностью 500 т/ч.",
            "object": "ДСК",
            "owner_match": True,
            "parameter_code": "CAPACITY",
            "value": 500,
            "unit": "т/ч",
            "unit_compatible": True,
            "score": 100,
        }],
    }
    row = run_assignment_runtime(
        [req],
        object_registry=[{"object_id": "REG-DSK-ID", "name": "ДСК"}],
    )["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_reason_code"] == "TYPED_VALUE_MATCH"
    assert row["core25_binding_reason_codes"]["OWNER_PARAMETER_BOUND"] == 1


def test_admission_diagnostics_distinguish_unverified_candidate():
    req = _base(
        "PRESENCE_REQUIREMENT",
        "Предусмотреть систему видеонаблюдения.",
        {
            "evidence_state": "candidate",
            "evidence_kind": "SOURCE_LOCKED_PASSAGE",
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 30,
            "context": "Система видеонаблюдения рассматривается в проекте.",
            "score": 70,
        },
    )
    row = run_assignment_runtime([req])["rows"][0]
    assert row["core25_admission_stage"] == "CANDIDATE_NOT_VERIFIED"
    assert row["core25_raw_candidate_count"] == 1
    assert row["core25_verified_candidate_count"] == 0
    assert row["core25_qualified_evidence_count"] == 0


def test_pdf_hyphenation_repair_restores_equipment_owner_and_mixed_positive_is_not_prohibition():
    from core.assignment_compliance import (
        TYPE_PRESENCE,
        _object_name,
        _repair_pdf_hyphenation,
        _requirement_type,
    )

    equipment = _repair_pdf_hyphenation(
        "Подача руды в приёмный бункер осуществляется двумя погруз- чиками SHANTUI L76-С5 с объёмом ковша 4,5 м3"
    )
    owner = _object_name(equipment, "")
    assert owner.startswith("Погрузчик")
    assert "SHANTUI" in owner.upper()

    mixed = (
        "Выполнить электроснабжение согласно ТУ. "
        "Прокладку кабельных линий в земле не предусматривать."
    )
    assert _requirement_type(mixed, "Электроснабжение", "", None) == TYPE_PRESENCE


def test_short_presence_requirement_can_be_verified_when_all_terms_match():
    from core.assignment_verification_kernel import verify_assignment_requirement

    requirement = {
        "requirement_id": "REQ-SHORT-PRESENCE",
        "requirement_text": "Предусмотреть металлическое ограждение территории",
        "requirement_type": "PRESENCE_REQUIREMENT",
        "source_row_title": "Ограждение территории",
        "evidence_contract_v2": {
            "scope": "SITE_SPECIFIC",
            "expected_sections": ["ПЗУ"],
            "critical_qualifiers": ["металлическ"],
        },
    }
    result = verify_assignment_requirement(
        requirement,
        [{
            "document": "Раздел ПД №2_ПЗУ.pdf",
            "document_type": "ПЗУ",
            "page": 12,
            "text": "Проектом предусмотрено металлическое ограждение территории площадки.",
        }],
    )
    assert result is not None
    assert result["status"] == "Соответствует заданию"
    assert result["verification_evidence"][0]["evidence_state"] == "verified_candidate"


def test_support_wall_requirement_is_not_misbound_to_loader_or_dsk():
    from core.assignment_compliance import _object_name
    from core.requirement_contracts import build_contract

    text = (
        "Для формирования площадки временного хранения и перегрузки взорванной руды "
        "фронтальными погрузчиками в приёмные бункера ДСК предусмотреть подпорную стену."
    )
    owner = _object_name(text, "")
    assert owner == "Подпорная стена"

    req = {
        "requirement_text": text,
        "requirement_type": "PRESENCE_REQUIREMENT",
        "object_name": owner,
        "parameter_code": "",
        "source_row_title": "Технологические решения",
    }
    contract = build_contract(req)
    assert contract["scope"] == "SITE_SPECIFIC"
    assert contract["expected_sections"] == ["ПЗУ"]


def test_modular_building_and_canopy_requirements_get_profile_sections():
    from core.requirement_contracts import infer_expected_sections

    assert infer_expected_sections(
        {"requirement_text": "Характеристики блочно-модульных зданий принять по документации завода изготовителя."}
    ) == ["АР", "ПЗ"]
    assert infer_expected_sections(
        {"requirement_text": "Навес системы подачи извести выполнить открытым."}
    ) == ["АР", "ПЗ"]


def test_contractual_handover_materials_are_not_assignment_design_requirements(tmp_path):
    import fitz
    from core.assignment_compliance import extract_requirements
    from core.project_upload import PreparedUpload
    import legacy_analyzer

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Задание на проектирование")
    page.insert_text((72, 100), "Количество и формат представляемых материалов")
    page.insert_text((72, 128), "После получения положительных заключений экспертиз Исполнитель передает Заказчику окончательную версию проектной документации")
    data = pdf.tobytes()
    pdf.close()
    upload = PreparedUpload(name="Задание на проектирование.pdf", data=data, declared_document_type="Задание на проектирование")
    rows = extract_requirements([upload], legacy_analyzer.read_pdf)
    assert not any("передает Заказчику окончательную версию" in row.get("requirement_text", "") for row in rows)


def test_negative_applicability_requires_same_local_clause():
    from core.assignment_verification_kernel import verify_assignment_requirement

    requirement = {
        "requirement_type": "PROHIBITION_OR_NOT_REQUIRED",
        "source_row_title": "Требования к разработке специальных технических условий",
        "requirement_text": "Разработка не требуется",
        "evidence_contract_v2": {"expected_sections": []},
    }
    unrelated = [{
        "document": "ПЗ.pdf", "document_type": "ПЗ", "page": 10,
        "text": "Требования к разработке специальных технических условий рассматриваются отдельно.\nВозмещение убытков не требуется.",
    }]
    result = verify_assignment_requirement(requirement, unrelated)
    assert result is None or result.get("status") != "Соответствует заданию"

    same_clause = [{
        "document": "ПЗ.pdf", "document_type": "ПЗ", "page": 11,
        "text": "Разработка специальных технических условий\nне требуется.",
    }]
    result = verify_assignment_requirement(requirement, same_clause)
    assert result and result.get("status") == "Соответствует заданию"


def test_construction_duration_design_determined_requires_actual_duration_value():
    from core.assignment_verification_kernel import verify_assignment_requirement

    requirement = {
        "requirement_type": "DESIGN_DETERMINED",
        "source_row_title": "Срок строительства объекта",
        "requirement_text": "Определить проектной документацией",
        "evidence_contract_v2": {"expected_sections": []},
    }
    toc_only = [{
        "document": "ПЗ.pdf", "document_type": "ПЗ", "page": 2,
        "text": "Содержание. Срок строительства объекта. Проектом предусмотрено строительство объекта.",
    }]
    result = verify_assignment_requirement(requirement, toc_only)
    assert result is None or result.get("status") != "Соответствует заданию"

    actual = [{
        "document": "ПЗ.pdf", "document_type": "ПЗ", "page": 20,
        "text": "Срок строительства объекта проектом предусмотрен 8 месяцев.",
    }]
    result = verify_assignment_requirement(requirement, actual)
    assert result and result.get("status") == "Соответствует заданию"


def test_core25_design_determined_structured_duration_can_close():
    req = {
        "requirement_id": "REQ-DURATION-STRUCTURED",
        "requirement_text": "Определить проектной документацией",
        "requirement_type": "DESIGN_DETERMINED",
        "requirement_scope": "PROJECT_GLOBAL",
        "expected_sections": ["ПЗ"],
        "directed_evidence_candidates": [{
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_DESIGN_DETERMINED",
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 27,
            "context": "Сведения о сроках проведения работ. Продолжительность работ, месяц: 12.",
            "score": 98,
            "design_determined_subject": "CONSTRUCTION_DURATION",
            "structured_project_fact": True,
            "observed_value": 12,
            "observed_unit": "месяц",
        }],
    }
    row = run_assignment_runtime([req])["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_reason_code"] == "ASSIGNMENT_DESIGN_VALUE_CONFIRMED"


def test_secondary_determine_clause_does_not_reclassify_primary_presence():
    from core.assignment_compliance import TYPE_PRESENCE, _requirement_type

    text = (
        "Предусмотреть ограждение территории с воротами и калитками. "
        "Размеры определить проектом."
    )
    assert _requirement_type(text, "Ограждение", "", None) == TYPE_PRESENCE


def test_lightning_grounding_composite_requires_all_conditions():
    from core.assignment_verification_kernel import verify_assignment_requirement

    requirement = {
        "requirement_type": "PRESENCE_REQUIREMENT",
        "source_row_title": "Молниезащита и заземление",
        "requirement_text": (
            "Для защиты людей предусмотреть заземляющее устройство. "
            "Молниезащиту выполнить молниеприемниками на мачтах освещения, "
            "для зданий вне зоны защиты — металлическими конструкциями, "
            "в соответствии с РД 34.21.122-87 и СО 153-34.21.122-2003."
        ),
        "evidence_contract_v2": {"expected_sections": ["ИОС1"]},
    }
    complete = [{
        "document": "Раздел ПД №5_ИОС1.1.pdf",
        "document_type": "ИОС1",
        "page": 21,
        "text": (
            "Для защиты людей от поражения электрическим током и защиты электрооборудования "
            "предусматривается заземляющее устройство. "
            "Молниезащита сооружений технологического комплекса выполняется по II категории "
            "в соответствии с РД 34.21.122-87. "
            "Объект классифицируется согласно СО 153-34.21.122-2003. "
            "Молниезащита технологического комплекса выполняется с помощью молниеприемников "
            "установленных на мачтах освещения. "
            "Молниезащита зданий вне зоны защиты мачт освещения осуществляется с помощью "
            "металлических конструкций этих зданий. Конструктивные элементы зданий "
            "удовлетворяют требованиям к естественным молниеприемникам в соответствии "
            "с п. 3.2.1.2 СО 153-34.21.122-2003."
        ),
    }]
    result = verify_assignment_requirement(requirement, complete)
    assert result is not None
    assert result["status"] == "Соответствует заданию"
    assert result["condition_summary"]["proven"] == 5
    assert result["condition_summary"]["total"] == 5
    assert all(
        item["evidence_state"] == "verified_candidate"
        for item in result["verification_evidence"]
    )

    incomplete = [{
        **complete[0],
        "text": (
            "Для защиты людей от поражения электрическим током и защиты электрооборудования "
            "предусматривается заземляющее устройство. "
            "Молниезащита технологического комплекса выполняется с помощью молниеприемников "
            "установленных на мачтах освещения."
        ),
    }]
    result = verify_assignment_requirement(requirement, incomplete)
    assert result is not None
    assert result["status"] == "Требует проверки"
    assert result["condition_summary"]["proven"] == 2
    assert all(
        item["evidence_state"] == "candidate"
        for item in result["verification_evidence"]
    )

def test_lightning_grounding_scope_precedes_inherited_dsk_equipment_owner():
    from core.requirement_contracts import SCOPE_EQUIPMENT, SCOPE_SYSTEM, infer_scope

    lightning = {
        "source_row_title": "Молниезащита и заземление",
        "requirement_text": (
            "Для защиты людей от поражения электрическим током и защиты "
            "электрооборудования предусматривается заземляющее устройство. "
            "Молниезащиту площадки ДСК выполнить с помощью молниеприемников "
            "на мачтах освещения."
        ),
        "object_name": "ДСК",
    }
    assert infer_scope(lightning) == SCOPE_SYSTEM

    equipment = {
        "source_row_title": "Технологические решения",
        "requirement_text": "Предусмотреть насосный агрегат для технологической линии ДСК.",
        "object_name": "Насос",
    }
    assert infer_scope(equipment) == SCOPE_EQUIPMENT




def test_lightning_grounding_composite_accumulates_realistic_split_page_evidence():
    from core.assignment_verification_kernel import verify_assignment_requirement

    requirement = {
        "requirement_type": "PRESENCE_REQUIREMENT",
        "source_row_title": "Молниезащита и заземление",
        "requirement_text": (
            "Для защиты людей от поражения электрическим током и защиты электрооборудования "
            "предусматривается заземляющее устройство. Молниезащиту площадки ДСК выполнить "
            "с помощью молниеприемников на мачтах освещения. Молниезащиту зданий вне зоны "
            "защиты мачт выполнить с помощью металлических конструкций зданий. "
            "Молниезащиту выполнить в соответствии с РД 34.21.122-87 и СО 153-34.21.122-2003."
        ),
        "evidence_contract_v2": {"expected_sections": ["ИОС1"]},
    }
    pages = [
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 20,
            "text": (
                "Система защитного заземления. Для защиты людей от поражения электрическим током "
                "и защиты электрооборудования предусматривается заземляющее устройство."
            ),
        },
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 21,
            "text": (
                "Молниезащита сооружений технологического комплекса выполняется по II категории "
                "в соответствии с РД 34.21.122-87. Объект классифицируется как обычное промышленное "
                "предприятие согласно СО 153-34.21.122-2003. Молниезащита технологического комплекса "
                "выполняется с помощью молниеприемников установленных на мачтах освещения. "
                "Молниезащита зданий вне зоны защиты мачт освещения осуществляется с помощью "
                "металлических конструкций этих зданий. Конструктивные элементы зданий удовлетворяют "
                "требованиям к естественным молниеприемникам в соответствии с п. 3.2.1.2 "
                "СО 153-34.21.122-2003."
            ),
        },
    ]

    result = verify_assignment_requirement(requirement, pages)
    assert result is not None
    assert result["status"] == "Соответствует заданию"
    assert result["verification_kernel"] == "LIGHTNING_GROUNDING_COMPOSITE_EXECUTOR"
    assert result["condition_summary"]["proven"] == 5
    assert result["condition_summary"]["total"] == 5
    assert {item["page"] for item in result["verification_evidence"]} == {20, 21}
    assert all(item["evidence_state"] == "verified_candidate" for item in result["verification_evidence"])


def test_lightning_grounding_composite_reaches_core25_verified_ok():
    from core.assignment_verification_kernel import verify_assignment_requirement

    legacy_requirement = {
        "requirement_type": "PRESENCE_REQUIREMENT",
        "source_row_title": "Молниезащита и заземление",
        "requirement_text": (
            "Предусмотреть заземляющее устройство; молниезащиту выполнить молниеприемниками "
            "на мачтах освещения и металлическими конструкциями зданий вне зоны защиты; "
            "применить РД 34.21.122-87 и СО 153-34.21.122-2003."
        ),
        "evidence_contract_v2": {"expected_sections": ["ИОС1"]},
    }
    pages = [
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 20,
            "text": (
                "Для защиты людей от поражения электрическим током и защиты электрооборудования "
                "предусматривается заземляющее устройство."
            ),
        },
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 21,
            "text": (
                "Молниезащита сооружений технологического комплекса выполняется по II категории "
                "в соответствии с РД 34.21.122-87. Объект классифицируется как обычное промышленное "
                "предприятие согласно СО 153-34.21.122-2003. Молниезащита технологического комплекса "
                "выполняется с помощью молниеприемников установленных на мачтах освещения. "
                "Молниезащита зданий вне зоны защиты мачт освещения осуществляется с помощью "
                "металлических конструкций этих зданий. Конструктивные элементы зданий удовлетворяют "
                "требованиям к естественным молниеприемникам в соответствии с п. 3.2.1.2 "
                "СО 153-34.21.122-2003."
            ),
        },
    ]
    legacy = verify_assignment_requirement(legacy_requirement, pages)
    assert legacy is not None
    assert legacy["status"] == "Соответствует заданию"

    req = {
        "requirement_id": "ASSIGN-LIGHTNING-GROUNDING",
        "requirement_text": legacy_requirement["requirement_text"],
        "requirement_type": "PRESENCE_REQUIREMENT",
        "requirement_scope": "SYSTEM_SPECIFIC",
        "expected_sections": ["ИОС1"],
        "directed_evidence_candidates": legacy["verification_evidence"],
    }
    row = run_assignment_runtime([req])["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["proof_state"] == "PROVEN_MATCH"
    assert row["core25_reason_code"] == "ASSIGNMENT_PRESENCE_CONFIRMED"



def test_lighting_composite_requires_all_five_conditions():
    from core.assignment_verification_kernel import verify_assignment_requirement

    requirement = {
        "requirement_type": "NORMATIVE_COMPLIANCE",
        "source_row_title": "Электроосвещение",
        "requirement_text": (
            "Для электроосвещения предусмотреть светодиодные светильники. "
            "Освещение площадки дробильно-сортировочного комплекса выполнить с помощью "
            "прожекторных мачт. Остальную территорию осветить с помощью консольных "
            "светильников, устанавливаемых на опорах. Уровни искусственного освещения "
            "принять в соответствии с СП 52.13330.2016."
        ),
        "evidence_contract_v2": {"expected_sections": ["ИОС1"]},
    }
    complete = [
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 24,
            "text": (
                "Выбор количества и мощности осветительных устройств выполнен исходя из "
                "нормированных уровней освещенности. Уровни искусственного освещения "
                "приняты в соответствии с СП 52.13330.2016."
            ),
        },
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 26,
            "text": (
                "Наружное освещение. Светильники наружного освещения устанавливаются на "
                "опорах вдоль проездов и площадок стоянки автотранспорта. Для освещения "
                "центральной части производственного комплекса применяются осветительные "
                "мачты. В качестве источников света приняты современные светодиодные светильники."
            ),
        },
        {
            "document": "Раздел ПД №5_ИОС1.2.pdf",
            "document_type": "ИОС1",
            "page": 15,
            "text": (
                "Светодиодный прожектор 600 Вт. Устанавливается на осветительную мачту "
                "на высоте 20 м. Схема установки светильника на опоре. Светильник "
                "консольный. Кронштейн, угол 15°. Остальная территория освещается "
                "консольными светильниками, устанавливаемыми на опорах."
            ),
        },
    ]
    result = verify_assignment_requirement(requirement, complete)
    assert result is not None
    assert result["status"] == "Соответствует заданию"
    assert result["verification_kernel"] == "LIGHTING_COMPOSITE_EXECUTOR"
    assert result["condition_summary"]["proven"] == 5
    assert result["condition_summary"]["total"] == 5
    assert all(item["evidence_state"] == "verified_candidate" for item in result["verification_evidence"])

    incomplete = [complete[0], complete[1], {
        **complete[2],
        "text": (
            "Светодиодный прожектор 600 Вт. Устанавливается на осветительную мачту "
            "на высоте 20 м. Схема установки светильника на опоре. Светильник "
            "консольный. Кронштейн, угол 15°."
        ),
    }]
    result = verify_assignment_requirement(requirement, incomplete)
    assert result is not None
    assert result["status"] == "Требует проверки"
    assert result["condition_summary"]["proven"] == 4
    assert result["condition_summary"]["total"] == 5
    assert any("остальная территория" in item for item in result["condition_summary"]["missing"])
    assert all(item["evidence_state"] == "candidate" for item in result["verification_evidence"])


def test_lighting_composite_reaches_core25_only_after_full_gate():
    from core.assignment_verification_kernel import verify_assignment_requirement

    legacy_requirement = {
        "requirement_type": "NORMATIVE_COMPLIANCE",
        "source_row_title": "Электроосвещение",
        "requirement_text": (
            "Для электроосвещения предусмотреть светодиодные светильники. "
            "Освещение площадки ДСК выполнить с помощью прожекторных мачт. "
            "Остальную территорию осветить с помощью консольных светильников на опорах. "
            "Уровни искусственного освещения принять в соответствии с СП 52.13330.2016."
        ),
        "evidence_contract_v2": {"expected_sections": ["ИОС1"]},
    }
    pages = [
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 24,
            "text": (
                "Уровни искусственного освещения приняты в соответствии с СП 52.13330.2016."
            ),
        },
        {
            "document": "Раздел ПД №5_ИОС1.1.pdf",
            "document_type": "ИОС1",
            "page": 26,
            "text": (
                "Наружное освещение. Светильники наружного освещения устанавливаются на "
                "опорах вдоль проездов и площадок стоянки автотранспорта. Для освещения "
                "центральной части производственного комплекса применяются осветительные "
                "мачты. В качестве источников света приняты современные светодиодные светильники."
            ),
        },
        {
            "document": "Раздел ПД №5_ИОС1.2.pdf",
            "document_type": "ИОС1",
            "page": 15,
            "text": (
                "Светодиодный прожектор 600 Вт. Устанавливается на осветительную мачту "
                "на высоте 20 м. Схема установки светильника на опоре. Светильник "
                "консольный. Кронштейн, угол 15°. Остальная территория освещается "
                "консольными светильниками, устанавливаемыми на опорах."
            ),
        },
    ]
    legacy = verify_assignment_requirement(legacy_requirement, pages)
    assert legacy is not None
    assert legacy["status"] == "Соответствует заданию"
    assert sum(
        item["evidence_kind"] == "QUALIFIED_NORMATIVE_ASSERTION"
        for item in legacy["verification_evidence"]
    ) == 1

    req = {
        "requirement_id": "ASSIGN-LIGHTING",
        "requirement_text": legacy_requirement["requirement_text"],
        "requirement_type": "NORMATIVE_COMPLIANCE",
        "requirement_scope": "SYSTEM_SPECIFIC",
        "expected_sections": ["ИОС1"],
        "directed_evidence_candidates": legacy["verification_evidence"],
    }
    row = run_assignment_runtime([req])["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["proof_state"] == "PROVEN_MATCH"
    assert row["core25_reason_code"] == "FACTUAL_NORMATIVE_ASSERTION_CONFIRMED"


def test_electrical_lighting_routes_to_system_scope():
    from core.requirement_contracts import SCOPE_SYSTEM, infer_scope

    requirement = {
        "source_row_title": "Электроосвещение",
        "requirement_text": (
            "Для электроосвещения предусмотреть светодиодные светильники. "
            "Освещение площадки ДСК выполнить с помощью прожекторных мачт."
        ),
        "object_name": "ДСК",
    }
    assert infer_scope(requirement) == SCOPE_SYSTEM
