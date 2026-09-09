from __future__ import annotations

from typing import Any, Iterable

from .model import CanonicalProject, Comparison, Evidence, Finding, ProjectObject, PropertyValue, Requirement, stable_id
from .requirement_router import route_typed_requirement_evidence


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value=row.get(key)
        if value not in (None, '', 'nan', 'None', '—'):
            return str(value).strip()
    return ''


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().casefold() not in {'', '0', 'false', 'нет', 'no', 'исключено'}


def _page(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _list(value: Any) -> list[str]:
    if value in (None, "", "—"):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).replace("|", ",").replace(";", ",").split(",") if part.strip()]


def _float_or_text(value: Any) -> float | str | None:
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _evidence_from_row(project: CanonicalProject, row: dict[str, Any], *, fallback_fragment: str = '') -> str | None:
    document=_text(row,'document','Файл','file','source_document')
    page=_page(row.get('page') if 'page' in row else row.get('Страница'))
    section=_text(row,'section','Раздел','document_type','Тип документа')
    fragment=_text(row,'fragment','text','context','snippet','evidence','Фрагмент') or fallback_fragment
    table_id=_text(row,'table_id','Таблица')
    row_id=_text(row,'row_id','table_row','row_index','Строка таблицы')
    if not any((document, page is not None, fragment, table_id, row_id)):
        return None
    evidence_id=_text(row,'evidence_id') or stable_id('EVD',document,page,section,table_id,row_id,fragment[:160])
    project.add_evidence(Evidence(
        evidence_id=evidence_id,
        document_id=_text(row,'document_id'),
        document_name=document,
        section=section,
        page=page,
        table_id=table_id,
        row_id=row_id,
        fragment=fragment,
        source_kind=_text(row,'source_kind','Тип источника'),
        addressable=bool(document and page is not None),
        trusted=(
            _bool(row.get('trusted_for_mismatch'), False)
            or _bool(row.get('trusted'), False)
            or _text(row,'evidence_state').casefold() in {'verified','verified_candidate','qualified'}
            or _text(row,'evidence_kind').upper().startswith(('VERIFIED_','QUALIFIED_'))
            or _text(row,'evidence_kind').upper() in {'EQUIPMENT_REGISTER_COMPARISON'}
        ),
        confidence=_float_or_text(row.get('confidence')) if isinstance(_float_or_text(row.get('confidence')), float) else None,
        confidence_kind=_text(row,'confidence_kind'),
        metadata={
            'migrated_from':'18.x',
            'observed_value':row.get('value'),
            'observed_value_text':_text(row,'value_text','value','Значение'),
            'observed_unit':_text(row,'unit','Единица измерения','Ед. изм.'),
            'observed_object_id':_text(row,'object_id'),
            'observed_parameter_code':_text(row,'parameter_code'),
            'evidence_kind':_text(row,'evidence_kind'),
            'evidence_state':_text(row,'evidence_state'),
            'concept':_text(row,'concept'),
            'project_value':row.get('project_value'),
            'project_quantity':row.get('project_quantity'),
            'task_quantity':row.get('task_quantity'),
            'project_unit':_text(row,'project_unit'),
            'project_parameter_code':_text(row,'project_parameter_code','typed_parameter_code'),
            'typed_parameter_code':_text(row,'typed_parameter_code'),
            'candidate_values':list(row.get('candidate_values') or []),
            'summary_hourly_values':list(row.get('summary_hourly_values') or []),
            'capacity_required_level':_text(row,'capacity_required_level'),
            'capacity_observed_level':_text(row,'capacity_observed_level'),
            'capacity_level_compatible':row.get('capacity_level_compatible'),
            'line_count':row.get('line_count'),
            'task_models':list(row.get('task_models') or []),
            'project_models':list(row.get('project_models') or []),
            'difference':_text(row,'difference'),
            'structured':bool(row.get('structured')),
            'part_role':_text(row,'part_role'),
            'clause_verified':_bool(row.get('clause_verified'),False),
            'set_complete':_bool(row.get('set_complete'),False),
            'completeness_verified':_bool(row.get('completeness_verified'),False),
            'semantic_gate_state':_text(row,'semantic_gate_state'),
            'contract_state':_text(row,'contract_state'),
            'semantic_verdict':_text(row,'semantic_verdict'),
        },
    ))
    return evidence_id


