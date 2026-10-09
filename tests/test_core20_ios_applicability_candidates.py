from core20.ios_applicability_candidates import build_ios_applicability_candidates
from core20.normative_execution import _ios_inventory, _set_completeness_evaluation


def _fixture(*, document="Объект А/ИОС1.pdf", quote=None):
    quote=quote or "Для объекта предусмотрен подраздел ИОС1 согласно заданию."
    documents=[
        {"Файл":document,"Тип документа":"ИОС1"},
        {"project_understanding":{"objects":[{
            "object_id":"OBJ-A",
            "properties":{"ios_subsection_applicability":[{
                "subsection":"ИОС1","applicability":"REQUIRED",
                "document":document,"page":7,"fragment":quote,
            }]},
        }]}},
    ]
    pages=[{"document":document,"page":7,"text":quote}]
    return documents,pages


def _run(documents,pages):
    return build_ios_applicability_candidates(documents,pages,_ios_inventory(documents))


def test_typed_source_and_object_candidate_is_only_for_specialist_review():
    documents,pages=_fixture()
    result=_run(documents,pages)
    assert result["state"]=="CANDIDATE_ONLY"
    assert result["promotion_policy"]=="HOLD"
    assert result["complete"] is False
    assert result["candidate_count"]==1
    assert result["rejected"]==[]
    item=result["candidates"][0]
    assert item["object_id"]=="OBJ-A"
    assert item["document"]=="Объект А/ИОС1.pdf"
    assert item["page"]==7
    assert item["subsection"]=="ИОС1"
    assert item["admission"]=="SPECIALIST_REVIEW_ONLY"
    assert item["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"


def test_unavailable_document_page_or_forged_quote_fails_closed():
    documents,pages=_fixture()
    for changed in (
        [{"document":"Объект Б/ИОС1.pdf","page":7,"text":pages[0]["text"]}],
        [{"document":"Объект А/ИОС1.pdf","page":8,"text":pages[0]["text"]}],
        [{"document":"Объект А/ИОС1.pdf","page":7,"text":"Совсем иное техническое содержание."}],
        [*pages,*pages],
    ):
        result=_run(documents,changed)
        assert result["candidate_count"]==0
        assert result["rejected"]


def test_duplicate_object_identifiers_are_not_source_owners():
    documents,pages=_fixture()
    model=documents[1]["project_understanding"]
    model["objects"].append({
        "object_id":"OBJ-A",
        "properties":{},
    })
    result=_run(documents,pages)
    assert result["candidate_count"]==0
    assert result["reason_code"]=="UNRESOLVED_OBJECT_IDENTITIES"


def test_same_page_claimed_by_two_objects_is_ambiguous_not_bound():
    documents,pages=_fixture()
    documents[1]["project_understanding"]["objects"].append({
        "object_id":"OBJ-B",
        "properties":{"other_property":[{
            "document":"Объект А/ИОС1.pdf","page":7,
        }]},
    })
    result=_run(documents,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="AMBIGUOUS_OBJECT_OWNER"


def test_source_identity_conflict_quarantines_candidate():
    documents,pages=_fixture()
    documents[0]["document_type"]="ИОС2"
    result=_run(documents,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="IOS_SOURCE_IDENTITY_NOT_PROVEN"


def test_claimed_subsection_must_match_loaded_source_identity():
    documents,pages=_fixture()
    claim=documents[1]["project_understanding"]["objects"][0]["properties"][
        "ios_subsection_applicability"
    ][0]
    claim["subsection"]="ИОС2"
    result=_run(documents,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="IOS_SUBSECTION_SOURCE_MISMATCH"


def test_candidate_emission_never_promotes_normative_set_completeness():
    documents,pages=_fixture()
    contract={
        "requirement_id":"PP87-CLAUSE-15-IOS",
        "evidence_contract":{"set_contract":{
            "mode":"APPLICABILITY_AWARE_INVENTORY","promotion_policy":"HOLD",
        }},
    }
    result=_set_completeness_evaluation(contract,pages,documents)
    assert result["complete"] is False
    assert result["promotion_policy"]=="HOLD"
    assert result["missing_ids"]==["APPLICABILITY_MAP_REQUIRED"]
    assert result["applicability_map_candidates"]["candidate_count"]==1
    assert result["evidence"]==[]


def test_absent_model_has_no_candidate_and_no_inferred_six_item_map():
    docs=[{"Файл":"Объект А/ИОС1.pdf","Тип документа":"ИОС1"}]
    page={"document":"Объект А/ИОС1.pdf","page":7,"text":"ИОС1"}
    result=_run(docs,[page])
    assert result["candidate_count"]==0
    assert result["reason_code"]=="NO_TYPED_PROJECT_APPLICABILITY_CLAIMS"
    assert result["complete"] is False


def test_conflicting_project_models_reject_map_without_choosing_one():
    docs,pages=_fixture()
    docs.append({"project_understanding":{"objects":[
        {"object_id":"OBJ-Z","properties":{}}
    ]}})
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["reason_code"]=="CONFLICTING_PROJECT_MODELS"


def test_same_filename_in_another_object_directory_cannot_replace_page():
    docs,pages=_fixture()
    changed=[{"document":"Объект Б/ИОС1.pdf","page":7,"text":pages[0]["text"]}]
    result=_run(docs,changed)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_NOT_UNIQUE"


def test_unrelated_legacy_project_property_does_not_generate_candidate():
    docs=[{"project_understanding":{"objects":[
        {"object_id":"OBJ-A","properties":{"ios":[
            {"subsection":"ИОС1","document":"ИОС1.pdf","page":1}
        ]}}
    ]}},{"Файл":"ИОС1.pdf","Тип документа":"ИОС1"}]
    result=_run(docs,[{"document":"ИОС1.pdf","page":1,"text":"ИОС1"}])
    assert result["candidate_count"]==0
    assert result["reason_code"]=="NO_TYPED_PROJECT_APPLICABILITY_CLAIMS"
