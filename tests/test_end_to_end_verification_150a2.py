from core.atomic_requirement_graph import atomize_requirement
from core.atomic_verification_engine import verify_atomic_requirements
from types import SimpleNamespace

from core.semantic_evidence_engine import _public_packet, run_semantic_evidence_engine
from core.verification_recipe_compiler_v2 import VerificationRecipeCompilerV2
from core.report_engine import build_structured_report
from core.ru_labels import ru_label
from tests.test_semantic_evidence_engine_140a1 import FakeProvider, _row


def _value_atoms(text: str, **parent):
    requirement = {"requirement_id": "A2-REQ", "requirement_text": text, **parent}
    return [row for row in atomize_requirement(requirement) if row.get("atomic_kind") == "VALUE_COMPARISON"]


def test_units_bind_to_their_own_numeric_occurrence():
    electrical = _value_atoms("Напряжение сети 220 В, частота 50 Гц.")
    assert [(row["parameter_code"], row["required_value"]) for row in electrical] == [
        ("VOLTAGE", 220.0), ("FREQUENCY", 50.0),
    ]
    dust = _value_atoms("Давление воздуха; содержание пыли должно быть более 1 мг/м3.")
    assert len(dust) == 1
    assert (dust[0]["parameter_code"], dust[0]["comparison_operator"]) == ("DUST_CONCENTRATION", "GT")


def test_stale_parent_measurement_is_not_inherited_by_line_count_atom():
    atoms = atomize_requirement({
        "requirement_id": "A2-LINES",
        "requirement_text": "Дробление выполняется двумя независимыми технологическими линиями.",
        "requirement_type": "VALUE_COMPARISON",
        "parameter_code": "CAPACITY", "required_value": 500, "unit": "т/ч",
    })
    assert len(atoms) == 1
    assert (atoms[0]["parameter_code"], atoms[0]["required_value"], atoms[0]["unit"]) == ("LINE_COUNT", 2, "шт")


def test_nonnumeric_row_heading_does_not_inherit_numeric_kind():
    atoms = atomize_requirement({
        "requirement_id": "A2-SHIFT-HEADING",
        "requirement_text": "Продолжительность смены",
        "requirement_type": "VALUE_COMPARISON",
        "parameter_code": "SHIFT_DURATION",
    })
    assert len(atoms) == 1
    assert atoms[0]["atomic_kind"] == "PRESENCE_REQUIREMENT"
    assert atoms[0].get("required_value") in (None, "")


def test_equipment_atoms_keep_precise_equipment_owner():
    atoms = atomize_requirement({
        "requirement_id": "A2-EQUIPMENT",
        "requirement_text": "Предусмотреть два погрузчика SHANTUI L76-C5 с ковшом 4,5 м3.",
        "object_name": "Бункер",
    })
    assert {row.get("object_name") for row in atoms} == {"Погрузчик SHANTUI L76-C5"}
    values = {row.get("parameter_code"): row.get("required_value") for row in atoms if row.get("parameter_code")}
    assert values == {"QUANTITY": 2, "BUCKET_VOLUME": 4.5}


def test_adaptive_search_pattern_does_not_demote_numeric_recipe():
    atom = _value_atoms("Рабочее давление должно быть не более 1,6 МПа.")[0]
    recipe = VerificationRecipeCompilerV2("knowledge").compile(atom)
    assert recipe["check_method"] == "VALUE_COMPARISON"
    assert recipe["pattern_origin"] == "ADAPTIVE_CONTRACT_COMPILER"
    assert recipe["retrieval_only"] is False
    assert recipe["recipe_status"] == "TRUSTED"
    assert recipe["executable"] is True


def test_numeric_checker_accepts_canonical_property_alias():
    atom = _value_atoms("Установленная мощность должна быть не более 100 кВт.")[0]
    atom["parameter_code"] = "POWER_INST"
    fact = {
        "fact_id": "A2-POWER", "property_code": "POWER_INSTALLED", "property_name": "Установленная мощность",
        "value": 120, "unit": "кВт", "document": "ИОС1.pdf", "page": 9, "section": "ИОС1",
        "source_trace": "Установленная мощность 120 кВт", "fact_admission_decision": "ADMIT",
        "evidence_quality_decision": "VERIFIED", "binding_status": "ROW_LOCKED",
        "physical_trace_level": "ROW_TRACE", "owner": "Проект",
    }
    result = verify_atomic_requirements(
        [atom], knowledge_root="knowledge", fact_graph={"facts": [fact], "passages": []}, page_corpus=[]
    )[0]
    assert result["verification_kind"] == "PROJECT_FINDING"
    assert result["difference"]["observed"] == 120


