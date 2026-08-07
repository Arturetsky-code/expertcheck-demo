from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable
from .normalization import normalize_text

class NormativeKnowledgeLayer:
    """Local normative knowledge layer.

    Statuses are intentionally conservative. Unless a record has been explicitly
    curated, the application says 'Требует проверки актуальности' instead of
    claiming a legal document is current.
    """
    def __init__(self, knowledge_root: str | Path):
        self.path=Path(knowledge_root)/'normative_knowledge.json'
        try:
            self.records=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else []
        except Exception:
            self.records=[]

    def lookup(self, reference: str) -> dict[str, Any] | None:
        q=normalize_text(reference)
        if not q:return None
        best=None
        for rec in self.records:
            aliases=[rec.get('reference','')]+list(rec.get('aliases') or [])
            if any(normalize_text(a) in q or q in normalize_text(a) for a in aliases if a):
                best=rec;break
        return dict(best) if best else None

    def enrich(self, references: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        out=[]
        for row in references:
            item=dict(row); rec=self.lookup(str(row.get('reference') or ''))
            if rec:
                item['knowledge_status']=rec.get('status') or 'Требует проверки актуальности'
                item['official_title']=rec.get('title') or ''
                item['scope']=rec.get('scope') or ''
                item['sections']=rec.get('sections') or []
                item['object_types']=rec.get('object_types') or []
                item['knowledge_source']='curated'
            else:
                item['knowledge_status']='Требует проверки актуальности'
                item['knowledge_source']='not_curated'
            out.append(item)
        return out

    def summary(self) -> dict[str, Any]:
        return {'records':len(self.records),'curated_current':sum(1 for x in self.records if x.get('status')=='Действует (проверено)')}
