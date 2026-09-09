from __future__ import annotations

from typing import Any

from .model import CanonicalProject, Requirement
from .parameter_contracts import numeric, structured_values, unit
from .normative_foundation import clause_registry_trust


def _norm(value: Any) -> str:
    return " ".join(str(value or "").replace("ё","е").casefold().replace("\xa0"," ").split())


def _section_matches(section: str, target: str) -> bool:
    left=_norm(section).replace(" ","")
    right=_norm(target).replace(" ","")
    if not left or not right:
        return False
    if left==right or left.startswith(right) or right.startswith(left):
        return True
    aliases={
        "пзу":("пзу","раздел2","схемапланировочнойорганизации"),
        "ар":("ар","раздел3","архитектур"),
        "иос":("иос","раздел5","инженер"),
    }
    tokens=aliases.get(right,(right,))
    return any(token in left for token in tokens)


def _inventory(project: CanonicalProject) -> list[dict[str,Any]]:
    rows=project.metadata.get("document_inventory") or []
    return [dict(row) for row in rows if isinstance(row,dict)]


def _applicability(project: CanonicalProject, requirement: Requirement) -> tuple[str,str]:
    if requirement.applicable is False:
        return "NOT_APPLICABLE","Применимость требования явно снята для данного проекта."
    if requirement.applicable is True:
        return "APPLICABLE","Применимость требования явно подтверждена."

    meta=requirement.metadata or {}
    contract=meta.get("applicability") or {}
    project_types={_norm(x) for x in (contract.get("project_types") or []) if _norm(x)}
    current_project_type=_norm(project.metadata.get("normative_project_type") or meta.get("project_type"))
    if project_types:
        if not current_project_type:
            return "UNKNOWN","Для требования задан тип проекта, но тип текущего проекта канонически не подтверждён."
        if current_project_type not in project_types:
            return "NOT_APPLICABLE","Тип текущего проекта не входит в область применимости требования."

    routes=list(requirement.expected_evidence_route or [])
    inventory=_inventory(project)
    for route in routes:
        if any(_section_matches(row.get("section") or row.get("document"),route) for row in inventory):
            return "APPLICABLE_BY_SECTION",f"Применимость подтверждена наличием профильного раздела {route}."
    if not routes and (not project_types or current_project_type in project_types):
        return "APPLICABLE_BY_CONTRACT","Область применимости подтверждена контрактом требования; обязательный профильный раздел не задан."
    return "UNKNOWN","Применимость требования не подтверждена каноническими данными проекта."


def _verified_clause(requirement: Requirement) -> tuple[bool,str,dict[str,Any]]:
    meta=requirement.metadata or {}
    if not bool(meta.get("verified_clause")):
        return False,"Пункт НТД не имеет признака verified_clause.",{}
    source=str(meta.get("source_reference") or "").strip()
    paragraph=str(meta.get("paragraph") or "").strip()
    if not source or not paragraph:
        return False,"Для verified-clause отсутствует адрес нормы: документ и/или пункт.",{}
    knowledge=str(meta.get("knowledge_kind") or "").upper()
    if knowledge and knowledge!="LAW_REQUIREMENT":
        return False,"Источник не классифицирован как LAW_REQUIREMENT.",{}

    trust=clause_registry_trust(meta)
    if not trust.get("source_verified"):
        return False,"Источник НТД не имеет подтверждённого действующего статуса в кураторском реестре ExpertCheck.",trust
    if trust.get("trust_state")!="VERIFIED_CLAUSE":
        return False,"Документ верифицирован, но атомарный пункт ещё не имеет полного verified-clause контракта.",trust
    return True,"Идентичность пункта НТД и доверие к источнику подтверждены кураторским реестром.",trust


def _part_role(document: str, section: str) -> str:
    name=_norm(document).replace(" ","")
    sec=_norm(section).replace(" ","")
    if sec and "пзу" in sec:
        if any(token in name for token in ("пзу2","пзу_2","графическ","чертеж","чертёж")):
            return "GRAPHIC_PART"
        if any(token in name for token in ("пзу1","пзу_1","текстов")):
            return "TEXT_PART"
    if sec and ("ар"==sec or sec.startswith("ар")):
        if any(token in name for token in ("ар2","ар_2","графическ","чертеж","чертёж")):
            return "GRAPHIC_PART"
        if any(token in name for token in ("ар1","ар_1","текстов")):
            return "TEXT_PART"
    return ""


