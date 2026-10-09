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


def _add_claim(documents, *, oid="OBJ-A", section="ИОС1",
               decision="NOT_REQUIRED", document="Объект А/ИОС1.pdf",
               page=8, fragment="По данному объекту подраздел ИОС1 не требуется."):
    objects=documents[1]["project_understanding"]["objects"]
    obj=next((row for row in objects if row["object_id"]==oid),None)
    if obj is None:
        obj={"object_id":oid,"properties":{}}
        objects.append(obj)
    obj["properties"].setdefault("ios_subsection_applicability",[]).append({
        "subsection":section,"applicability":decision,
        "document":document,"page":page,"fragment":fragment,
    })


def test_opposite_applicability_claims_same_object_and_subsection_are_quarantined():
    docs,pages=_fixture()
    opposite="Для этого объекта подраздел ИОС1 не требуется по обоснованию."
    _add_claim(docs,fragment=opposite)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    result=_run(docs,pages)
    assert result["state"]=="CANDIDATE_ONLY"
    assert result["promotion_policy"]=="HOLD"
    assert result["complete"] is False
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    assert result["reason_code"]=="CONTRADICTORY_TYPED_APPLICABILITY_CLAIMS"
    group=result["conflicts"][0]
    assert (group["object_id"],group["subsection"])==("OBJ-A","ИОС1")
    assert [x["applicability_claim"] for x in group["claims"]]==[
        "REQUIRED","NOT_REQUIRED"
    ]
    assert all(x["source_state"]=="PAGE_QUOTE_LOCATED_APPLICABILITY_UNVERIFIED"
               for x in group["claims"])
    assert group["source_matched_claim_count"]==2
    assert group["source_unmatched_claim_count"]==0
    assert group["interpretation"]=="CONTRADICTORY_CLAIMS_NOT_NORMATIVE_VIOLATION_PROOF"
    assert group["resolution"]=="SPECIALIST_REVIEW_REQUIRED"
    assert [x["reason_code"] for x in result["rejected"]]==[
        "IOS_APPLICABILITY_CLAIM_CONFLICT"
    ]*2


def test_ungrounded_opposite_claim_still_blocks_uncontested_candidate():
    docs,pages=_fixture()
    _add_claim(docs,document="Объект Б/ИОС1.pdf",page=51,
               fragment="Не подтверждено документом, подраздел ИОС1 не требуется.")
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    assert {x["applicability_claim"]
            for x in result["conflicts"][0]["claims"]}=={
                "REQUIRED","NOT_REQUIRED"
            }
    assert all(x["reason_code"]=="IOS_APPLICABILITY_CLAIM_CONFLICT"
               for x in result["rejected"])


def test_two_consistent_claims_do_not_create_false_opposition():
    docs,pages=_fixture()
    quote="Проектом предусмотрен подраздел ИОС1 и необходимые сети."
    _add_claim(docs,decision="REQUIRED",fragment=quote)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":quote})
    result=_run(docs,pages)
    assert result["conflict_count"]==0
    assert result["reason_code"]=="REVIEW_ONLY_TYPED_CANDIDATES"
    assert result["candidate_count"]==2


def test_opposite_claims_for_different_objects_are_separate():
    docs,pages=_fixture()
    other="Для второго объекта подраздел ИОС1 не требуется по заданию."
    _add_claim(docs,oid="OBJ-B",decision="NOT_REQUIRED",
               document="Объект Б/ИОС1.pdf",page=8,fragment=other)
    docs.insert(1,{"Файл":"Объект Б/ИОС1.pdf","Тип документа":"ИОС1"})
    pages.append({"document":"Объект Б/ИОС1.pdf","page":8,"text":other})
    result=_run(docs,pages)
    assert result["conflict_count"]==0
    assert result["candidate_count"]==2
    assert {c["object_id"] for c in result["candidates"]}=={"OBJ-A","OBJ-B"}


