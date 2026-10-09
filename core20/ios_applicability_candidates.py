from __future__ import annotations

import re
from typing import Any


# Candidate retrieval is not evidence of normative applicability or completeness.
# Only the typed Project Understanding property below is considered.
PROPERTY_KEY="ios_subsection_applicability"
SECTION_PATTERN=re.compile(r"ИОС[1-9]\d*(?:\.\d+)*",re.IGNORECASE)


def _text(value:Any)->str:
    return " ".join(str(value or "").replace("ё","е").casefold().replace("\xa0"," ").split())


def _path(value:Any)->str:
    return re.sub(r"/+","/",_text(value).replace("\\","/"))


def _page_number(value:Any)->str:
    if isinstance(value,bool):
        return ""
    raw=str(value or "").strip()
    return str(int(raw)) if re.fullmatch(r"[1-9]\d*",raw) else ""


def _section_code(value:Any)->str:
    raw=str(value or "").strip().upper().replace(" ","")
    return raw if SECTION_PATTERN.fullmatch(raw) else ""


def build_ios_applicability_candidates(
    documents:list[dict[str,Any]]|None,
    pages:list[dict[str,Any]]|None,
    inventory:list[dict[str,Any]]|None,
)->dict[str,Any]:
    """Build *review-only* object/source-locked candidate records.

    No candidate, even a source-matched one, may prove a clause-15
    applicability decision. Owners and assertions come from the explicit
    Project Understanding model and require independent expert validation.
    """
    result:dict[str,Any]={
        "state":"CANDIDATE_ONLY",
        "promotion_policy":"HOLD",
        "complete":False,
        "candidate_count":0,
        "candidates":[],
        "rejected":[],
        "reason_code":"NO_TYPED_PROJECT_APPLICABILITY_CLAIMS",
    }
    project_models=[
        row["project_understanding"]
        for row in (documents or [])
        if isinstance(row,dict) and isinstance(row.get("project_understanding"),dict)
    ]
    if not project_models:
        return result
    if any(model!=project_models[0] for model in project_models[1:]):
        result["reason_code"]="CONFLICTING_PROJECT_MODELS"
        return result

    model=project_models[0]
    objects=[obj for obj in (model.get("objects") or []) if isinstance(obj,dict)]
    ids=[str(obj.get("object_id") or "").strip() for obj in objects]
    if not ids or any(not oid for oid in ids) or len(set(ids))!=len(ids):
        result["reason_code"]="UNRESOLVED_OBJECT_IDENTITIES"
        return result

    page_index:dict[tuple[str,str],list[str]]={}
    for page in (pages or []):
        if not isinstance(page,dict):
            continue
        document=_path(page.get("document") or page.get("Файл"))
        number=_page_number(page.get("page"))
        if document and number:
            page_index.setdefault((document,number),[]).append(
                str(page.get("text") or page.get("content") or "")
            )

    source_index:dict[str,list[dict[str,Any]]]={}
    for item in inventory or []:
        if isinstance(item,dict):
            key=_path(item.get("document"))
            if key:
                source_index.setdefault(key,[]).append(item)

    # A page listed under two separate objects cannot prove a unique
    # engineering owner. This is a diagnostic guard, not owner verification.
    page_owners:dict[tuple[str,str],set[str]]={}
    for obj,oid in zip(objects,ids):
        props=obj.get("properties") or {}
        if not isinstance(props,dict):
            continue
        for rows in props.values():
            if not isinstance(rows,list):
                continue
            for ev in rows:
                if not isinstance(ev,dict):
                    continue
                key=(_path(ev.get("document")),_page_number(ev.get("page")))
                if all(key):
                    page_owners.setdefault(key,set()).add(oid)

    seen:set[tuple[str,str,str,str]]=set()
    claims_found=0
    for obj,oid in zip(objects,ids):
        props=obj.get("properties") or {}
        records=(props.get(PROPERTY_KEY) or []) if isinstance(props,dict) else []
        if not isinstance(records,list):
            result["rejected"].append({
                "object_id":oid,"reason_code":"INVALID_TYPED_PROPERTY_SHAPE"
            })
            continue
        for ev in records:
            claims_found+=1
            if not isinstance(ev,dict):
                result["rejected"].append({
                    "object_id":oid,"reason_code":"INVALID_CANDIDATE_SHAPE"
                })
                continue

            doc=str(ev.get("document") or "").strip()
            pg=_page_number(ev.get("page"))
            code=_section_code(ev.get("subsection"))
            decision=str(ev.get("applicability") or "").strip().upper()
            fragment=str(ev.get("fragment") or "").strip()
            reject=""
            source_key=_path(doc)
            key=(source_key,pg)
            matched_source=source_index.get(source_key) or []
            page_texts=page_index.get(key) or []
            if not doc or not pg or not code or decision not in {"REQUIRED","NOT_REQUIRED"}:
                reject="INVALID_TYPED_APPLICABILITY_RECORD"
            elif len(matched_source)!=1 or matched_source[0].get("metadata_conflict"):
                reject="IOS_SOURCE_IDENTITY_NOT_PROVEN"
            elif code not in (matched_source[0].get("subsections") or []):
                reject="IOS_SUBSECTION_SOURCE_MISMATCH"
            elif len(page_texts)!=1:
                reject="SOURCE_PAGE_NOT_UNIQUE"
            elif len(page_owners.get(key,set()))!=1:
                reject="AMBIGUOUS_OBJECT_OWNER"
            elif not fragment or len(_text(fragment))<20 or _text(fragment) not in _text(page_texts[0]):
                reject="SOURCE_QUOTE_NOT_LOCATED"
            else:
                normalized_fragment=_text(fragment)
                if not re.search(
                    rf"(?<![а-яa-z0-9]){re.escape(code.casefold())}(?!\d|\.\d)",
                    normalized_fragment
                ):
                    reject="IOS_CODE_NOT_IN_SOURCE_QUOTE"

            if reject:
                result["rejected"].append({
                    "object_id":oid,
                    "document":doc,
                    "page":pg or None,
                    "subsection":code,
                    "reason_code":reject,
                })
                continue

            dedup=(oid,source_key,pg,code)
            if dedup in seen:
                result["rejected"].append({
                    "object_id":oid,"document":doc,"page":pg,
                    "subsection":code,"reason_code":"DUPLICATE_CANDIDATE"
                })
                continue
            seen.add(dedup)
            result["candidates"].append({
                "object_id":oid,
                "subsection":code,
                "applicability_claim":decision,
                "document":doc,
                "page":int(pg),
                "fragment":fragment,
                "source_state":"EXACT_PAGE_QUOTE_MATCHED",
                "owner_state":"PROJECT_UNDERSTANDING_CLAIM_ONLY",
                "admission":"SPECIALIST_REVIEW_ONLY",
            })

    result["candidate_count"]=len(result["candidates"])
    result["reason_code"]=(
        "REVIEW_ONLY_TYPED_CANDIDATES" if result["candidates"]
        else "TYPED_CLAIMS_REJECTED" if claims_found or result["rejected"]
        else "NO_TYPED_PROJECT_APPLICABILITY_CLAIMS"
    )
    return result