STRUCTURAL_CONTRACTS={
    "PP87-CLAUSE-12-PZU":{
        "section":"ПЗУ",
        "required_roles":{"TEXT_PART","GRAPHIC_PART"},
        "label":"ПП РФ №87, п. 12 — состав ПЗУ",
    },
    "PP87-CLAUSE-13-AR":{
        "section":"АР",
        "required_roles":{"TEXT_PART","GRAPHIC_PART"},
        "label":"ПП РФ №87, п. 13 — состав АР",
    },
}


def _requirement_identity(requirement: Requirement) -> str:
    meta=requirement.metadata or {}
    return str(
        meta.get("normative_requirement_id")
        or meta.get("canonical_id")
        or requirement.requirement_id
        or ""
    ).strip().upper()


def _structural_proof(project: CanonicalProject, requirement: Requirement) -> dict[str,Any] | None:
    rid=_requirement_identity(requirement)
    contract=STRUCTURAL_CONTRACTS.get(rid)
    if not contract:
        return None

    inventory=_inventory(project)
    matched=[
        row for row in inventory
        if _section_matches(row.get("section") or row.get("document"),contract["section"])
    ]
    roles=set()
    documents=[]
    for row in matched:
        role=_part_role(str(row.get("document") or ""),str(row.get("section") or contract["section"]))
        if role:
            roles.add(role)
        documents.append(str(row.get("document") or ""))

    missing=sorted(contract["required_roles"]-roles)
    base={
        "normative_contract":"STRUCTURE",
        "normative_requirement_id":rid,
        "normative_label":contract["label"],
        "required_document_roles":sorted(contract["required_roles"]),
        "observed_document_roles":sorted(roles),
        "missing_document_roles":missing,
        "document_inventory_matches":documents,
        "evidence_level":"L4",
    }
    if not missing:
        return {
            **base,
            "state":"COMPLIANT",
            "reason_code":"NORMATIVE_STRUCTURE_VERIFIED",
            "reason":"20.0 независимо подтвердил требуемый состав профильного раздела по инвентарю загруженных документов.",
            "correct_value_verified":True,
        }

    # Missing files are not yet an automatic finding: naming/profile ambiguity
    # remains possible until the document inventory contract is fully canonical.
    return {
        **base,
        "state":"REVIEW",
        "reason_code":"NORMATIVE_STRUCTURE_PART_MISSING",
        "reason":"В каноническом инвентаре не подтверждён полный требуемый состав раздела; отсутствие пока не трактуется как нарушение автоматически.",
    }


def _numeric_normative_proof(
    requirement: Requirement,
    evidence_rows,
) -> dict[str,Any] | None:
    meta=requirement.metadata or {}
    required_value=numeric(meta.get("required_value"))
    parameter_code=str(requirement.expected_parameter_code or "").upper()
    required_unit=unit(meta.get("unit"))
    if required_value is None or not parameter_code:
        return None

    facts=[]
    for evidence in evidence_rows:
        for fact in structured_values(
            parameter_code=parameter_code,
            requirement_text=requirement.text,
            required_unit=required_unit,
            evidence_fragment=evidence.fragment or "",
            evidence_meta=evidence.metadata or {},
        ):
            facts.append({**fact,"evidence_id":evidence.evidence_id,"address":evidence.address})

    base={
        "normative_contract":"TYPED_VALUE",
        "parameter_code":parameter_code,
        "required_value":required_value,
        "required_unit":required_unit,
        "typed_fact_count":len(facts),
        "facts":facts,
    }
    if not facts:
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"NORMATIVE_PARAMETER_BINDING_NOT_PROVEN",
            "reason":"Пункт НТД верифицирован, но проектное evidence не доказало тот же параметр с совместимой единицей.",
        }

    values={round(float(f["value"]),9) for f in facts}
    if len(values)>1:
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"NORMATIVE_PROJECT_VALUE_CONFLICT",
            "reason":"Адресные источники проекта дают разные значения параметра, связанного с верифицированным пунктом НТД.",
        }

    project_value=float(facts[0]["value"])
    if not bool(meta.get("categorical_conclusion_allowed")):
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"NORMATIVE_CATEGORICAL_CONCLUSION_BLOCKED",
            "reason":"Параметр сопоставлен, но evidence-contract данного пункта НТД пока не разрешает категорический автоматический вывод.",
            "project_value":project_value,
        }

    if abs(project_value-required_value)<=1e-9:
        return {
            **base,
            "state":"COMPLIANT",
            "reason_code":"NORMATIVE_TYPED_VALUE_MATCH",
            "reason":"20.0 независимо подтвердил соответствие проектного значения верифицированному числовому требованию НТД.",
            "project_value":project_value,
            "correct_value_verified":True,
        }

    return {
        **base,
        "state":"NONCOMPLIANT",
        "reason_code":"NORMATIVE_TYPED_VALUE_MISMATCH",
        "reason":"20.0 независимо подтвердил расхождение проектного значения с верифицированным числовым требованием НТД.",
        "project_value":project_value,
        "correct_value_verified":True,
    }


