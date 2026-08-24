from __future__ import annotations

from pathlib import Path
from typing import Any

from .normalization import normalize_text
from .page_evidence_store import canonical_section, is_assignment_source
from .normative_kb_v4 import NormativeKnowledgeBaseV4
from .normative_requirement_quality import requirement_quality


def _evidence_candidates(req:dict[str,Any], findings:list[dict[str,Any]], limit:int=8)->list[dict[str,Any]]:
    keywords=[normalize_text(x) for x in req.get('keywords') or [] if x]
    sections=[normalize_text(x) for x in req.get('sections') or [] if x and normalize_text(x)!='all']
    ranked=[]
    for f in findings or []:
        section=normalize_text(f.get('document_type') or f.get('section_family') or f.get('section') or '')
        if sections and section and not any(s in section or section in s for s in sections):
            continue
        blob=' '.join(str(f.get(k) or '') for k in ('context','section_title','table_title','table_evidence','parameter_name','value_text','object_hint','semantic_anchor_name'))
        low=normalize_text(blob)
        hits=[kw for kw in keywords if kw and kw in low]
        if not hits: continue
        score=len(hits)*4
        if f.get('page') not in (None,''):score+=1
        if f.get('evidence_id') or f.get('source_fingerprint'):score+=2
        if str(f.get('fact_admission_decision') or '').upper()=='ADMIT':score+=3
        ranked.append((score,f,hits))
    ranked.sort(key=lambda x:x[0],reverse=True)
    out=[]
    for score,f,hits in ranked[:limit]:
        out.append({
            'score':score,'evidence_id':f.get('evidence_id'),'document':f.get('document'),'page':f.get('page'),
            'object':f.get('semantic_anchor_name') or f.get('object_hint') or '','parameter':f.get('parameter_name') or '',
            'parameter_code':f.get('parameter_code'),'value':f.get('value_text') or f.get('value'),
            'context':str(f.get('context') or f.get('table_evidence') or '')[:550],
            'matched_terms':hits,
        })
    return out


def _part_role(document:str, section:str)->str:
    name=normalize_text(document).replace(' ','')
    section=normalize_text(section).replace(' ','')
    if any(token in name for token in ('пзу2','ар2')):
        return 'GRAPHIC_PART'
    if any(token in name for token in ('пзу1','ар1')):
        return 'TEXT_PART'
    if section in {'пзу','ар'} and any(token in name for token in ('графическ','чертеж','чертёж')):
        return 'GRAPHIC_PART'
    if section in {'пзу','ар'}:
        return 'TEXT_PART'
    return ''


def _pp87_structural_evidence(req:dict[str,Any], page_corpus:list[dict[str,Any]])->dict[str,Any]|None:
    requirement_id=str(req.get('id') or '')
    target={'PP87-CLAUSE-12-PZU':'ПЗУ','PP87-CLAUSE-13-AR':'АР'}.get(requirement_id)
    if not target:
        return None
    parts:dict[str,dict[str,Any]]={}
    for page in page_corpus or []:
        if is_assignment_source(page):
            continue
        document=str(page.get('document') or '')
        section=canonical_section(page.get('document_type') or page.get('section') or document)
        if section != target:
            continue
        role=_part_role(document,section)
        if not role or role in parts:
            continue
        parts[role]={
          'kind':'STRUCTURED_COMPLETENESS','document':document,'page':page.get('page') or 1,
          'section':section,'part_role':role,'text':f'{target}: {"графическая" if role=="GRAPHIC_PART" else "текстовая"} часть комплекта',
          'clause_verified':True,'set_complete':False,'completeness_verified':False,
          'semantic_gate_state':'PASSED','contract_state':'SATISFIED','semantic_verdict':'SUPPORTS',
        }
    complete={'TEXT_PART','GRAPHIC_PART'} <= set(parts)
    evidence=list(parts.values())
    for row in evidence:
        row['set_complete']=complete
        row['completeness_verified']=complete
    return {'complete':complete,'evidence':evidence,'missing':sorted({'TEXT_PART','GRAPHIC_PART'}-set(parts))}


