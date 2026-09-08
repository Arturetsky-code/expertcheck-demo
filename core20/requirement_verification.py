from __future__ import annotations

from math import isclose
import re
from typing import Any

from .model import CanonicalProject, Requirement


DESIGN_MARKERS = (
    "предусмотр", "проектом", "принят", "выполнен", "выполнена",
    "оборудуется", "ограждается", "устанавливается", "размещается",
    "осуществляется", "обеспечивается",
)

STOP_WORDS = {
    "проект", "проектом", "проектной", "документации", "требование",
    "предусмотреть", "обеспечить", "выполнить", "принять", "разработать",
    "должен", "должна", "должны", "необходимо", "объект", "площадка",
    "согласно", "заказчик", "часть",
}

CONCEPT_ANCHORS = {
    "FENCING": ("ограж", "ворот", "калит"),
    "FLOOD_PROTECTION": ("подтоп", "водоотвед", "нагорн"),
    "INTERNAL_ROADS": ("проезд", "дорог"),
    "SITE_LIGHTING": ("освещ", "светиль"),
    "GROUNDING_LIGHTNING": ("зазем", "молни"),
    "VIDEO_SURVEILLANCE": ("видеонаблюд", "камер"),
    "WASTEWATER_SYSTEMS": ("канализац", "водоотвед", "сток"),
    "PERSONNEL_AND_VEHICLE_ACCESS": ("проезд", "проход", "лестниц"),
}


def _norm(value: Any) -> str:
    return " ".join(
        str(value or "").replace("ё", "е").casefold().replace("\xa0", " ").split()
    )


def _unit(value: Any) -> str:
    text=_norm(value).replace(" ", "").replace("²","2").replace("^2","2").replace("³","3")
    aliases={
        "м2":"m2","m2":"m2","м.кв.":"m2","кв.м":"m2",
        "м3":"m3","m3":"m3",
        "мм":"mm","mm":"mm","см":"cm","cm":"cm","м":"m","m":"m",
        "квт":"kw","kw":"kw","мпа":"mpa","mpa":"mpa",
        "т/ч":"t/h","тч":"t/h","t/h":"t/h",
        "шт":"pcs","pcs":"pcs",
    }
    return aliases.get(text,text)