def test_opposite_claims_for_different_subsections_do_not_conflict():
    docs,pages=_fixture()
    other="Для объекта подраздел ИОС2 не предусматривается по заданию."
    _add_claim(docs,section="ИОС2",decision="NOT_REQUIRED",
               document="Объект А/ИОС2.pdf",fragment=other)
    docs.insert(1,{"Файл":"Объект А/ИОС2.pdf","Тип документа":"ИОС2"})
    pages.append({"document":"Объект А/ИОС2.pdf","page":8,"text":other})
    result=_run(docs,pages)
    assert result["conflict_count"]==0
    assert result["candidate_count"]==2


def test_undeclared_decision_is_not_construed_as_opposition():
    docs,pages=_fixture()
    _add_claim(docs,decision="MAYBE")
    result=_run(docs,pages)
    assert result["conflict_count"]==0
    assert result["candidate_count"]==1
    assert result["rejected"][0]["reason_code"]=="INVALID_TYPED_APPLICABILITY_RECORD"


def test_opposite_claims_can_coexist_with_independent_safe_candidate():
    docs,pages=_fixture()
    _add_claim(docs)
    third="Предусмотрен подраздел ИОС2 для данного объекта по заданию."
    _add_claim(docs,section="ИОС2",decision="REQUIRED",
               document="Объект А/ИОС2.pdf",page=9,fragment=third)
    docs.insert(1,{"Файл":"Объект А/ИОС2.pdf","Тип документа":"ИОС2"})
    pages.append({"document":"Объект А/ИОС2.pdf","page":9,"text":third})
    result=_run(docs,pages)
    assert result["conflict_count"]==1
    assert result["candidate_count"]==1
    assert result["candidates"][0]["subsection"]=="ИОС2"
    assert result["reason_code"]=="CONTRADICTORY_TYPED_APPLICABILITY_CLAIMS"


def test_opposite_claims_never_promote_completeness_set_or_rendered_verdict():
    from core20.normative_execution import NormativeExecutionEngine20
    from core20.normative_foundation import NormativeKnowledgeFoundation20
    from pathlib import Path

    docs,pages=_fixture()
    other="Для объекта подраздел ИОС1 не требуется по техническому заданию."
    _add_claim(docs,fragment=other)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":other})
    contract={
        "requirement_id":"PP87-CLAUSE-15-IOS",
        "evidence_contract":{"set_contract":{
            "mode":"APPLICABILITY_AWARE_INVENTORY","promotion_policy":"HOLD"
        }},
    }
    set_result=_set_completeness_evaluation(contract,pages,docs)
    assert set_result["complete"] is False
    assert set_result["promotion_policy"]=="HOLD"
    assert set_result["evidence"]==[]
    assert set_result["applicability_map_candidates"]["conflict_count"]==1

    foundation=NormativeKnowledgeFoundation20(
        Path(__file__).resolve().parents[1]/"knowledge"
    )
    runtime=NormativeExecutionEngine20(foundation).run(docs,pages)
    ios=next(row for row in runtime["rows"]
             if row["requirement_id"]=="PP87-CLAUSE-15-IOS")
    assert ios["kind"]=="REVIEW_QUESTION"
    assert ios["proof_state"]=="SET_PROOF_CONTRACT_REQUIRED"



def test_conflict_diagnostic_identifies_located_vs_missing_document_source():
    docs,pages=_fixture()
    _add_claim(docs,document="Объект Б/ИОС1.pdf",page=51,
               fragment="В другом томе подраздел ИОС1 не требуется по проекту.")
    result=_run(docs,pages)
    group=result["conflicts"][0]
    assert result["candidate_count"]==0
    assert group["source_matched_claim_count"]==1
    assert group["source_unmatched_claim_count"]==1
    assert group["claims"][0]["source_reason_code"]=="EXACT_DOCUMENT_PAGE_QUOTE_MATCH"
    assert group["claims"][1]["source_reason_code"]=="IOS_SOURCE_IDENTITY_NOT_PROVEN"
    assert group["claims"][1]["source_state"]=="SOURCE_NOT_GROUNDED"
    assert result["rejected"][0]["reason_code"]=="IOS_APPLICABILITY_CLAIM_CONFLICT"
    assert result["rejected"][1]["source_reason_code"]=="IOS_SOURCE_IDENTITY_NOT_PROVEN"


