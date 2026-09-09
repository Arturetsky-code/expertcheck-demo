from pathlib import Path

from core20.normative_foundation import _section_key, NormativeKnowledgeFoundation20


def test_alpha72_recognises_real_project_section_filenames():
    assert _section_key("Раздел ПД №1_ПЗ.pdf")=="пз"
    assert _section_key("Раздел ПД №2_ПЗУ1.pdf")=="пзу"
    assert _section_key("Раздел ПД №3_АР.pdf")=="ар"
    assert _section_key("Раздел ПД №4_КР.pdf")=="кр"
    assert _section_key("Раздел ПД №6_ТХ1.pdf")=="тх"
    assert _section_key("Раздел ПД №5_подраздел ПД №1_ИОС1.1.pdf")=="иос"


def test_alpha72_verified_pp87_routes_are_selected_from_real_filenames():
    foundation=NormativeKnowledgeFoundation20(Path(__file__).resolve().parents[1]/"knowledge")
    docs=[
        {"document":"Раздел ПД №2_ПЗУ1.pdf"},
        {"document":"Раздел ПД №3_АР.pdf"},
        {"document":"Раздел ПД №5_подраздел ПД №1_ИОС1.1.pdf"},
    ]
    routed=foundation.project_routes(docs)
    assert routed["verified_clause_routes"] >= 3
    assert routed["automatic_contract_ready"] >= 3
