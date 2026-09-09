from __future__ import annotations

from math import isclose
import re
from typing import Any

from .model import CanonicalProject, Requirement
from .parameter_contracts import (
    canonical_contract,
    compare_values,
    equipment_terms,
    norm,
    numeric,
    reserve_topology,
    structured_values,
    unit,
)


DESIGN_MARKERS = (
    "предусмотр", "проектом", "принят", "выполнен", "выполнена",
    "оборудуется", "ограждается", "устанавливается", "размещается",
    "осуществляется", "обеспечивается",
)

TOPOLOGY_EQUIPMENT_CLASSES = {
    "pump","fan","compressor","transformer","crusher","screen","conveyor",
    "loader","excavator","dump_truck",
}

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


def _stems(text: str) -> set[str]:
    words=re.findall(r"[a-zа-я0-9-]{5,}",norm(text))
    out=set()
    for word in words:
        if word in STOP_WORDS or word.isdigit():
            continue
        out.add(word[:max(5,min(8,len(word)))])
    return out


def _section_matches(section: str, routes: list[str]) -> bool:
    if not routes:
        return True
    low=norm(section)
    return any(norm(route) in low or low in norm(route) for route in routes if norm(route))


def _addressable_candidates(project: CanonicalProject, requirement: Requirement):
    rows=[]
    for eid in requirement.evidence_ids:
        item=project.evidence.get(eid)
        if not item or not item.addressable:
            continue
        if not _section_matches(item.section or item.document_name or item.document_id, requirement.expected_evidence_route):
            continue
        rows.append(item)
    return rows


def _trusted_candidates(project: CanonicalProject, requirement: Requirement):
    return [item for item in _addressable_candidates(project,requirement) if item.trusted]


def _numeric_assignment_proof(
    requirement: Requirement,
    evidence_rows,
) -> dict[str,Any] | None:
    required_value=numeric(requirement.metadata.get("required_value"))
    required_unit=unit(requirement.metadata.get("unit"))
    code=str(requirement.expected_parameter_code or "").upper()
    if required_value is None or not code:
        return None

    all_facts=[]
    evidence_without_binding=[]
    for item in evidence_rows:
        facts=structured_values(
            parameter_code=code,
            requirement_text=requirement.text,
            required_unit=required_unit,
            evidence_fragment=item.fragment or "",
            evidence_meta=item.metadata or {},
        )
        if not facts:
            evidence_without_binding.append(item.evidence_id)
            continue
        for fact in facts:
            all_facts.append({
                **fact,
                "evidence_id":item.evidence_id,
                "address":item.address,
            })

    base={
        "proof_source":"CANONICAL_REQUIREMENT_RECONSTRUCTION",
        "domain":requirement.domain,
        "parameter_code":code,
        "required_value":required_value,
        "required_unit":required_unit,
        "typed_fact_count":len(all_facts),
        "unbound_evidence_ids":evidence_without_binding,
    }
    if not all_facts:
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"PARAMETER_BINDING_NOT_PROVEN",
            "reason":"Адресные фрагменты найдены, но ни один не доказал тот же инженерный параметр с совместимой единицей.",
        }

    values=[float(f["value"]) for f in all_facts]
    state,anchor=compare_values(values,required_value)
    if state=="CONFLICT":
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"PROJECT_EVIDENCE_VALUE_CONFLICT",
            "reason":"Типизированные адресные источники проекта дают разные значения одного параметра; сначала требуется разрешить внутренний конфликт ПД.",
            "facts":all_facts,
        }

    if state=="MATCH":
        return {
            **base,
            "state":"COMPLIANT",
            "reason_code":"ASSIGNMENT_TYPED_VALUE_MATCH",
            "reason":"20.0 независимо сопоставил требуемое значение Задания с типизированным адресным значением того же параметра.",
            "project_value":anchor,
            "facts":all_facts,
        }

    return {
        **base,
        "state":"NONCOMPLIANT",
        "reason_code":"ASSIGNMENT_TYPED_VALUE_MISMATCH",
        "reason":"20.0 независимо подтвердил расхождение между требуемым значением Задания и типизированным адресным значением того же параметра.",
        "project_value":anchor,
        "facts":all_facts,
        "correct_value_verified":True,
    }


