from core.atomic_requirement_graph import atomize_requirement
from core.atomic_verification_engine import verify_atomic_requirements
from core.engineering_plausibility import apply_engineering_plausibility_guard
from core.fact_admission import assess_fact_admission
from core.typed_evidence_resolver import resolve_typed_evidence
from core.normative_compliance_engine import NormativeComplianceEngine
from core.project_review_planner import build_review_plan
from core.adversarial_review import adversarial_gate


def _fact(code, value):
    return {
        "document": "Раздел ПД №1_ПЗ.pdf", "page": 46,
        "table_index": "PZ_COMPLEX_OBJECT_REGISTER", "row_index": "4.18",
        "column_index": 4, "source_span": f"{code}-span",
        "object_hint": "Насосная станция", "genplan_position": "4.18",
        "binding_status": "ROW_LOCKED", "parameter_code": code,
        "parameter_name": code, "value": value, "unit": "м",
        "evidence_quality_decision": "VERIFIED", "row_integrity_status": "CONFIRMED",
    }


def test_height_source_typo_is_quarantined_without_rewrite():
    area = _fact("AREA_BUILD", 26.9); area["unit"] = "м2"
    volume = _fact("VOLUME_BUILD", 64.8); volume["unit"] = "м3"
    height = _fact("HEIGHT_BUILD", 25)
    findings = [area, volume, height]
    audit = apply_engineering_plausibility_guard(findings)
    assert height["value"] == 25
    assert height["engineering_plausibility_status"] == "BLOCKED_DIMENSIONAL_CONFLICT"
    assert height["possible_decimal_separator_candidate"] == 2.5
    assert height["comparison_excluded"] is True
    assert audit["blocked_dimensional_conflicts"] == 1
    assert assess_fact_admission(height)["fact_admission_decision"] == "HOLD"


def test_reasonable_height_remains_available():
    area = _fact("AREA_BUILD", 26.9); area["unit"] = "м2"
    volume = _fact("VOLUME_BUILD", 64.8); volume["unit"] = "м3"
    height = _fact("HEIGHT_BUILD", 2.5)
    apply_engineering_plausibility_guard([area, volume, height])
    assert height["engineering_plausibility_status"] == "PASSED_DIMENSIONAL_CHECK"
    assert not height.get("comparison_excluded")


def _verify(requirement, pages):
    atom = atomize_requirement({"requirement_id": "REQ-X", "requirement_text": requirement})[0]
    return verify_atomic_requirements(
        [atom], knowledge_root="knowledge",
        fact_graph={"facts": [], "passages": pages}, page_corpus=pages,
    )[0]


def test_offsite_disposal_is_not_proved_by_water_meter_text():
    row = _verify(
        "Бытовые стоки собирать в выгреб с последующим внеплощадочным вывозом.",
        [{"document": "ИОС2.pdf", "section": "ИОС2", "document_type": "ИОС2", "page": 7,
          "text": "Проектом предусмотрен водомерный узел. Учет воды выполняется счетчиком."}],
    )
    assert row["verification_kind"] not in {"VERIFIED_OK", "PROJECT_FINDING"}


