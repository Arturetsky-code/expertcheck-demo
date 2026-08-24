from core.atomic_requirement_graph import atomize_requirement, build_atomic_requirement_graph
from core.atomic_verification_engine import verify_atomic_requirements
from core.normative_kb_v4 import NormativeKnowledgeBaseV4


def test_equipment_clause_is_split_by_identity_quantity_and_attribute():
    atoms = atomize_requirement({
        "requirement_id": "REQ-EQ",
        "requirement_text": "Подача выполняется двумя погрузчиками SHANTUI L76-С5 с объёмом ковша 4,5 м3",
    })
    focuses = {row.get("focus") for row in atoms}
    assert "EQUIPMENT_IDENTITY" in focuses
    assert "EQUIPMENT_QUANTITY" in focuses
    assert "BUCKET_VOLUME" in focuses


def test_prohibition_is_not_inherited_by_whole_power_clause():
    atoms = atomize_requirement({
        "requirement_id": "REQ-PWR",
        "requirement_text": (
            "Электропитание выполнить воздушными линиями с изолированными проводами. "
            "Прокладку кабельных линий в земле не предусматривать."
        ),
    })
    assert sum(row["atomic_kind"] == "PROHIBITION" for row in atoms) == 1
    assert any(row["atomic_kind"] != "PROHIBITION" for row in atoms)


def test_explicit_negative_project_decision_confirms_prohibition():
    atom = atomize_requirement({
        "requirement_id": "REQ-NO",
        "requirement_text": "Прокладку кабельных линий в земле не предусматривать.",
    })[0]
    pages = [{
        "document": "ИОС1.pdf", "document_type": "ИОС1", "section": "ИОС1", "page": 22,
        "text": "Внутриплощадочные сети прокладываются на опорах. Прокладка в земле не предусматривается.",
    }]
    row = verify_atomic_requirements(
        [atom], knowledge_root="knowledge", fact_graph={"facts": [], "passages": pages}, page_corpus=pages,
    )[0]
    assert row["verification_kind"] == "VERIFIED_OK"
    assert row["critic_state"] == "PASSED"
    assert row["verification_evidence"][0]["page"] == 22


def test_not_found_never_becomes_project_finding():
    atom = atomize_requirement({
        "requirement_id": "REQ-MISS",
        "requirement_text": "Предусмотреть систему, для которой нет специализированного рецепта.",
    })[0]
    row = verify_atomic_requirements(
        [atom], knowledge_root="knowledge", fact_graph={"facts": [], "passages": []}, page_corpus=[],
    )[0]
    assert row["verification_kind"] != "PROJECT_FINDING"


def test_graph_uses_explicit_project_wide_scope_instead_of_undefined():
    graph = build_atomic_requirement_graph([{
        "requirement_id": "REQ-ALL", "requirement_text": "Требования отсутствуют",
    }])
    assert graph["summary"]["scope_coverage_pct"] == 100.0
    assert graph["atoms"][0]["expected_sections"] == ["ALL"]


def test_clause_addressed_pp87_pack_is_verified_but_conservative():
    kb = NormativeKnowledgeBaseV4("knowledge")
    verified = [row for row in kb.compliance_requirements() if row.get("verified_clause")]
    assert {row["paragraph"] for row in verified} >= {"п. 12", "п. 13", "п. 15"}
    assert all(row.get("conclusion_mode") == "CATEGORICAL_ALLOWED" for row in verified)


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()