def reconstruct_normative_proof(
    project: CanonicalProject,
    requirement: Requirement,
    *,
    addressable_evidence: list[Any],
    trusted_evidence: list[Any],
) -> dict[str,Any]:
    meta=requirement.metadata or {}
    base={
        "proof_source":"CANONICAL_NORMATIVE_RECONSTRUCTION",
        "domain":requirement.domain,
        "source_reference":str(meta.get("source_reference") or ""),
        "paragraph":str(meta.get("paragraph") or ""),
        "check_kind":str(meta.get("check_kind") or meta.get("requirement_type") or "").upper(),
        "verified_clause":bool(meta.get("verified_clause")),
        "trusted_evidence_count":len(trusted_evidence),
        "addressable_evidence_count":len(addressable_evidence),
        "evidence_ids":[row.evidence_id for row in addressable_evidence],
    }

    verified,verified_reason,registry_trust=_verified_clause(requirement)
    if registry_trust:
        base.update({
            "normative_registry_trust":registry_trust.get("trust_state") or "",
            "normative_source_status":registry_trust.get("source_status") or "",
            "normative_history_occurrences":registry_trust.get("expert_occurrences") or 0,
            "normative_history_projects":registry_trust.get("expert_project_count") or 0,
            "normative_history_policy":registry_trust.get("history_policy") or "",
        })
    if not verified:
        return {
            **base,
            "state":"LIMITATION",
            "reason_code":"NORMATIVE_CLAUSE_NOT_VERIFIED",
            "reason":verified_reason+" Автоматический нормативный вывод запрещён.",
        }

    applicability_state,applicability_reason=_applicability(project,requirement)
    base.update({
        "applicability_state":applicability_state,
        "applicability_reason":applicability_reason,
    })
    if applicability_state=="NOT_APPLICABLE":
        return {
            **base,
            "state":"NOT_APPLICABLE",
            "reason_code":"NORMATIVE_NOT_APPLICABLE",
            "reason":"Применимость пункта НТД для данного проекта явно исключена.",
        }
    if applicability_state=="UNKNOWN":
        return {
            **base,
            "state":"REVIEW",
            "reason_code":"NORMATIVE_APPLICABILITY_NOT_PROVEN",
            "reason":"Пункт НТД верифицирован, но его применимость к данному проекту ещё не доказана канонически.",
        }

    structural=_structural_proof(project,requirement)
    if structural is not None:
        return {**base,**structural}

    numeric_proof=_numeric_normative_proof(requirement,addressable_evidence)
    if numeric_proof is not None:
        return {**base,**numeric_proof}

    if not addressable_evidence:
        return {
            **base,
            "state":"LIMITATION",
            "reason_code":"NORMATIVE_PROJECT_EVIDENCE_MISSING",
            "reason":"Пункт НТД и его применимость подтверждены, но отсутствует адресное проектное evidence для проверки выполнения.",
        }

    return {
        **base,
        "state":"REVIEW",
        "reason_code":"NORMATIVE_SEMANTIC_PROOF_PENDING",
        "reason":"Пункт НТД, применимость и адресное evidence доступны, но для данного типа нормы ещё нет независимого канонического semantic-proof маршрута.",
    }
