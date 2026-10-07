from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .expert_history import ExpertHistoryCorpus20
from .normative_proof import resolved_proof_type


ACTIVE_STATUSES={"Действует","Действует с изменениями"}
VERIFIED_POLICIES={"VERIFIED_ONLY"}
HISTORY_POLICY="PRIORITIZATION_ONLY"


def _load_json(path:Path, default:Any)->Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _norm(value:Any)->str:
    return " ".join(str(value or "").replace("ё","е").casefold().replace("\xa0"," ").split())


def _section_key(value:Any)->str:
    text=_norm(value).replace(" ","")
    aliases={
        "раздел1":"пз","пояснительнаязаписка":"пз",
        "раздел2":"пзу","схемапланировочнойорганизацииземельногоучастка":"пзу",
        "раздел3":"ар","архитектурныерешения":"ар","объемно-планировочныеиархитектурныерешения":"ар",
        "раздел4":"кр","конструктивныерешения":"кр",
        "раздел6":"тх","технологическиерешения":"тх",
    }
    if text in aliases:
        return aliases[text]

    # Real project files usually arrive as names such as
    # "Раздел ПД №2_ПЗУ1.pdf", "Раздел ПД №3_АР.pdf" and
    # "Раздел ПД №5_подраздел ПД №1_ИОС1.1.pdf".  Routing must recognise the
    # section code inside the filename rather than treating the whole filename
    # as an unknown section.  Broad PP87 IОС clauses intentionally route to
    # any IОС subsection.
    filename_tokens=(
        ("пзу","пзу"),("иос","иос"),("спозу","пзу"),
        ("ар","ар"),("кр","кр"),("тх","тх"),("пб","пб"),
        ("оди","оди"),("пос","пос"),("пмоос","пмоос"),("ээ","ээ"),
        ("пз","пз"),
    )
    for token,key in filename_tokens:
        if re.search(rf"(?:^|[_.№-]){token}(?:\d+(?:\.\d+)*)?(?:$|[_.-])",text):
            return key

    for token,key in (
        ("пояснительн","пз"),("планировочн","пзу"),("архитектур","ар"),
        ("конструктив","кр"),("технологическ","тх"),("пожар","пб"),
        ("водоснабж","иос"),("водоотвед","иос"),("электроснабж","иос"),
    ):
        if token in text:
            return key
    return text


def _sections_from_documents(documents:list[dict[str,Any]]|None)->set[str]:
    out=set()
    for row in documents or []:
        if not isinstance(row,dict):
            continue
        for value in (
            row.get("Тип документа"),row.get("Файл"),
            row.get("document_type"),row.get("section"),row.get("Раздел"),
            row.get("document"),row.get("document_name"),row.get("filename"),
        ):
            key=_section_key(value)
            if key:
                out.add(key)
    return out