class NormativeComplianceEngine:
    """Evidence-driven normative compliance over Normative KB 4.0.

    LAW_REQUIREMENT, ENGINEERING_RULE and EXPERT_PRACTICE_RULE are kept separate.
    Only LAW_REQUIREMENT is eligible for normative compliance. A missing verified
    clause is KB coverage debt, never a project risk.
    """
    def __init__(self, knowledge_root:str|Path):
        self.kb=NormativeKnowledgeBaseV4(knowledge_root)
        self.requirements=self.kb.compliance_requirements()
        self.docs=self.kb.documents_by_id

    def review(self, findings:list[dict[str,Any]], *, project_type:str='', limit:int=500, page_corpus:list[dict[str,Any]]|None=None)->list[dict[str,Any]]:
        rows=[]
        for req in self.requirements[:limit]:
            doc=self.docs.get(str(req.get('document_id') or ''))
            quality=requirement_quality(req,doc)
            evidence=_evidence_candidates(req,findings,limit=8)
            check_kind=str(req.get('check_kind') or req.get('check_type') or 'SEMANTIC').upper()
            verified_clause=bool(quality.get('verified_clause'))
            categorical=quality.get('conclusion_mode')=='CATEGORICAL_ALLOWED'
            contract=dict(req.get('evidence_contract') or {})
            contract.update({
              'check_kind':check_kind,
              'negative_from_not_found_allowed':False,
              'requires_verified_clause':True,
              'minimum_sources':int(contract.get('minimum_sources') or 1),
            })
            structural=_pp87_structural_evidence(req,list(page_corpus or [])) if verified_clause else None
            if structural and structural.get('complete'):
                evidence=list(structural.get('evidence') or [])
                status='Проверено системой'
                basis='Адресно подтверждены текстовая и графическая части профильного раздела, требуемые верифицированным пунктом ПП РФ № 87.'
                coverage_state='VERIFIED_OK'
            elif not verified_clause:
                status='Не покрыто нормативной базой'
                basis='Конкретный пункт и его нормативный текст не верифицированы в KB ExpertCheck. Это пробел покрытия базы, а не недостаток проектной документации.'
                coverage_state='KB_GAP'
            elif not evidence:
                status='Не проверено системой'
                basis='Верифицированное требование доступно, но доказательство выполнения специализированным алгоритмом не получено. Отсутствие находки не является нарушением.'
                coverage_state='EVIDENCE_GAP'
            else:
                status='Готово к проверке по доказательствам'
                basis='Верифицированное требование и кандидаты проектных доказательств доступны. Требуется типизированная/AI-проверка evidence packet.'
                coverage_state='READY_FOR_REVIEW'
            packet={
              'knowledge_kind':'LAW_REQUIREMENT',
              'document_id':req.get('document_id'),'source':req.get('source'),'paragraph':req.get('paragraph') or '',
              'normative_text':req.get('requirement') or '',
              'verification_status':req.get('verification_status') or req.get('status') or '',
              'contract':contract,'project_type':project_type,'evidence':evidence,
              'guardrail':'AI не использует память о норме; анализируется только переданный верифицированный текст и evidence packet.',
            }
            rows.append({
                'requirement_id':req.get('id'),'knowledge_kind':'LAW_REQUIREMENT','source':req.get('source'),'paragraph':req.get('paragraph') or '',
                'topic':req.get('topic') or '','requirement':req.get('requirement') or '','check_kind':check_kind,
                'verification_status':req.get('verification_status') or req.get('status') or '',
                'verified_clause':verified_clause,'categorical_conclusion_allowed':categorical,
                'status':status,'coverage_state':coverage_state,'decision_basis':basis,'evidence':evidence,
                'verification_kind':'VERIFIED_OK' if coverage_state=='VERIFIED_OK' else ('REVIEW_QUESTION' if coverage_state=='READY_FOR_REVIEW' else 'SYSTEM_LIMITATION'),
                'verification_state':'Соответствует' if coverage_state=='VERIFIED_OK' else ('Требует проверки специалистом' if coverage_state=='READY_FOR_REVIEW' else 'Не проверено автоматически'),
                'final_verification_kind':'VERIFIED_OK' if coverage_state=='VERIFIED_OK' else '',
                'final_verification_state':'Соответствует' if coverage_state=='VERIFIED_OK' else '',
                'proof_kind':'STRUCTURED_COMPLETENESS' if coverage_state=='VERIFIED_OK' else 'CANDIDATE_EVIDENCE',
                'structural_check':structural or {},
                'evidence_count':len(evidence),'ai_review_ready':bool(verified_clause and evidence),
                'evidence_contract':contract,'evidence_packet':packet,
                'guardrail':'Непроверенная норма или ненайденное доказательство не формируют нормативный риск проекта.',
            })
        return rows

    def coverage(self)->dict[str,Any]:
        return self.kb.coverage()

    @staticmethod
    def summary(rows:list[dict[str,Any]])->dict[str,Any]:
        total=len(rows)
        verified=sum(1 for x in rows if x.get('verified_clause'))
        ready=sum(1 for x in rows if x.get('ai_review_ready'))
        return {
            'requirements':total,
            'verified_clause':verified,
            'ai_review_ready':ready,
            'requires_kb_verification':sum(1 for x in rows if x.get('coverage_state')=='KB_GAP'),
            'project_review':sum(1 for x in rows if x.get('coverage_state')=='READY_FOR_REVIEW'),
            'evidence_gap':sum(1 for x in rows if x.get('coverage_state')=='EVIDENCE_GAP'),
            'verified_ok':sum(1 for x in rows if x.get('coverage_state')=='VERIFIED_OK'),
            'verified_coverage_pct':round(100*verified/max(1,total),1),
            'review_ready_pct':round(100*ready/max(1,total),1),
        }