def _numeric(value: Any) -> float | None:
    if isinstance(value,(int,float)):
        return float(value)
    text=str(value or "").strip().replace("\xa0"," ").replace(",",".")
    if not text:
        return None
    match=re.search(r"[-+]?\d+(?:\.\d+)?",text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _stems(text: str) -> set[str]:
    words=re.findall(r"[a-zа-я0-9-]{5,}",_norm(text))
    out=set()
    for word in words:
        if word in STOP_WORDS or word.isdigit():
            continue
        out.add(word[:max(5,min(8,len(word)))])
    return out


def _section_matches(section: str, routes: list[str]) -> bool:
    if not routes:
        return True
    low=_norm(section)
    return any(_norm(route) in low or low in _norm(route) for route in routes if _norm(route))


def _project_value(meta: dict[str,Any], *, required_unit: str="", parameter_code: str="") -> tuple[float | None,str,str]:
    """Return only a semantically compatible structured project value.

    Quantity fields are counts, not generic engineering values. They may be used
    only for quantity/count requirements expressed in pieces. Missing evidence
    units are never silently inherited from the requirement.
    """
    code=str(parameter_code or "").upper()
    if required_unit=="pcs" or code in {"QUANTITY","COUNT","EQUIPMENT_COUNT"}:
        value=_numeric(meta.get("project_quantity"))
        if value is not None:
            return value,"pcs","project_quantity"

    for key in ("project_value","observed_value","value"):
        value=_numeric(meta.get(key))
        if value is None:
            continue
        unit=_unit(
            meta.get("project_unit")
            or meta.get("observed_unit")
            or meta.get("unit")
        )
        if required_unit and not unit:
            continue
        if required_unit and unit!=required_unit:
            continue
        return value,unit,key
    return None,"",""


def reconstruct_requirement_proof(
    project: CanonicalProject,
    requirement: Requirement,
) -> dict[str,Any]:
    domain=_norm(requirement.domain)
    evidence=[
        project.evidence[eid]
        for eid in requirement.evidence_ids
        if eid in project.evidence
    ]
    trusted=[
        item for item in evidence
        if item.addressable and item.trusted
        and _section_matches(item.section or item.document_name or item.document_id, requirement.expected_evidence_route)
    ]
    base={
        "proof_source":"CANONICAL_REQUIREMENT_RECONSTRUCTION",
        "domain":requirement.domain,
        "trusted_evidence_count":len(trusted),
        "evidence_ids":[item.evidence_id for item in trusted],
    }

    if domain in {"normative","нтд"}:
        if not bool(requirement.metadata.get("verified_clause")):
            return {
                **base,
                "state":"LIMITATION",
                "reason_code":"NORMATIVE_CLAUSE_NOT_VERIFIED",
                "reason":"Пункт НТД не имеет канонически подтверждённого verified-clause; автоматический нормативный вывод запрещён.",
            }
        if not trusted:
            return {
                **base,
                "state":"LIMITATION",
                "reason_code":"NO_ADDRESSABLE_PROJECT_EVIDENCE",
                "reason":"Пункт НТД верифицирован, но в проекте нет адресного доказательства для проверки его выполнения.",
            }
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"NORMATIVE_SEMANTIC_ADJUDICATION_PENDING",
            "reason":"Есть verified-clause и адресное evidence проекта, но семантическая проверка выполнения пункта НТД ещё не реализована канонически.",
        }

    if domain not in {"assignment","задание на проектирование"}:
        if not trusted:
            return {
                **base,
                "state":"LIMITATION",
                "reason_code":"NO_ADDRESSABLE_PROJECT_EVIDENCE",
                "reason":"Нет адресного канонического evidence для независимой проверки требования.",
            }
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"DOMAIN_PROOF_NOT_IMPLEMENTED",
            "reason":"Evidence присутствует, но для этого домена ещё нет независимого канонического proof-маршрута.",
        }

    if not trusted:
        return {
            **base,
            "state":"LIMITATION",
            "reason_code":"NO_ADDRESSABLE_PROJECT_EVIDENCE",
            "reason":"По требованию Задания не найдено доверенное адресное evidence в ожидаемом разделе.",
        }

    requirement_type=str(requirement.metadata.get("requirement_type") or "").upper()
    required_value=_numeric(requirement.metadata.get("required_value"))
    required_unit=_unit(requirement.metadata.get("unit"))

    if required_value is not None:
        facts=[]
        for item in trusted:
            meta=item.metadata or {}
            value,unit,value_source=_project_value(
                meta,
                required_unit=required_unit,
                parameter_code=requirement.expected_parameter_code,
            )
            if value is None:
                continue
            facts.append({
                "evidence_id":item.evidence_id,
                "value":value,
                "unit":unit,
                "value_source":value_source,
                "address":item.address,
            })
        if facts:
            values=[float(x["value"]) for x in facts]
            anchor=values[0]
            if not all(isclose(v,anchor,rel_tol=1e-9,abs_tol=1e-6) for v in values[1:]):
                return {
                    **base,
                    "state":"REVIEW",
                    "reason_code":"PROJECT_EVIDENCE_VALUE_CONFLICT",
                    "reason":"Адресные источники проекта дают разные значения; сначала требуется разрешить внутренний конфликт ПД.",
                    "required_value":required_value,
                    "required_unit":required_unit,
                    "facts":facts,
                }
            matches=isclose(anchor,required_value,rel_tol=1e-9,abs_tol=1e-6)
            return {
                **base,
                "state":"COMPLIANT" if matches else "NONCOMPLIANT",
                "reason_code":"ASSIGNMENT_VALUE_MATCH" if matches else "ASSIGNMENT_VALUE_MISMATCH",
                "reason":(
                    "20.0 независимо сопоставил требуемое значение Задания со структурированным адресным значением проекта."
                    if matches else
                    "20.0 независимо подтвердил расхождение между требуемым значением Задания и структурированным значением проекта."
                ),
                "required_value":required_value,
                "project_value":anchor,
                "required_unit":required_unit,
                "facts":facts,
                "correct_value_verified":not matches,
            }

    if "PRESENCE" in requirement_type:
        req_stems=_stems(requirement.text)
        for item in trusted:
            fragment=item.fragment or ""
            low=_norm(fragment)
            if not any(marker in low for marker in DESIGN_MARKERS):
                continue
            shared=req_stems & _stems(fragment)
            concept=str((item.metadata or {}).get("concept") or "").upper()
            anchors=CONCEPT_ANCHORS.get(concept,())
            concept_match=bool(
                anchors
                and any(anchor in _norm(requirement.text) for anchor in anchors)
                and any(anchor in low for anchor in anchors)
            )
            if len(shared)>=2 or concept_match:
                return {
                    **base,
                    "state":"COMPLIANT",
                    "reason_code":"ASSIGNMENT_PRESENCE_CONFIRMED",
                    "reason":"20.0 независимо подтвердил наличие требуемого проектного решения по адресному фрагменту ПД.",
                    "evidence_id":item.evidence_id,
                    "shared_terms":sorted(shared),
                    "concept":concept,
                }
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"PRESENCE_EVIDENCE_NOT_STRONG_ENOUGH",
            "reason":"Адресное evidence найдено, но канонический движок не смог надёжно подтвердить само требуемое проектное решение.",
        }

    return {
        **base,
        "state":"REVIEW",
        "reason_code":"ASSIGNMENT_PROOF_ROUTE_PENDING",
        "reason":"По требованию Задания есть адресное evidence, но тип требования пока не имеет независимого канонического proof-маршрута.",
    }
