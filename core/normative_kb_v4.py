from __future__ import annotations
from pathlib import Path
from typing import Any
import json
from .normalization import normalize_text
from .normative_requirement_quality import requirement_quality

KIND_LAW='LAW_REQUIREMENT'
KIND_ENGINEERING='ENGINEERING_RULE'
KIND_EXPERT='EXPERT_PRACTICE_RULE'

def classify_rule(row:dict[str,Any])->str:
    source=normalize_text(row.get('source') or '')
    status=normalize_text(row.get('verification_status') or row.get('status') or '')
    if 'expertcheck' in source or 'внутренн' in status or not str(row.get('document_id') or '').strip():
        return KIND_ENGINEERING
    if any(x in source for x in ('практик экспертиз','замечан экспертиз','ггэ')):
        return KIND_EXPERT
    return KIND_LAW

class NormativeKnowledgeBaseV4:
    def __init__(self, root:str|Path):
        root=Path(root)
        self.root=root
        self.documents=self._load(root/'normative_documents_registry.json')
        reqs=self._load(root/'normative_requirements_v3.json') or self._load(root/'normative_requirements_v2.json')
        self.documents_by_id={str(x.get('document_id') or ''):x for x in self.documents}
        self.all_rules=[]
        for raw in reqs:
            row=dict(raw); row['knowledge_kind']=classify_rule(row)
            doc=self.documents_by_id.get(str(row.get('document_id') or ''))
            q=requirement_quality(row,doc)
            row['verified_clause']=bool(q.get('verified_clause'))
            row['conclusion_mode']=q.get('conclusion_mode')
            self.all_rules.append(row)
        self.law_requirements=[x for x in self.all_rules if x['knowledge_kind']==KIND_LAW]
        self.engineering_rules=[x for x in self.all_rules if x['knowledge_kind']==KIND_ENGINEERING]
        self.expert_rules=[x for x in self.all_rules if x['knowledge_kind']==KIND_EXPERT]

    @staticmethod
    def _load(path:Path):
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            return data if isinstance(data,list) else []
        except Exception:return []

    def compliance_requirements(self)->list[dict[str,Any]]:
        # Only actual law/normative rules belong to normative compliance.
        return list(self.law_requirements)

    def coverage(self)->dict[str,Any]:
        law=self.law_requirements
        return {
          'law_requirements':len(law),
          'verified_clauses':sum(1 for x in law if x.get('verified_clause')),
          'engineering_rules':len(self.engineering_rules),
          'expert_practice_rules':len(self.expert_rules),
          'categorical_ready':sum(1 for x in law if x.get('conclusion_mode')=='CATEGORICAL_ALLOWED'),
          'coverage_pct':round(100*sum(1 for x in law if x.get('verified_clause'))/max(1,len(law)),1),
        }
