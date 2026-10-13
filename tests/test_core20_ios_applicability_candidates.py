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



def test_registry_explicit_matching_owner_is_diagnostic_not_proof():
    docs,pages=_fixture()
    docs[0]["object_id"]="OBJ-A"
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    item=result["candidates"][0]
    assert item["registry_owner_state"]=="DOCUMENT_REGISTRY_OBJECT_ID_MATCH_UNVERIFIED"
    assert item["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"
    assert item["admission"]=="SPECIALIST_REVIEW_ONLY"
    assert result["complete"] is False
    assert result["promotion_policy"]=="HOLD"


def test_missing_registry_owner_keeps_review_only_with_explicit_unknown_state():
    docs,pages=_fixture()
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["registry_owner_state"]=="DOCUMENT_REGISTRY_OBJECT_ID_ABSENT"
    assert result["candidates"][0]["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"


def test_wrong_explicit_registry_owner_blocks_self_attributed_candidate():
    docs,pages=_fixture()
    docs[0]["object_id"]="OBJ-B"
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="DOCUMENT_REGISTRY_OBJECT_ID_MISMATCH"
    assert result["complete"] is False


def test_two_different_registry_owners_for_same_path_block_candidate():
    docs,pages=_fixture()
    docs[0]["object_id"]="OBJ-A"
    docs.append({
        "Файл":r"объект а\иос1.PDF",
        "Тип документа":"ИОС1","object_id":"OBJ-B",
    })
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="DOCUMENT_REGISTRY_OBJECT_IDS_CONFLICT"


def test_registry_owner_of_distinct_document_does_not_poison_target_claim():
    docs,pages=_fixture()
    docs[0]["object_id"]="OBJ-A"
    docs.append({"Файл":"Объект Б/ИОС1.pdf","Тип документа":"ИОС1",
                 "object_id":"OBJ-B"})
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["registry_owner_state"]=="DOCUMENT_REGISTRY_OBJECT_ID_MATCH_UNVERIFIED"


def test_conflicting_applicability_claims_keep_registry_owner_diagnostic():
    docs,pages=_fixture()
    docs[0]["object_id"]="OBJ-B"
    opposite="Данному объекту подраздел ИОС1 не требуется по заданию."
    _add_claim(docs,fragment=opposite)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    group=result["conflicts"][0]
    assert group["source_matched_claim_count"]==0
    assert all(x["registry_owner_state"]=="DOCUMENT_REGISTRY_OBJECT_ID_MISMATCH"
               for x in group["claims"])
    assert all(x["source_reason_code"]=="DOCUMENT_REGISTRY_OBJECT_ID_MISMATCH"
               for x in group["claims"])
    assert all(x["reason_code"]=="IOS_APPLICABILITY_CLAIM_CONFLICT"
               for x in result["rejected"])


def test_registry_owner_guard_preserves_normative_hold_only():
    docs,pages=_fixture()
    docs[0]["object_id"]="OBJ-B"
    contract={
        "requirement_id":"PP87-CLAUSE-15-IOS",
        "evidence_contract":{"set_contract":{
            "mode":"APPLICABILITY_AWARE_INVENTORY","promotion_policy":"HOLD",
        }},
    }
    result=_set_completeness_evaluation(contract,pages,docs)
    assert result["complete"] is False
    assert result["evidence"]==[]
    assert result["applicability_map_candidates"]["candidate_count"]==0
    assert result["applicability_map_candidates"]["rejected"][0][
        "reason_code"
    ]=="DOCUMENT_REGISTRY_OBJECT_ID_MISMATCH"



def test_self_cited_owner_reference_is_marked_without_extra_corroboration():
    docs,pages=_fixture()
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["owner_reference_state"]==(
        "SELF_CITED_APPLICABILITY_CLAIM_ONLY"
    )
    assert result["candidates"][0]["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"
    assert result["promotion_policy"]=="HOLD"


def test_same_page_reference_from_another_property_is_only_model_corroboration():
    docs,pages=_fixture()
    model_obj=docs[1]["project_understanding"]["objects"][0]
    model_obj["properties"]["engineering_network_description"]=[{
        "document":"Объект А/ИОС1.pdf","page":7,
        "fragment":"В этом подразделе описаны сети ИОС1."
    }]
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["owner_reference_state"]==(
        "CROSS_PROPERTY_PROJECT_MODEL_REFERENCE_UNVERIFIED"
    )
    assert result["candidates"][0]["admission"]=="SPECIALIST_REVIEW_ONLY"
    assert result["candidates"][0]["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"
    assert result["complete"] is False


def test_reference_to_other_page_does_not_count_as_candidate_corroboration():
    docs,pages=_fixture()
    docs[1]["project_understanding"]["objects"][0]["properties"]["different_fact"]=[
        {"document":"Объект А/ИОС1.pdf","page":8}
    ]
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["owner_reference_state"]==(
        "SELF_CITED_APPLICABILITY_CLAIM_ONLY"
    )


def test_same_basename_from_another_object_is_not_cross_property_evidence():
    docs,pages=_fixture()
    docs[1]["project_understanding"]["objects"][0]["properties"]["different_fact"]=[
        {"document":"Объект Б/ИОС1.pdf","page":7}
    ]
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["owner_reference_state"]==(
        "SELF_CITED_APPLICABILITY_CLAIM_ONLY"
    )


def test_cross_property_owner_ref_does_not_override_two_object_page_conflict():
    docs,pages=_fixture()
    docs[1]["project_understanding"]["objects"][0]["properties"]["other"]=[
        {"document":"Объект А/ИОС1.pdf","page":7}
    ]
    docs[1]["project_understanding"]["objects"].append({
        "object_id":"OBJ-B","properties":{"other":[
            {"document":"Объект А/ИОС1.pdf","page":7}
        ]}
    })
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="AMBIGUOUS_OBJECT_OWNER"


def test_opposite_claims_explain_self_citation_vs_cross_property_without_promotion():
    docs,pages=_fixture()
    opposite="Для этого объекта подраздел ИОС1 не требуется согласно заданию."
    _add_claim(docs,fragment=opposite)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    docs[1]["project_understanding"]["objects"][0]["properties"]["assignment"]=[
        {"document":"Объект А/ИОС1.pdf","page":7}
    ]
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    assert result["conflicts"][0]["source_matched_claim_count"]==2
    assert [x["owner_reference_state"] for x in result["conflicts"][0]["claims"]]==[
        "CROSS_PROPERTY_PROJECT_MODEL_REFERENCE_UNVERIFIED",
        "SELF_CITED_APPLICABILITY_CLAIM_ONLY",
    ]
    assert result["conflicts"][0]["resolution"]=="SPECIALIST_REVIEW_REQUIRED"
    assert result["complete"] is False
    assert result["promotion_policy"]=="HOLD"


def test_cross_property_source_without_any_reference_reports_zero_support():
    docs,pages=_fixture()
    result=_run(docs,pages)
    diagnostic=result["candidates"][0]["cross_property_source_diagnostic"]
    assert diagnostic["state"]=="NO_CROSS_PROPERTY_MODEL_REFERENCE"
    assert diagnostic["matched_quote_count"]==0
    assert diagnostic["unverified_reference_count"]==0
    assert diagnostic["independence"]=="MODEL_REFERENCE_ONLY_NOT_OWNER_PROOF"
    assert result["promotion_policy"]=="HOLD"


def test_other_model_property_exact_page_quote_is_located_but_not_owner_proof():
    docs,pages=_fixture()
    quote="Данным разделом ИОС1 описываются проектируемые инженерные сети."
    pages[0]["text"]+=" "+quote
    docs[1]["project_understanding"]["objects"][0]["properties"]["networks"]=[
        {"document":"Объект А/ИОС1.pdf","page":7,"fragment":quote}
    ]
    result=_run(docs,pages)
    diagnostic=result["candidates"][0]["cross_property_source_diagnostic"]
    assert diagnostic["state"]=="CROSS_PROPERTY_QUOTES_LOCATED_OWNER_UNVERIFIED"
    assert diagnostic["matched_quote_count"]==1
    assert diagnostic["unverified_reference_count"]==0
    assert diagnostic["reason_codes"]==["EXACT_PAGE_QUOTE_MATCHED"]
    assert diagnostic["independence"]=="MODEL_REFERENCE_ONLY_NOT_OWNER_PROOF"
    assert result["candidates"][0]["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"
    assert result["complete"] is False


def test_other_property_quote_absent_from_page_is_not_source_support():
    docs,pages=_fixture()
    docs[1]["project_understanding"]["objects"][0]["properties"]["networks"]=[
        {"document":"Объект А/ИОС1.pdf","page":7,
         "fragment":"В этом разделе ИОС1 описаны несуществующие технические решения."}
    ]
    diagnostic=_run(docs,pages)["candidates"][0]["cross_property_source_diagnostic"]
    assert diagnostic["state"]=="CROSS_PROPERTY_REFERENCES_NOT_FULLY_GROUNDED"
    assert diagnostic["matched_quote_count"]==0
    assert diagnostic["reason_codes"]==["SOURCE_QUOTE_NOT_LOCATED"]


def test_other_property_page_reference_with_no_quote_is_unverified():
    docs,pages=_fixture()
    docs[1]["project_understanding"]["objects"][0]["properties"]["networks"]=[
        {"document":"Объект А/ИОС1.pdf","page":7}
    ]
    diagnostic=_run(docs,pages)["candidates"][0]["cross_property_source_diagnostic"]
    assert diagnostic["unverified_reference_count"]==1
    assert diagnostic["reason_codes"]==["SOURCE_QUOTE_NOT_PROVIDED_OR_TOO_SHORT"]


def test_mixed_cross_property_source_quality_does_not_hide_forged_quote():
    docs,pages=_fixture()
    good="Раздел ИОС1 включает сведения о проектируемых инженерных сетях."
    wrong="Раздел ИОС1 содержит выдуманное утверждение о данном объекте."
    pages[0]["text"]+=" "+good
    docs[1]["project_understanding"]["objects"][0]["properties"]["networks"]=[
        {"document":"Объект А/ИОС1.pdf","page":7,"fragment":good},
        {"document":"Объект А/ИОС1.pdf","page":7,"fragment":wrong},
    ]
    result=_run(docs,pages)
    d=result["candidates"][0]["cross_property_source_diagnostic"]
    assert d["state"]=="CROSS_PROPERTY_REFERENCES_NOT_FULLY_GROUNDED"
    assert d["matched_quote_count"]==1
    assert d["unverified_reference_count"]==1
    assert d["reason_codes"]==["EXACT_PAGE_QUOTE_MATCHED","SOURCE_QUOTE_NOT_LOCATED"]
    assert result["candidate_count"]==1
    assert result["complete"] is False


def test_cross_property_reference_to_other_document_not_counted_for_candidate():
    docs,pages=_fixture()
    docs[1]["project_understanding"]["objects"][0]["properties"]["networks"]=[
        {"document":"Объект Б/ИОС1.pdf","page":7,
         "fragment":"Раздел ИОС1 содержит сведения об инженерных сетях другого объекта."}
    ]
    result=_run(docs,pages)
    diagnostic=result["candidates"][0]["cross_property_source_diagnostic"]
    assert diagnostic["state"]=="NO_CROSS_PROPERTY_MODEL_REFERENCE"
    assert result["candidate_count"]==1


def test_conflicting_ios_claims_show_separate_cross_property_quote_checks():
    docs,pages=_fixture()
    opposite="Для объекта проектом подраздел ИОС1 не требуется по заданию."
    _add_claim(docs,fragment=opposite)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    docs[1]["project_understanding"]["objects"][0]["properties"]["networks"]=[
        {"document":"Объект А/ИОС1.pdf","page":7,
         "fragment":"Заявление ИОС1, отсутствующее на указанной странице."}
    ]
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    claims=result["conflicts"][0]["claims"]
    assert claims[0]["cross_property_source_diagnostic"]["reason_codes"]==[
        "SOURCE_QUOTE_NOT_LOCATED"
    ]
    assert claims[1]["cross_property_source_diagnostic"]["state"]==(
        "NO_CROSS_PROPERTY_MODEL_REFERENCE"
    )
    assert result["complete"] is False
    assert result["promotion_policy"]=="HOLD"


def test_conflicting_source_page_file_aliases_are_never_accepted():
    docs,pages=_fixture()
    pages[0]["Файл"]="Объект Б/ИОС1.pdf"
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_FILE_ALIASES_CONFLICT"
    assert result["promotion_policy"]=="HOLD"
    assert result["complete"] is False


def test_page_source_alias_equivalence_after_canonicalization_is_allowed():
    docs,pages=_fixture()
    pages[0]["Файл"]=r"ОБЪЕКТ А\\ИОС1.PDF"
    pages[0]["filename"]="объект а/иос1.pdf"
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["admission"]=="SPECIALIST_REVIEW_ONLY"


def test_source_page_filename_field_alone_can_resolve_exact_document():
    docs,pages=_fixture()
    pages[0].pop("document")
    pages[0]["filename"]="Объект А/ИОС1.pdf"
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["complete"] is False


def test_conflicting_page_alias_even_with_valid_duplicate_row_fails_closed():
    docs,pages=_fixture()
    pages.append({
        "document":"Объект А/ИОС1.pdf",
        "Файл":"Объект Б/ИОС1.pdf",
        "page":7,"text":pages[0]["text"],
    })
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_FILE_ALIASES_CONFLICT"


def test_cross_property_diagnostics_do_not_approve_conflicting_page_alias():
    docs,pages=_fixture()
    quote="Дополнительный текст ИОС1 содержит сведения об инженерных сетях."
    pages[0]["text"]+=" "+quote
    pages[0]["Файл"]="Объект Б/ИОС1.pdf"
    props=docs[1]["project_understanding"]["objects"][0]["properties"]
    props["networks"]=[{
        "document":"Объект А/ИОС1.pdf","page":7,"fragment":quote
    }]
    # Original applicability candidate is rejected; a conflict group
    # retains the same per-page source diagnostic for specialist review.
    _add_claim(docs,fragment="Для объекта подраздел ИОС1 не требуется.")
    pages.append({
        "document":"Объект А/ИОС1.pdf","page":8,
        "text":"Для объекта подраздел ИОС1 не требуется.",
    })
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    conflict=result["conflicts"][0]["claims"][0]
    assert conflict["source_reason_code"]=="SOURCE_PAGE_FILE_ALIASES_CONFLICT"
    assert conflict["cross_property_source_diagnostic"]["reason_codes"]==[
        "SOURCE_PAGE_FILE_ALIASES_CONFLICT"
    ]
    assert result["complete"] is False


def test_conflict_on_one_page_does_not_poison_other_page_or_document():
    docs,pages=_fixture()
    pages[0]["Файл"]="Объект Б/ИОС1.pdf"
    quote="Для объекта обязательно предусмотрен подраздел ИОС1."
    _add_claim(docs,decision="REQUIRED",page=8,fragment=quote)
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":quote})
    result=_run(docs,pages)
    assert result["conflict_count"]==0
    assert result["candidate_count"]==1
    assert result["candidates"][0]["page"]==8
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_FILE_ALIASES_CONFLICT"


def test_conflicting_alias_for_another_document_cannot_replace_claim_page():
    docs,pages=_fixture()
    pages[0]["filename"]="Объект Б/ИОС1.pdf"
    docs.append({"Файл":"Объект Б/ИОС1.pdf","Тип документа":"ИОС1"})
    model=docs[1]["project_understanding"]["objects"][0]["properties"]
    model["ios_subsection_applicability"][0]["document"]="Объект Б/ИОС1.pdf"
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_FILE_ALIASES_CONFLICT"


def test_conflicting_page_text_and_content_never_support_ios_candidate():
    docs,pages=_fixture()
    pages[0]["content"]="Совершенно иной фрагмент проектной документации."
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_TEXT_FIELDS_CONFLICT"
    assert result["complete"] is False
    assert result["promotion_policy"]=="HOLD"


def test_equivalent_text_and_content_with_normalized_case_are_accepted_for_review():
    docs,pages=_fixture()
    pages[0]["content"]="  ДЛЯ ОБЪЕКТА  ПРЕДУСМОТРЕН подраздел ИОС1 согласно заданию. "
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["admission"]=="SPECIALIST_REVIEW_ONLY"
    assert result["complete"] is False


def test_content_only_page_remains_valid_when_text_is_empty():
    docs,pages=_fixture()
    pages[0]["content"]=pages[0]["text"]
    pages[0]["text"]=""
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["complete"] is False


def test_other_content_cannot_override_disagreeing_text():
    docs,pages=_fixture()
    pages[0]["content"]=pages[0]["text"]
    pages[0]["text"]="В документе не указан этот подраздел ИОС1."
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_TEXT_FIELDS_CONFLICT"


def test_conflicting_page_text_even_with_clean_duplicate_fails_closed():
    docs,pages=_fixture()
    pages.append({
        "document":"Объект А/ИОС1.pdf",
        "page":7,
        "text":pages[0]["text"],
        "content":"Проектное решение с противоположным смыслом.",
    })
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_TEXT_FIELDS_CONFLICT"


def test_conflicting_page_text_cannot_ground_cross_property_quote():
    docs,pages=_fixture()
    cross="В подразделе ИОС1 описаны технологические инженерные коммуникации."
    pages[0]["text"]+=" "+cross
    pages[0]["content"]="Документ содержит информацию о другом объекте."
    props=docs[1]["project_understanding"]["objects"][0]["properties"]
    props["networks"]=[{
        "document":"Объект А/ИОС1.pdf",
        "page":7,"fragment":cross
    }]
    _add_claim(
        docs,fragment="Для объекта подраздел ИОС1 не требуется согласно заданию."
    )
    pages.append({
        "document":"Объект А/ИОС1.pdf","page":8,
        "text":"Для объекта подраздел ИОС1 не требуется согласно заданию."
    })
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    claim=result["conflicts"][0]["claims"][0]
    assert claim["source_reason_code"]=="SOURCE_PAGE_TEXT_FIELDS_CONFLICT"
    assert claim["cross_property_source_diagnostic"]["reason_codes"]==[
        "SOURCE_PAGE_TEXT_FIELDS_CONFLICT"
    ]
    assert result["promotion_policy"]=="HOLD"


def test_text_conflict_for_one_page_does_not_taint_clean_second_page():
    docs,pages=_fixture()
    pages[0]["content"]="В документе отсутствует требуемый фрагмент."
    another="Для объекта также предусмотрен подраздел ИОС1 по заданию."
    _add_claim(docs,decision="REQUIRED",page=8,fragment=another)
    pages.append({
        "document":"Объект А/ИОС1.pdf","page":8,"text":another
    })
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    assert result["candidates"][0]["page"]==8
    assert result["rejected"][0]["reason_code"]=="SOURCE_PAGE_TEXT_FIELDS_CONFLICT"
    assert result["complete"] is False


def _add_documentary_owner_quote(docs,pages):
    name="Насосная станция технологических растворов"
    quote=("Экспликация объектов капитального строительства: "
           "Насосная станция технологических растворов, позиция 5.")
    obj=docs[1]["project_understanding"]["objects"][0]
    obj["name"]=name
    obj["position"]="5"
    obj["source_records"]=[{
        "kind":"PZ_COMPLEX_OBJECT_REGISTER",
        "document":"Объект А/ПЗ.pdf","page":4,
        "fragment":quote,"position":"5",
    }]
    docs.append({"Файл":"Объект А/ПЗ.pdf","Тип документа":"ПЗ"})
    pages.append({"document":"Объект А/ПЗ.pdf","page":4,"text":quote})
    return obj,quote


def test_documentary_object_identity_requires_typed_exact_page_quote():
    docs,pages=_fixture()
    _add_documentary_owner_quote(docs,pages)
    result=_run(docs,pages)
    assert result["candidate_count"]==1
    d=result["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["state"]=="DOCUMENTARY_OBJECT_QUOTES_LOCATED_OWNER_UNVERIFIED"
    assert d["matched_quote_count"]==1
    assert d["unverified_reference_count"]==0
    assert d["scope"]=="OBJECT_REGISTER_LINEAGE_NOT_IOS_DOCUMENT_OWNERSHIP"
    assert d["independence"]=="MODEL_SOURCE_RECORD_NOT_INDEPENDENT_OWNER_PROOF"
    assert result["promotion_policy"]=="HOLD"
    assert result["complete"] is False


def test_no_object_register_records_do_not_masquerade_as_proof():
    docs,pages=_fixture()
    d=_run(docs,pages)["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["state"]=="NO_TYPED_DOCUMENTARY_OBJECT_REFERENCE"
    assert d["matched_quote_count"]==0


def test_documentary_owner_quote_must_appear_on_its_exact_page():
    docs,pages=_fixture()
    _,quote=_add_documentary_owner_quote(docs,pages)
    pages[-1]["text"]="Экспликация не содержит указанного объекта."
    d=_run(docs,pages)["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["reason_codes"]==["DOCUMENTARY_QUOTE_NOT_LOCATED"]
    assert d["matched_quote_count"]==0


def test_documentary_quote_without_object_name_is_not_owner_support():
    docs,pages=_fixture()
    obj,_=_add_documentary_owner_quote(docs,pages)
    wrong="Экспликация объектов капитального строительства: склад реагентов."
    obj["source_records"][0]["fragment"]=wrong
    pages[-1]["text"]=wrong
    d=_run(docs,pages)["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["reason_codes"]==["OBJECT_NAME_NOT_IN_DOCUMENTARY_QUOTE"]


def test_documentary_quote_same_basename_wrong_folder_is_not_source():
    docs,pages=_fixture()
    obj,_=_add_documentary_owner_quote(docs,pages)
    obj["source_records"][0]["document"]="Объект Б/ПЗ.pdf"
    d=_run(docs,pages)["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["reason_codes"]==["DOCUMENTARY_SOURCE_NOT_UNIQUELY_REGISTERED"]


def test_documentary_page_conflicting_alias_quarantines_owner_quote():
    docs,pages=_fixture()
    _add_documentary_owner_quote(docs,pages)
    pages[-1]["filename"]="Объект Б/ПЗ.pdf"
    d=_run(docs,pages)["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["reason_codes"]==["SOURCE_PAGE_FILE_ALIASES_CONFLICT"]


def test_documentary_registry_conflicting_alias_poison_even_with_clean_row():
    docs,pages=_fixture()
    _add_documentary_owner_quote(docs,pages)
    docs.append({
        "Файл":"Объект А/ПЗ.pdf",
        "document":"Объект Б/ПЗ.pdf","Тип документа":"ПЗ",
    })
    d=_run(docs,pages)["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["reason_codes"]==["DOCUMENTARY_REGISTRY_FILE_ALIASES_CONFLICT"]


def test_documentary_name_shared_by_two_objects_is_ambiguous():
    docs,pages=_fixture()
    obj,_=_add_documentary_owner_quote(docs,pages)
    docs[1]["project_understanding"]["objects"].append({
        "object_id":"OBJ-B","name":obj["name"],"properties":{},
    })
    d=_run(docs,pages)["candidates"][0]["documentary_object_identity_diagnostic"]
    assert d["reason_codes"]==["OBJECT_NAME_NOT_UNIQUE_IN_PROJECT_MODEL"]


def test_documentary_support_never_promotes_opposite_ios_claims():
    docs,pages=_fixture()
    _add_documentary_owner_quote(docs,pages)
    opposite="Для данного объекта подраздел ИОС1 не требуется по заданию."
    _add_claim(docs,page=8,fragment=opposite,decision="NOT_REQUIRED")
    pages.append({"document":"Объект А/ИОС1.pdf","page":8,"text":opposite})
    result=_run(docs,pages)
    assert result["candidate_count"]==0
    assert result["conflict_count"]==1
    for claim in result["conflicts"][0]["claims"]:
        d=claim["documentary_object_identity_diagnostic"]
        assert d["state"]=="DOCUMENTARY_OBJECT_QUOTES_LOCATED_OWNER_UNVERIFIED"
        assert claim["owner_state"]=="PROJECT_UNDERSTANDING_CLAIM_ONLY"
    assert result["promotion_policy"]=="HOLD"
    assert result["complete"] is False