class Legacy18Adapter:
    """One-way adapter from accepted 18.x state into the 20.0 canonical model.

    The adapter does not alter legacy structures. It is deliberately permissive
    at ingestion and strict at CanonicalProject.validate(), allowing 20.0 to
    measure migration gaps explicitly instead of hiding them.
    """

    def build(
        self,
        *,
        project_name: str,
        documents: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        comparisons: list[dict[str, Any]],
        assembly_rows: list[dict[str, Any]] | None = None,
    ) -> CanonicalProject:
        first=documents[0] if documents else {}
        document_inventory=[]
        seen_documents=set()
        for doc in documents or []:
            if not isinstance(doc,dict):
                continue
            name=_text(doc,'document','Файл','file','name','filename')
            section=_text(doc,'document_type','Тип документа','section','Раздел')
            page_count=doc.get('page_count')
            key=(name.casefold(),section.casefold())
            if not name or key in seen_documents:
                continue
            seen_documents.add(key)
            document_inventory.append({
                'document':name,
                'section':section,
                'page_count':page_count,
            })
        project=CanonicalProject(
            project_id=_text(first,'project_id') or stable_id('PRJ',project_name),
            name=project_name,
            metadata={
                'migrated_from':'18.x',
                'snapshot_id':_text(first.get('analysis_snapshot') or {},'snapshot_id'),
                'legacy_version':_text(first,'version'),
                'document_inventory':document_inventory,
                'document_inventory_complete':bool(document_inventory),
            },
        )
        assembly_rows=list(assembly_rows or [])
        included_by_identity=self._included_map(assembly_rows)
        registry=list(first.get('consolidated_registry') or first.get('composition_baseline') or first.get('restored_trusted_registry') or [])
        object_by_name: dict[str,str]={}
        object_by_position: dict[str,str]={}
        for row in registry:
            name=_text(row,'Наименование объекта','name','object_name')
            position=_text(row,'Позиция по ГП','position','genplan_position')
            object_id=_text(row,'object_id') or stable_id('OBJ',position,name)
            identity=(position.casefold(),name.casefold())
            included=included_by_identity.get(identity, _bool(row.get('included'), True))
            evidence_ids=[]
            ev=_evidence_from_row(project,row,fallback_fragment=name)
            if ev:evidence_ids.append(ev)
            obj=ProjectObject(
                object_id=object_id,name=name or object_id,genplan_position=position,
                object_kind=_text(row,'Тип объекта','object_type','object_type_name'),
                lifecycle=_text(row,'Статус проектирования','lifecycle','object_lifecycle_status'),
                included=included,
                parent_object_id=_text(row,'parent_object_id') or None,
                evidence_ids=evidence_ids,
                metadata={'migrated_from':'18.x','source':'object_registry'},
            )
            project.add_object(obj)
            if name:object_by_name[name.casefold()]=object_id
            if position:object_by_position[position.casefold()]=object_id

        def resolve_object(row: dict[str, Any]) -> str | None:
            direct=_text(row,'object_id')
            if direct and direct in project.objects:return direct
            position=_text(row,'genplan_position','position','Позиция по ГП').casefold()
            if position and position in object_by_position:return object_by_position[position]
            name=_text(row,'object','object_name','object_hint','Наименование объекта','entity').casefold()
            return object_by_name.get(name)

        for row in findings:
            object_id=resolve_object(row)
            code=_text(row,'parameter_code')
            if not object_id or not code:
                continue
            evidence_ids=[]
            ev=_evidence_from_row(project,row,fallback_fragment=_text(row,'value_text','text'))
            if ev:evidence_ids.append(ev)
            property_id=_text(row,'property_id') or stable_id(
                'PROP',object_id,code,_text(row,'unit'),_text(row,'document','Файл'),row.get('page'),row.get('value'),_text(row,'value_text')
            )
            project.add_property(PropertyValue(
                property_id=property_id,object_id=object_id,parameter_code=code,
                parameter_name=_text(row,'parameter_name','parameter') or code,
                value=_float_or_text(row.get('value')),value_text=_text(row,'value_text'),unit=_text(row,'unit'),
                semantic_level=_text(row,'semantic_level','engineering_semantic_level'),
                binding_status=_text(row,'binding_status','project_understanding_binding','row_integrity_status'),
                physical_row_key=_text(row,'physical_row_key','row_key'),
                evidence_ids=evidence_ids,metadata={'migrated_from':'18.x','source':'finding'},
            ))

        for row in comparisons:
            object_id=resolve_object(row)
            code=_text(row,'parameter_code')
            if not object_id or not code:
                continue
            evidence_ids=[]
            for source in (row.get('verification_evidence') or []):
                if not isinstance(source,dict):continue
                ev=_evidence_from_row(project,source)
                if ev:
                    evidence=project.evidence[ev]
                    evidence.metadata.update({
                        'comparison_object_id':object_id,
                        'comparison_parameter_code':code,
                        'comparison_unit':_text(row,'unit'),
                    })
                    if ev not in evidence_ids:evidence_ids.append(ev)
            property_ids=[
                prop.property_id for prop in project.properties.values()
                if prop.object_id==object_id and prop.parameter_code==code
            ]
            comparison_id=_text(row,'comparison_id','check_id','check_code','id') or stable_id('CMP',object_id,code,_text(row,'unit'))
            project.add_comparison(Comparison(
                comparison_id=comparison_id,object_id=object_id,parameter_code=code,
                parameter_name=_text(row,'parameter_name','parameter') or code,unit=_text(row,'unit'),
                property_ids=property_ids,evidence_ids=evidence_ids,status=_text(row,'final_verification_state','verification_state','status'),
                proof_kind=_text(row,'proof_kind'),conflict_confirmed=_bool(row.get('conflict_confirmed'),False),
                correct_value_verified=_bool(row.get('correct_value_verified'),False),
                evidence_level=_text(row,'evidence_level') or 'L0',metadata={
                    'migrated_from':'18.x','source':'comparison',
                    'verification_kind':_text(row,'final_verification_kind','verification_kind','finding_type'),
                    'coverage_reason':_text(row,'coverage_reason','explanation'),
                },
            ))

        plan=dict(first.get('project_review_plan') or {})
        raw_assignment=list(first.get('assignment_compliance') or [])
        raw_normative=list(first.get('normative_compliance_audit') or [])
        page_corpus=list((first.get('analysis_snapshot') or {}).get('page_corpus') or [])
        normative_project_type=''
        for raw in raw_normative:
            if not isinstance(raw,dict):
                continue
            packet=raw.get('evidence_packet') or {}
            candidate=_text(packet,'project_type') if isinstance(packet,dict) else ''
            if candidate:
                normative_project_type=candidate
                break
        if normative_project_type:
            project.metadata['normative_project_type']=normative_project_type

        raw_requirement_by_id={}
        for raw in raw_assignment + raw_normative:
            if not isinstance(raw,dict):
                continue
            rid=_text(raw,'requirement_id','atom_id','plan_id','id','source_row')
            if rid:
                raw_requirement_by_id[rid]=raw
        for item in (plan.get('items') or []):
            if not isinstance(item,dict):continue
            requirement_id=_text(item,'requirement_id','atom_id','plan_id','id') or stable_id('REQ',_text(item,'domain'),_text(item,'title'))
            object_id=resolve_object(item)
            source_id=_text(item,'source_id','requirement_id','atom_id','plan_id','id')
            raw=raw_requirement_by_id.get(source_id) or raw_requirement_by_id.get(requirement_id) or {}
            requirement_evidence_ids=[]
            for source in list(raw.get('verification_evidence') or raw.get('evidence_candidates') or []):
                if not isinstance(source,dict):
                    continue
                ev=_evidence_from_row(project,source)
                if ev:
                    evidence=project.evidence[ev]
                    evidence.metadata.update({
                        'requirement_id':requirement_id,
                        'requirement_domain':_text(item,'domain_code','domain'),
                        'requirement_object_id':object_id or '',
                        'requirement_parameter_code':_text(item,'parameter_code','metric'),
                    })
                    if ev not in requirement_evidence_ids:
                        requirement_evidence_ids.append(ev)
            raw_contract=dict(raw.get('evidence_contract_v2') or raw.get('evidence_contract') or {})
            requirement_text=_text(raw,'requirement_text','requirement') or _text(item,'requirement_text','requirement','title','question')
            parameter_code=_text(raw,'parameter_code') or _text(item,'parameter_code','metric')
            expected_route=_list(
                raw.get('expected_evidence_route')
                or raw_contract.get('expected_sections')
                or raw_contract.get('sections')
                or raw.get('sections')
                or item.get('expected_evidence_route')
                or item.get('expected_sections')
            )
            if (
                _text(item,'domain_code','domain').casefold() in {'assignment','задание на проектирование'}
                and parameter_code
                and raw.get('required_value', item.get('required_value')) not in (None,'')
                and page_corpus
            ):
                routed=route_typed_requirement_evidence(
                    requirement_text=requirement_text,
                    parameter_code=parameter_code,
                    required_unit=_text(raw,'unit') or _text(item,'unit'),
                    expected_sections=expected_route,
                    page_corpus=page_corpus,
                )
                for source in routed:
                    ev=_evidence_from_row(project,source)
                    if not ev:
                        continue
                    evidence=project.evidence[ev]
                    evidence.metadata.update({
                        'requirement_id':requirement_id,
                        'requirement_domain':'assignment',
                        'requirement_object_id':object_id or '',
                        'requirement_parameter_code':parameter_code,
                        'canonical_routed':True,
                    })
                    if ev not in requirement_evidence_ids:
                        requirement_evidence_ids.append(ev)
            project.add_requirement(Requirement(
                requirement_id=requirement_id,domain=_text(item,'domain_code','domain') or 'UNKNOWN',
                text=requirement_text,
                applicable=item.get('applicable') if isinstance(item.get('applicable'),bool) else None,
                target_object_id=object_id,expected_parameter_code=parameter_code,
                expected_evidence_route=expected_route,
                required_slots=_list(item.get('required_slots') or item.get('missing_evidence_slots')),
                evidence_ids=requirement_evidence_ids,
                verification_kind=_text(item,'verification_kind'),evidence_level=_text(item,'evidence_level') or 'L0',
                metadata={
                    'migrated_from':'18.x','source':'review_plan',
                    'domain_code':_text(item,'domain_code'),
                    'requirement_type':_text(raw,'requirement_type','check_type') or _text(item,'check_type'),
                    'required_value':raw.get('required_value', item.get('required_value')),
                    'unit':_text(raw,'unit') or _text(item,'unit'),
                    'proof_kind':_text(raw,'proof_kind','evidence_quality_state') or _text(item,'proof_kind'),
                    'legacy_status':_text(raw,'status','result'),
                    'canonical_id':_text(raw,'canonical_id'),
                    'verified_clause':_bool(raw.get('verified_clause'),False),
                    'verified_clause_text':_text(raw,'verified_clause_text') or _text(raw.get('evidence_packet') or {},'normative_text'),
                    'source_reference':_text(raw,'source','reference'),
                    'document_id':_text(raw,'document_id'),
                    'paragraph':_text(raw,'paragraph','clause'),
                    'official_source':_text(raw,'official_source'),
                    'verification_status':_text(raw,'verification_status','status'),
                    'knowledge_kind':_text(raw,'knowledge_kind'),
                    'applicability':dict(raw.get('applicability') or {}),
                    'normative_requirement_id':_text(raw,'requirement_id','id'),
                    'topic':_text(raw,'topic'),
                    'check_kind':_text(raw,'check_kind','check_type'),
                    'coverage_state':_text(raw,'coverage_state'),
                    'expected_evidence_route':expected_route,
                    'project_type':_text(raw.get('evidence_packet') or {},'project_type') if isinstance(raw.get('evidence_packet'),dict) else '',
                    'categorical_conclusion_allowed':_bool(raw.get('categorical_conclusion_allowed'),False),
                    'evidence_contract':dict(raw.get('evidence_contract') or raw_contract),
                    'structural_check':dict(raw.get('structural_check') or {}),
                    'decision_basis':_text(raw,'decision_basis'),
                    'object_name':_text(raw,'object_name') or _text(item,'entity'),
                    'source_row_title':_text(raw,'source_row_title'),
                    'requirement_scope':_text(raw,'requirement_scope') or _text(item,'scope'),
                    'verification_kernel':_text(raw,'verification_kernel'),
                    'expected_evidence':_text(raw,'expected_evidence') or _text(item,'expected_evidence'),
                    'coverage_reason_code':_text(raw,'coverage_reason_code') or _text(item,'coverage_reason_code'),
                    'registry_enforcement_required':_text(item,'domain_code','domain').casefold() in {'normative','нтд'},
                },
            ))
            kind=_text(item,'verification_kind')
            if kind in {'PROJECT_FINDING','REVIEW_QUESTION','VERIFIED_OK','SYSTEM_LIMITATION'}:
                finding_id=_text(item,'finding_id','plan_id','id') or stable_id('FND',requirement_id,kind)
                project.add_finding(Finding(
                    finding_id=finding_id,kind=kind,title=_text(item,'title','requirement_text') or requirement_id,
                    object_id=object_id,parameter_code=_text(item,'parameter_code'),severity=_text(item,'priority','severity'),
                    state=_text(item,'verification_state'),evidence_level=_text(item,'evidence_level') or 'L0',
                    reason=_text(item,'coverage_reason','decision_basis','recommendation'),requirement_id=requirement_id,
                    metadata={'migrated_from':'18.x','source':'review_plan'},
                ))

        for cmp in project.comparisons.values():
            raw=cmp.metadata
            kind=_text(raw,'verification_kind')
            if kind not in {'PROJECT_FINDING','REVIEW_QUESTION','VERIFIED_OK','SYSTEM_LIMITATION'}:
                continue
            finding_id=stable_id('FND',cmp.comparison_id,kind)
            project.add_finding(Finding(
                finding_id=finding_id,kind=kind,title=f"{project.objects[cmp.object_id].name}: {cmp.parameter_name}",
                object_id=cmp.object_id,parameter_code=cmp.parameter_code,state=cmp.status,evidence_level=cmp.evidence_level,
                reason=_text(raw,'coverage_reason'),evidence_ids=list(cmp.evidence_ids),comparison_id=cmp.comparison_id,
                metadata={'migrated_from':'18.x','source':'comparison'},
            ))
        return project

    @staticmethod
    def _included_map(rows: Iterable[dict[str, Any]]) -> dict[tuple[str,str],bool]:
        result={}
        for row in rows or []:
            position=_text(row,'Позиция по ГП','position','genplan_position').casefold()
            name=_text(row,'Наименование объекта','Наименование','object','name').casefold()
            included=_bool(row.get('Включить',row.get('Включить в состав проекта',row.get('include',True))),True)
            result[(position,name)]=included
        return result