def test_gravity_requirement_needs_gravity_qualifier_in_same_clause():
    row = _verify(
        "Предусмотреть самотечный сбор хозяйственно-бытовых стоков.",
        [{"document": "ИОС2.pdf", "section": "ИОС2", "document_type": "ИОС2", "page": 8,
          "text": "Проектом предусмотрен сбор хозяйственно-бытовых стоков в накопительную емкость."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_metal_structure_lightning_requirement_needs_specific_clause():
    row = _verify(
        "Молниезащиту выполнить металлическими конструкциями здания.",
        [{"document": "ИОС1.pdf", "section": "ИОС1", "document_type": "ИОС1", "page": 12,
          "text": "Проектом предусматриваются защитное заземление и система молниезащиты объекта."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_existing_road_network_is_not_proved_by_new_internal_roads():
    row = _verify(
        "Учесть существующую дорожную сеть предприятия.",
        [{"document": "ПЗУ1.pdf", "section": "ПЗУ", "document_type": "ПЗУ", "page": 30,
          "text": "Внутриплощадочные проезды предусмотрены с покрытием из гравийной смеси."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_specific_route_is_not_proved_by_unrelated_site_entrances():
    row = _verify(
        "Предусмотреть проезд техники и проход персонала со склада недробленой руды до технологического комплекса.",
        [{"document": "ПЗУ1.pdf", "section": "ПЗУ", "document_type": "ПЗУ", "page": 29,
          "text": "Проектом предусмотрены три въезда: к КПП, зданию проборазделки и насосной станции."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_safe_interlocked_start_is_not_proved_by_safe_unblocking():
    row = _verify(
        "АСУ должна обеспечивать безопасный пуск и сблокированную работу технологического оборудования.",
        [{"document": "ТХ1.pdf", "section": "ТХ", "document_type": "ТХ", "page": 50,
          "text": "Предусматриваются специальные инструменты для безопасного разблокирования оборудования."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_unrelated_action_on_flattened_table_page_cannot_close_storm_sewer():
    filler = " описание элемента" * 80
    row = _verify(
        "Предусмотреть ливневую канализацию.",
        [{"document": "ПЗУ1.pdf", "section": "ПЗУ", "document_type": "ПЗУ", "page": 19,
          "text": "Очистные сооружения ливневых сточных вод." + filler + " Дизельная электростанция устанавливается на салазках."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_negated_project_decision_does_not_support_positive_presence():
    row = _verify(
        "Предусмотреть хозяйственно-питьевое водоснабжение.",
        [{"document": "ИОС2.pdf", "section": "ИОС2", "document_type": "ИОС2", "page": 9,
          "text": "Организация источников хозяйственно-питьевого водоснабжения настоящим проектом не предусматривается."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_lighting_mast_is_not_proved_by_lightning_protection_mast():
    row = _verify(
        "Освещение площадки выполнить с помощью прожекторных мачт.",
        [{"document": "ИОС1.pdf", "section": "ИОС1", "document_type": "ИОС1", "page": 21,
          "text": "Молниезащита комплекса выполняется молниеприемниками на мачтах освещения."}],
    )
    assert row["verification_kind"] != "VERIFIED_OK"


def test_glued_support_type_and_underground_prohibition_are_separated():
    atoms = atomize_requirement({
        "requirement_id": "REQ-GLUED",
        "requirement_text": (
            "Электропитание выполнить воздушными линиями с изолированными проводами. "
            "Тип применяемых опор: Прокладку кабельных линий в земле не предусматривать."
        ),
    })
    prohibition = next(atom for atom in atoms if atom["atomic_kind"] == "PROHIBITION")
    assert prohibition["atom_text"].startswith("Прокладку кабельных линий")
    assert "воздушными" not in prohibition["atom_text"]


def test_bullet_context_is_not_prepended_to_local_prohibition():
    atoms = atomize_requirement({
        "requirement_id": "REQ-BULLET-NO",
        "requirement_text": (
            "Выполнить электроснабжение согласно ТУ. Тип применяемых опор:\n"
            "• Прокладку кабельных линий в земле не предусматривать."
        ),
    })
    prohibition = next(atom for atom in atoms if atom["atomic_kind"] == "PROHIBITION")
    assert prohibition["atom_text"] == "Прокладку кабельных линий в земле не предусматривать."


def test_direct_exact_clause_passes_contract_and_semantic_gate():
    row = _verify(
        "Предусмотреть светодиодные светильники.",
        [{"document": "ИОС1.pdf", "section": "ИОС1", "document_type": "ИОС1", "page": 9,
          "text": "Проектом предусмотрены светодиодные светильники наружного освещения."}],
    )
    assert row["verification_kind"] == "VERIFIED_OK"
    assert row["semantic_gate_state"] == "PASSED"
    assert row["verification_evidence"][0]["exact_clause"].startswith("Проектом предусмотрен")


def test_drawing_contract_cannot_be_closed_by_text_volume():
    atom = {
        "requirement_text": "На плане показать проезды",
        "evidence_contract_v2": {
            "expected_sections": ["ПЗУ"], "required_modality": "DRAWING",
            "critical_qualifiers": [], "same_clause_required": True,
        },
    }
    recipe = {"evidence_groups": [["проезд"]], "minimum_groups": 1,
              "requires_design_marker": True, "expected_sections": ["ПЗУ"]}
    resolved = resolve_typed_evidence(atom, recipe, [{
        "document": "Раздел ПД №2_ПЗУ1.pdf", "section": "ПЗУ", "page": 5,
        "text": "Проектом предусмотрены внутриплощадочные проезды.",
    }])
    assert resolved["contract_state"] == "UNSATISFIED"
    assert resolved["candidates"][0]["modality_gate_state"] == "BLOCKED"


def test_plain_not_required_is_applicability_declaration_not_prohibition():
    atom = atomize_requirement({
        "requirement_id": "REQ-NA", "requirement_text": "Разработка раздела не требуется.",
    })[0]
    assert atom["atomic_kind"] == "APPLICABILITY_DECLARATION"


def test_pp87_p12_text_and_graphic_parts_are_checked_deterministically():
    pages = [
        {"document": "Раздел ПД №2_ПЗУ1.pdf", "document_type": "ПЗУ", "page": 1, "text": "Текстовая часть"},
        {"document": "Раздел ПД №2_ПЗУ2.pdf", "document_type": "ПЗУ", "page": 1, "text": "Графическая часть"},
    ]
    rows = NormativeComplianceEngine("knowledge").review([], page_corpus=pages)
    row = next(item for item in rows if item.get("requirement_id") == "PP87-CLAUSE-12-PZU")
    assert row["coverage_state"] == "VERIFIED_OK"
    assert row["proof_kind"] == "STRUCTURED_COMPLETENESS"
    assert {item["part_role"] for item in row["evidence"]} == {"TEXT_PART", "GRAPHIC_PART"}
    plan = build_review_plan(normative_rows=rows, assignment_rows=[], checklist_review={"results": []})
    assert plan["domains"]["НТД"]["confirmed"] >= 1
    planned = next(item for item in plan["items"] if item["plan_id"] == "PP87-CLAUSE-12-PZU")
    assert adversarial_gate(planned, [])["adversarial_state"] == "PASSED"


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