def _reserve_topology_proof(requirement: Requirement, evidence_rows) -> dict[str,Any] | None:
    low_req=norm(requirement.text)
    req_entities=equipment_terms(requirement.text) & TOPOLOGY_EQUIPMENT_CLASSES
    req=reserve_topology(requirement.text)

    # This checker is deliberately limited to physical equipment topology.
    # Lines/channels/networks/reservation of ASU or communications are not
    # "working + standby equipment" even if they contain those words.
    if not req_entities:
        return None
    if req is None:
        if not ("рабоч" in low_req and "резерв" in low_req):
            return None
        return {
            "proof_source":"CANONICAL_REQUIREMENT_RECONSTRUCTION",
            "domain":requirement.domain,
            "state":"REVIEW",
            "reason_code":"RESERVE_TOPOLOGY_REQUIREMENT_UNSTRUCTURED",
            "reason":"Требование относится к рабочему/резервному оборудованию, но количественная схема не структурирована однозначно.",
        }

    candidates=[]
    for item in evidence_rows:
        fragment=item.fragment or ""
        ev_entities=equipment_terms(fragment) & TOPOLOGY_EQUIPMENT_CLASSES
        if req_entities and not (req_entities & ev_entities):
            continue
        topology=reserve_topology(fragment)
        if topology is None:
            continue
        low=norm(fragment)
        strong=item.trusted or any(marker in low for marker in DESIGN_MARKERS)
        if not strong:
            continue
        candidates.append((item,topology))

    base={
        "proof_source":"CANONICAL_REQUIREMENT_RECONSTRUCTION",
        "domain":requirement.domain,
        "required_topology":{"working":req[0],"reserve":req[1]},
        "topology_entities":sorted(req_entities),
    }
    if not candidates:
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"RESERVE_TOPOLOGY_NOT_PROVEN",
            "reason":"Требование резервирования оборудования распознано, но в ПД не найдено адресное доказательство той же схемы рабочий/резервный.",
        }

    unique={top for _,top in candidates}
    if len(unique)>1:
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"RESERVE_TOPOLOGY_PROJECT_CONFLICT",
            "reason":"В ПД найдены противоречивые схемы рабочего и резервного оборудования одного типа.",
            "project_topologies":[{"working":x[0],"reserve":x[1]} for x in sorted(unique)],
        }

    actual=next(iter(unique))
    if actual==req:
        return {
            **base,
            "state":"COMPLIANT",
            "reason_code":"RESERVE_TOPOLOGY_MATCH",
            "reason":"20.0 подтвердил требуемую схему рабочего и резервного оборудования по адресному проектному доказательству.",
            "project_topology":{"working":actual[0],"reserve":actual[1]},
        }
    return {
        **base,
        "state":"NONCOMPLIANT",
        "reason_code":"RESERVE_TOPOLOGY_MISMATCH",
        "reason":"20.0 подтвердил, что схема рабочего и резервного оборудования в ПД отличается от Задания.",
        "project_topology":{"working":actual[0],"reserve":actual[1]},
        "correct_value_verified":True,
    }


def _presence_proof(requirement: Requirement, trusted_rows) -> dict[str,Any] | None:
    requirement_type=str(requirement.metadata.get("requirement_type") or "").upper()
    if "PRESENCE" not in requirement_type:
        return None
    req_stems=_stems(requirement.text)
    for item in trusted_rows:
        fragment=item.fragment or ""
        low=norm(fragment)
        if not any(marker in low for marker in DESIGN_MARKERS):
            continue
        shared=req_stems & _stems(fragment)
        concept=str((item.metadata or {}).get("concept") or "").upper()
        anchors=CONCEPT_ANCHORS.get(concept,())
        concept_match=bool(
            anchors
            and any(anchor in norm(requirement.text) for anchor in anchors)
            and any(anchor in low for anchor in anchors)
        )
        if len(shared)>=2 or concept_match:
            return {
                "proof_source":"CANONICAL_REQUIREMENT_RECONSTRUCTION",
                "domain":requirement.domain,
                "state":"COMPLIANT",
                "reason_code":"ASSIGNMENT_PRESENCE_CONFIRMED",
                "reason":"20.0 независимо подтвердил наличие требуемого проектного решения по адресному фрагменту ПД.",
                "evidence_id":item.evidence_id,
                "shared_terms":sorted(shared),
                "concept":concept,
            }
    return {
        "proof_source":"CANONICAL_REQUIREMENT_RECONSTRUCTION",
        "domain":requirement.domain,
        "state":"REVIEW",
        "reason_code":"PRESENCE_EVIDENCE_NOT_STRONG_ENOUGH",
        "reason":"Адресное evidence найдено, но канонический движок не смог надёжно подтвердить само требуемое проектное решение.",
    }


def reconstruct_requirement_proof(
    project: CanonicalProject,
    requirement: Requirement,
) -> dict[str,Any]:
    domain=norm(requirement.domain)
    addressable=_addressable_candidates(project,requirement)
    trusted=[item for item in addressable if item.trusted]
    base={
        "proof_source":"CANONICAL_REQUIREMENT_RECONSTRUCTION",
        "domain":requirement.domain,
        "trusted_evidence_count":len(trusted),
        "addressable_evidence_count":len(addressable),
        "evidence_ids":[item.evidence_id for item in addressable],
    }

    if domain in {"normative","нтд"}:
        if not bool(requirement.metadata.get("verified_clause")):
            return {
                **base,
                "state":"LIMITATION",
                "reason_code":"NORMATIVE_CLAUSE_NOT_VERIFIED",
                "reason":"Пункт НТД не имеет канонически подтверждённого verified-clause; автоматический нормативный вывод запрещён.",
            }
        if not addressable:
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
        if not addressable:
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

    if not addressable:
        return {
            **base,
            "state":"LIMITATION",
            "reason_code":"NO_ADDRESSABLE_PROJECT_EVIDENCE",
            "reason":"По требованию Задания не найдено адресное evidence в ожидаемом разделе.",
        }

    topology=_reserve_topology_proof(requirement,addressable)
    if topology is not None:
        return {**base,**topology}

    numeric_proof=_numeric_assignment_proof(requirement,addressable)
    if numeric_proof is not None:
        return {**base,**numeric_proof}

    presence=_presence_proof(requirement,trusted)
    if presence is not None:
        return {**base,**presence}

    return {
        **base,
        "state":"REVIEW",
        "reason_code":"ASSIGNMENT_PROOF_ROUTE_PENDING",
        "reason":"По требованию Задания есть адресное evidence, но тип требования пока не имеет независимого канонического proof-маршрута.",
    }
