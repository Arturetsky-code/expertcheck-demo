from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable
from .normalization import normalize_text


class NormativeKnowledgeLayer:
    """Local normative knowledge layer with curated status + historical expert index.

    A historical mention is not treated as proof that a document is currently
    valid. Only explicitly curated records may carry a verified status.
    """
    def __init__(self, knowledge_root: str | Path):
        root=Path(knowledge_root)
        self.path=root/'normative_knowledge.json'
        try:self.records=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else []
        except Exception:self.records=[]
        idx=root/'normative_reference_index.json'
        try:self.historical_index=json.loads(idx.read_text(encoding='utf-8')) if idx.exists() else []
        except Exception:self.historical_index=[]

    def lookup(self, reference: str) -> dict[str, Any] | None:
        q=normalize_text(reference)
        if not q:return None
        for rec in self.records:
            aliases=[rec.get('reference','')]+list(rec.get('aliases') or [])
            if any(normalize_text(a) in q or q in normalize_text(a) for a in aliases if a):
                return dict(rec)
        return None

    def historical_mentions(self, reference: str, limit: int=5) -> list[dict[str,Any]]:
        q=normalize_text(reference)
        if not q:return []
        ranked=[]
        for row in self.historical_index:
            ref=normalize_text(row.get('reference') or '')
            if not ref:continue
            if ref in q or q in ref:
                ranked.append(dict(row))
            else:
                qparts={x for x in q.split() if len(x)>3}
                rparts={x for x in ref.split() if len(x)>3}
                common=len(qparts & rparts)
                if common>=2:
                    item=dict(row); item['_score']=common
                    ranked.append(item)
        ranked.sort(key=lambda x:(int(x.get('_score') or 99),int(x.get('historical_mentions') or 0)),reverse=True)
        return ranked[:limit]

    def enrich(self, references: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        out=[]
        for row in references:
            item=dict(row); ref=str(row.get('reference') or '')
            rec=self.lookup(ref)
            historical=self.historical_mentions(ref,limit=3)
            if rec:
                item['knowledge_status']=rec.get('status') or 'Требует проверки актуальности'
                item['official_title']=rec.get('title') or ''
                item['scope']=rec.get('scope') or ''
                item['sections']=rec.get('sections') or []
                item['object_types']=rec.get('object_types') or []
                item['verified_on']=rec.get('verified_on') or ''
                item['verified_revision']=rec.get('verified_revision') or ''
                item['knowledge_source']='curated'
            else:
                item['knowledge_status']='Требует проверки актуальности'
                item['knowledge_source']='historical_only' if historical else 'not_curated'
            if historical:
                item['historical_expert_mentions']=max(int(x.get('historical_mentions') or 0) for x in historical)
                item['historical_reference_examples']=historical
            out.append(item)
        return out

    def summary(self) -> dict[str, Any]:
        return {
            'records':len(self.records),
            'curated_current':sum(1 for x in self.records if x.get('status')=='Действует (проверено)'),
            'historical_reference_index':len(self.historical_index),
        }