def test_l4_always_has_visible_addressable_evidence():
    row = _row()
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="off",
    )
    assert audit["evidence_levels"]["L4"] == 1
    assert row["evidence_contract_state"] == "SATISFIED"
    assert row["verification_evidence"]
    assert row["evidence"]
    assert all(item.get("document") and item.get("page") not in (None, "") for item in row["verification_evidence"])


def test_critic_provider_is_called_once_for_one_judge_decision():
    row = _row()
    judge = FakeProvider("OpenRouter", "judge")
    critic = FakeProvider("Groq", "critic")
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=judge, critic_provider=critic,
    )
    assert len(audit["critic_calls"]) == 1
    assert critic.last_payload["packets"][0]["packet_id"] == row["atom_id"]


class PreflightFailureProvider:
    name = "BlockedProvider"

    def __init__(self):
        self.generate_calls = 0

    def test_connection(self):
        return SimpleNamespace(
            ok=False, provider=self.name, model="blocked-model", status_code=403,
            error="Модель запрещена настройками проекта.",
        )

    def generate(self, prompt, system=""):
        self.generate_calls += 1
        raise AssertionError("Bulk generation must not start after failed preflight")


def test_failed_preflight_blocks_bulk_evidence_calls():
    row = _row()
    judge = PreflightFailureProvider()
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=judge, critic_provider=FakeProvider("Groq", "critic"),
    )
    assert audit["judge_selected"] == 0
    assert audit["preflight"]["judge"]["state"] == "FAILED"
    assert judge.generate_calls == 0
    assert any("Preflight Judge" in reason for reason in audit["activation_reasons"])


def test_external_packet_is_limited_to_four_short_evidence_fragments():
    evidence = [{
        "evidence_id": f"E-{index}", "document": f"Документ-{index}.pdf", "page": index,
        "section": "ТХ", "text": "Фрагмент " + ("x" * 1600),
        "contract_ready_for_judgement": True,
    } for index in range(1, 7)]
    payload = _public_packet({
        "packet_id": "BOUNDED", "requirement": "Требование " + ("y" * 1500),
        "evidence": evidence,
    })
    assert len(payload["evidence"]) == 4
    assert all(len(row["text"]) <= 720 for row in payload["evidence"])
    assert len(payload["requirement"]) <= 900


def test_report_uses_the_admitted_finding_class_instead_of_raw_status():
    comparison = {
        "comparison_id": "CMP-A2", "object": "Компрессорная", "parameter_name": "Площадь застройки",
        "status": "Потенциальное расхождение", "independent_trusted_sources": 2,
        "independent_section_count": 2, "document_values": "ПЗ: 54,3 м²; ПЗУ: 48,7 м²",
        "sources": "ПЗ, стр. 4 | ПЗУ, стр. 8",
    }
    report = build_structured_report("A2", [{}], [comparison])
    assert report["summary"]["project_findings"] == 1
    assert report["summary"]["review_questions"] == 0
    assert report["problems"][0]["finding_type"] == "PROJECT_FINDING"
    assert report["problems"][0]["status"] == "Выявлено несоответствие"


def test_report_keeps_weak_mismatch_as_a_specialist_question():
    comparison = {
        "comparison_id": "CMP-A2-REVIEW", "object": "Насосная", "parameter_name": "Высота",
        "status": "Потенциальное расхождение", "independent_trusted_sources": 1,
        "independent_section_count": 1, "document_values": "АР: 2,5 м",
        "sources": "АР, стр. 3",
    }
    report = build_structured_report("A2", [{}], [comparison])
    assert report["summary"]["project_findings"] == 0
    assert report["summary"]["review_questions"] == 1
    assert report["problems"][0]["finding_type"] == "REVIEW_QUESTION"
    assert report["problems"][0]["status"] == "Требует проверки"


def test_new_service_codes_are_localized():
    raw_codes = (
        "SPECIALIST_REVIEW", "ENGINEERING_SEMANTIC_REVIEW", "FEATURE_PRESENCE",
        "NORMATIVE_CONTENT_REVIEW", "ATOMIC_PATTERN_PRESENCE",
        "INDEPENDENT_SEMANTIC_CONFIRMATION_REQUIRED", "PAYLOAD_TOO_LARGE",
        "DUST_CONCENTRATION", "FREQUENCY", "APPLICABILITY_DECLARATION",
        "TRACEABILITY", "EXECUTABLE_RECIPE",
    )
    assert all(ru_label(code) != code for code in raw_codes)
    combined = "DOCUMENT_TRACEABILITY, NUMERIC_VALUE_COMPARISON"
    assert ru_label(combined) == "Прослеживаемость документов, Сверка числового значения"