def _execution_diagnostic(contract:dict[str,Any])->dict[str,Any]:
    """Classify whether a verified normative contract can reach a product verdict.

    Executable means that the current runtime has a complete supported path from
    routed evidence to its proof engine. Hardened means the path additionally has
    a specialized/declarative proof contract rather than relying only on generic
    semantic judging.
    """
    proof_type=resolved_proof_type(contract)
    ec=dict(contract.get("evidence_contract") or {})
    automatic_ready=bool(contract.get("automatic_contract_ready"))

    def result(executable:bool,reason:str="",hardened:bool=False,tier:str="")->dict[str,Any]:
        return {
            "resolved_proof_type":proof_type,
            "executable_contract_ready":bool(executable),
            "executable_blocker_reason":str(reason or ""),
            "hardened_proof_ready":bool(hardened and executable),
            "execution_tier":tier or (
                "HARDENED" if hardened and executable else
                "GENERIC_SEMANTIC" if executable and proof_type=="SEMANTIC_REQUIREMENT" else
                "EXECUTABLE" if executable else
                "NOT_EXECUTABLE"
            ),
        }

    if not automatic_ready:
        return result(False,"CLAUSE_NOT_VERIFIED_OR_NOT_READY")

    if proof_type=="PRESENCE":
        if not bool(ec.get("requires_page_reference")):
            return result(False,"ADDRESSABLE_PRESENCE_NOT_CONFIGURED")
        return result(True,hardened=True,tier="HARDENED")

    if proof_type=="STRUCTURE":
        return result(True,hardened=True,tier="HARDENED")

    if proof_type=="SEMANTIC_REQUIREMENT":
        if str(ec.get("execution_mode") or "").upper()!="SEMANTIC_PROOF":
            return result(False,"SEMANTIC_EXECUTION_MODE_MISSING")
        semantic=dict(ec.get("semantic_proof_contract") or {})
        # Semantic Proof Gate 2.0 currently enforces required_groups/source_scope.
        # Other descriptive fields may improve prompts but are not counted as a
        # hardened machine-enforced gate until the runtime consumes them.
        hardened=bool(
            (isinstance(semantic.get("required_groups"),list) and semantic.get("required_groups"))
            or (isinstance(semantic.get("source_scope"),dict) and semantic.get("source_scope"))
        )
        return result(
            True,
            hardened=hardened,
            tier="HARDENED" if hardened else "GENERIC_SEMANTIC",
        )

    if proof_type=="SET_COMPLETENESS":
        set_contract=dict(ec.get("set_contract") or {})
        if not set_contract:
            return result(False,"SET_CONTRACT_MISSING")
        promotion=str(set_contract.get("promotion_policy") or "").upper()
        supported={
            "DETERMINISTIC_AFTER_COMPLETE",
            "DETERMINISTIC_WITH_SEMANTIC_FALLBACK",
            "SEMANTIC_AFTER_COMPLETE",
        }
        if promotion not in supported:
            return result(
                False,
                "SET_CONTRACT_HOLD_ONLY" if promotion=="HOLD" else "SET_CONTRACT_INCOMPLETE",
            )
        return result(True,hardened=True,tier="HARDENED")

    if proof_type=="GRAPHIC_CONTENT":
        visual=dict(ec.get("visual_contract") or {})
        if not str(visual.get("visual_kind") or "").strip() or not list(visual.get("elements") or []):
            return result(False,"VISUAL_CONTRACT_INCOMPLETE")
        return result(True,hardened=True,tier="HARDENED")

    if proof_type=="TYPED_VALUE":
        typed=dict(ec.get("typed_contract") or {})
        if not str(typed.get("kind") or "").strip() or not str(typed.get("promotion_policy") or "").strip():
            return result(False,"TYPED_CONTRACT_INCOMPLETE")
        return result(True,hardened=True,tier="HARDENED")

    if proof_type=="CROSS_DOCUMENT":
        cross=dict(ec.get("cross_document_contract") or {})
        if (
            not str(cross.get("kind") or "").strip()
            or not str(cross.get("promotion_policy") or "").strip()
            or len(list(cross.get("source_groups") or []))<2
        ):
            return result(False,"CROSS_DOCUMENT_CONTRACT_INCOMPLETE")
        return result(True,hardened=True,tier="HARDENED")

    return result(False,"UNSUPPORTED_OR_UNCONFIGURED_PROOF_ROUTE")