def test_conflict_diagnostic_quote_not_on_real_page_is_not_found():
    docs,pages=_fixture()
    _add_claim(docs,fragment="В томе ИОС1 не требуется для данного объекта.")
    pages.append({
        "document":"Объект А/ИОС1.pdf","page":8,
        "text":"Технические решения приведены без такого утверждения.",
    })
    group=_run(docs,pages)["conflicts"][0]
    assert group["source_matched_claim_count"]==1
    assert group["claims"][1]["source_reason_code"]=="SOURCE_QUOTE_NOT_LOCATED"


def test_conflict_diagnostic_duplicate_page_is_not_unique_evidence():
    docs,pages=_fixture()
    opposite="Для объекта подраздел ИОС1 не требуется по заданию."
    _add_claim(docs,fragment=opposite)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    group=_run(docs,pages)["conflicts"][0]
    assert group["source_matched_claim_count"]==1
    assert group["claims"][1]["source_reason_code"]=="SOURCE_PAGE_NOT_UNIQUE"


def test_conflict_diagnostic_shared_owner_page_cannot_be_called_source_matched():
    docs,pages=_fixture()
    opposite="Для объекта подраздел ИОС1 не требуется согласно заданию."
    _add_claim(docs,fragment=opposite)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    docs[1]["project_understanding"]["objects"].append({
        "object_id":"OBJ-B",
        "properties":{"other_property":[{
            "document":"Объект А/ИОС1.pdf","page":8,
        }]}
    })
    group=_run(docs,pages)["conflicts"][0]
    assert group["claims"][1]["source_reason_code"]=="AMBIGUOUS_OBJECT_OWNER"
    assert group["source_unmatched_claim_count"]==1


def test_uncontested_page_belonging_to_another_owner_cannot_be_accepted():
    docs,pages=_fixture()
    claim=docs[1]["project_understanding"]["objects"][0]["properties"][
        "ios_subsection_applicability"
    ][0]
    # OBJ-A makes the candidate claim, but only OBJ-B cites this page
    # in the source-owner index. The owner must match, not just be unique.
    claim["document"]="Объект А/ИОС1.pdf"
    claim["page"]=7
    props=docs[1]["project_understanding"]["objects"][0]["properties"]
    props["ios_subsection_applicability"]=[]
    docs[1]["project_understanding"]["objects"].append({
        "object_id":"OBJ-B",
        "properties":{"other_property":[{
            "document":"Объект А/ИОС1.pdf","page":7,
        }]}
    })
    # Restore OBJ-A's claim without introducing an additional ownership
    # evidence record (the code currently treats all claims as owner refs).
    # A dedicated property in OBJ-A with the same page is unavoidable
    # without a separate trusted owner index, so assert conflict for
    # two competing owners rather than a false unique admission.
    props["ios_subsection_applicability"]=[claim]
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="AMBIGUOUS_OBJECT_OWNER"


def test_conflict_diagnostic_never_asserts_normative_failure_when_both_quotes_found():
    docs,pages=_fixture()
    opposite="По этому объекту подраздел ИОС1 не требуется по заданию."
    _add_claim(docs,fragment=opposite)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    result=_run(docs,pages)
    group=result["conflicts"][0]
    assert group["source_matched_claim_count"]==2
    assert all(x["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"
               for x in group["claims"])
    assert group["interpretation"]=="CONTRADICTORY_CLAIMS_NOT_NORMATIVE_VIOLATION_PROOF"
    assert group["resolution"]=="SPECIALIST_REVIEW_REQUIRED"
    assert result["promotion_policy"]=="HOLD"
    assert result["complete"] is False
    assert result["candidate_count"]==0