class NormativeKnowledgeFoundation20:
    """Curated normative catalogue + verified clauses + expert-history priority.

    The foundation intentionally separates three different assets:
    1) a document/status registry;
    2) atomic executable requirements;
    3) historical expert practice.

    Historical expert practice may raise routing priority, but never upgrades a
    clause to VERIFIED_ONLY and never creates an automatic project verdict.
    """

    def __init__(self, knowledge_root:str|Path):
        self.root=Path(knowledge_root)
        docs=_load_json(self.root/"normative_documents_registry.json",[])
        validity=_load_json(self.root/"normative_validity_registry.json",{})
        requirements=_load_json(self.root/"normative_requirements_v3.json",[])
        self.documents=[dict(x) for x in docs if isinstance(x,dict)] if isinstance(docs,list) else []
        self.validity=[dict(x) for x in (validity.get("records") or []) if isinstance(x,dict)] if isinstance(validity,dict) else []
        self.requirements=[dict(x) for x in requirements if isinstance(x,dict)] if isinstance(requirements,list) else []

        self.documents_by_id={
            str(row.get("document_id") or "").strip().upper():row
            for row in self.documents if str(row.get("document_id") or "").strip()
        }
        self.validity_by_id={
            str(row.get("canonical_id") or "").strip().upper():row
            for row in self.validity if str(row.get("canonical_id") or "").strip()
        }

    def _document_for_requirement(self,row:dict[str,Any])->dict[str,Any]:
        document_id=str(row.get("document_id") or "").strip().upper()
        if document_id and document_id in self.documents_by_id:
            return self.documents_by_id[document_id]
        source=_norm(row.get("source") or row.get("reference"))
        if not source:
            return {}
        best={}
        best_score=0
        for doc in self.documents:
            title=_norm(doc.get("title"))
            did=_norm(doc.get("document_id"))
            score=100 if did and did in source else 90 if source in title or title in source else 0
            if score>best_score:
                best,best_score=doc,score
        return best

    def _validity_for_document(self,document:dict[str,Any])->dict[str,Any]:
        canonical=str(document.get("validity_canonical_id") or "").strip().upper()
        return self.validity_by_id.get(canonical,{}) if canonical else {}

    @staticmethod
    def _source_verified(document:dict[str,Any],validity:dict[str,Any])->bool:
        status=str(validity.get("status") or document.get("status") or "").strip()
        verified_on=str(validity.get("verified_on") or document.get("verified_on") or "").strip()
        source_class=str(document.get("source_class") or "").casefold()
        return bool(status in ACTIVE_STATUSES and verified_on and source_class=="official")

    def requirement_contract(self,row:dict[str,Any])->dict[str,Any]:
        document=self._document_for_requirement(row)
        validity=self._validity_for_document(document)
        clause_verified=bool(row.get("clause_verified") or row.get("verified_clause"))
        source_verified=self._source_verified(document,validity)
        conclusion_policy=str(row.get("conclusion_policy") or "").upper()
        document_id=str(document.get("document_id") or row.get("document_id") or "")
        paragraph=str(row.get("paragraph") or row.get("clause") or "")
        if clause_verified and source_verified and paragraph:
            trust_state="VERIFIED_CLAUSE"
        elif source_verified:
            trust_state="VERIFIED_DOCUMENT_CLAUSE_PENDING"
        elif document:
            trust_state="CURATED_DOCUMENT_STATUS_PENDING"
        else:
            trust_state="SOURCE_NOT_CURATED"

        automatic_contract_ready=bool(
            trust_state=="VERIFIED_CLAUSE"
            and conclusion_policy in VERIFIED_POLICIES
        )
        expert_occurrences=int(validity.get("expert_occurrences") or 0)
        expert_projects=int(validity.get("expert_project_count") or 0)
        priority=str(validity.get("verification_priority") or "")
        sections=list(row.get("sections") or (row.get("evidence_contract") or {}).get("sections") or [])
        contract={
            "requirement_id":str(row.get("id") or row.get("requirement_id") or ""),
            "document_id":document_id,
            "document_title":str(document.get("title") or row.get("source") or ""),
            "source_status":str(validity.get("status") or document.get("status") or "Не верифицирован"),
            "source_verified":source_verified,
            "paragraph":paragraph,
            "topic":str(row.get("topic") or ""),
            "requirement":str(row.get("requirement") or ""),
            "sections":sections,
            "check_kind":str(row.get("check_kind") or ""),
            "automation":str(row.get("automation") or ""),
            "keywords":[str(x) for x in (row.get("keywords") or []) if str(x).strip()],
            "evidence_contract":dict(row.get("evidence_contract") or {}),
            "conclusion_policy":conclusion_policy,
            "clause_verified":clause_verified,
            "trust_state":trust_state,
            "automatic_contract_ready":automatic_contract_ready,
            "expert_occurrences":expert_occurrences,
            "expert_project_count":expert_projects,
            "verification_priority":priority,
            "history_policy":HISTORY_POLICY,
        }
        contract.update(_execution_diagnostic(contract))
        return contract

    def contracts(self)->list[dict[str,Any]]:
        return [self.requirement_contract(row) for row in self.requirements]

    def summary(self)->dict[str,Any]:
        contracts=self.contracts()
        projects=set()
        history_occurrences=0
        history_records=0
        for row in self.validity:
            count=int(row.get("expert_occurrences") or 0)
            if count:
                history_records+=1
                history_occurrences+=count
            projects.update(str(x) for x in (row.get("expert_projects") or []) if str(x).strip())
        verified_status=sum(1 for row in self.documents if self._source_verified(row,self._validity_for_document(row)))
        history=ExpertHistoryCorpus20(self.root).summary()
        ready=[x for x in contracts if x["automatic_contract_ready"]]
        triggered=sum(
            str((row.get("evidence_contract") or {}).get("activation") or "").upper()=="TRIGGERED_ONLY"
            for row in ready
        )
        verified=[x for x in contracts if x["trust_state"]=="VERIFIED_CLAUSE"]
        executable=[x for x in verified if x.get("executable_contract_ready")]
        hardened=[x for x in executable if x.get("hardened_proof_ready")]
        executable_by_type={}
        for row in executable:
            proof_type=str(row.get("resolved_proof_type") or "UNKNOWN")
            executable_by_type[proof_type]=executable_by_type.get(proof_type,0)+1
        blockers=[
            {
                "requirement_id":str(row.get("requirement_id") or ""),
                "proof_type":str(row.get("resolved_proof_type") or ""),
                "reason_code":str(row.get("executable_blocker_reason") or ""),
            }
            for row in verified
            if not row.get("executable_contract_ready")
        ]
        return {
            "document_catalog_total":len(self.documents),
            "verified_document_statuses":verified_status,
            "validity_registry_total":len(self.validity),
            "atomic_requirements_total":len(self.requirements),
            "verified_clauses":sum(1 for x in contracts if x["trust_state"]=="VERIFIED_CLAUSE"),
            "automatic_contract_ready":len(ready),
            "triggered_only_contracts":triggered,
            "default_active_contracts":len(ready)-triggered,
            "executable_contracts":len(executable),
            "executable_verified_coverage_pct":round(100.0*len(executable)/max(1,len(verified)),1),
            "executable_total_coverage_pct":round(100.0*len(executable)/max(1,len(contracts)),1),
            "hardened_executable_contracts":len(hardened),
            "hardened_verified_coverage_pct":round(100.0*len(hardened)/max(1,len(verified)),1),
            "hardened_total_coverage_pct":round(100.0*len(hardened)/max(1,len(contracts)),1),
            "generic_semantic_executable_contracts":sum(
                row.get("execution_tier")=="GENERIC_SEMANTIC" for row in executable
            ),
            "executable_triggered_only_contracts":sum(
                str((row.get("evidence_contract") or {}).get("activation") or "").upper()=="TRIGGERED_ONLY"
                for row in executable
            ),
            "executable_by_proof_type":executable_by_type,
            "executable_blockers":blockers,
            "clause_verification_backlog":sum(1 for x in contracts if x["trust_state"]!="VERIFIED_CLAUSE"),
            "history_linked_normative_records":history_records,
            "history_expert_occurrences":history_occurrences,
            "history_projects":len(projects),
            "history_evidence_projects":history.get("projects",0),
            "history_records":history.get("records",0),
            "history_records_with_response":history.get("records_with_response",0),
            "history_resolved_records":history.get("resolved_records",0),
            "history_repeat_records":history.get("repeat_records",0),
            "history_records_with_normative_basis":history.get("records_with_normative_basis",0),
            "history_policy":HISTORY_POLICY,
        }

    def project_routes(self,documents:list[dict[str,Any]]|None)->dict[str,Any]:
        project_sections=_sections_from_documents(documents)
        rows=[]
        for contract in self.contracts():
            expected={_section_key(x) for x in contract.get("sections") or [] if _section_key(x)}
            all_sections=not expected or "all" in expected
            matched=sorted(expected & project_sections)
            if all_sections:
                applicability_state="PROJECT_WIDE"
            elif matched:
                applicability_state="MATCHED_SECTION"
            else:
                applicability_state="NOT_ROUTED_BY_SECTION"

            relevant=applicability_state!="NOT_ROUTED_BY_SECTION"
            row={
                **contract,
                "project_applicability_state":applicability_state,
                "matched_sections":matched,
                "project_relevant":relevant,
                "priority_score":(
                    (1000 if contract.get("verification_priority")=="P1" else 500 if contract.get("verification_priority")=="P2" else 0)
                    + min(int(contract.get("expert_occurrences") or 0),999)
                    + (250 if contract.get("automatic_contract_ready") else 0)
                ),
            }
            rows.append(row)

        rows.sort(key=lambda x:(
            not bool(x.get("project_relevant")),
            -int(x.get("priority_score") or 0),
            str(x.get("requirement_id") or ""),
        ))
        relevant=[x for x in rows if x.get("project_relevant")]
        return {
            "project_sections":sorted(project_sections),
            "requirements_total":len(rows),
            "project_relevant":len(relevant),
            "verified_clause_routes":sum(1 for x in relevant if x.get("trust_state")=="VERIFIED_CLAUSE"),
            "automatic_contract_ready":sum(1 for x in relevant if x.get("automatic_contract_ready")),
            "history_prioritized":sum(1 for x in relevant if int(x.get("expert_occurrences") or 0)>0),
            "rows":rows,
        }


def default_foundation()->NormativeKnowledgeFoundation20:
    return NormativeKnowledgeFoundation20(Path(__file__).resolve().parents[1]/"knowledge")


def clause_registry_trust(metadata:dict[str,Any])->dict[str,Any]:
    """Return registry trust for a runtime normative requirement.

    Runtime rows may originate in the legacy audit, so the adapter can provide
    document_id while source_reference remains the human-readable citation.
    """
    foundation=default_foundation()
    pseudo={
        "id":metadata.get("normative_requirement_id") or metadata.get("canonical_id") or "",
        "document_id":metadata.get("document_id") or "",
        "source":metadata.get("source_reference") or "",
        "paragraph":metadata.get("paragraph") or "",
        "topic":metadata.get("topic") or "",
        "requirement":metadata.get("requirement") or "",
        "sections":metadata.get("expected_evidence_route") or [],
        "check_kind":metadata.get("check_kind") or "",
        "automation":"AUTO",
        "clause_verified":bool(metadata.get("verified_clause")),
        "conclusion_policy":"VERIFIED_ONLY" if metadata.get("categorical_conclusion_allowed") else "PRELIMINARY_ONLY",
    }
    return foundation.requirement_contract(pseudo)
