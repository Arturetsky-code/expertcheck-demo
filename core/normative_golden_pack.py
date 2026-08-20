from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def load_golden_pack(root: str|Path)->list[dict[str,Any]]:
    path=Path(root)/'normative_golden_pack_v1.json'
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data,list) else []
    except Exception:return []

def golden_pack_summary(root: str|Path)->dict[str,Any]:
    rows=load_golden_pack(root)
    return {
        'documents':len(rows),
        'official_sources_verified':sum(1 for x in rows if x.get('document_verification')=='VERIFIED_OFFICIAL_SOURCE'),
        'verified_clauses':sum(1 for x in rows if x.get('clause_verification')=='VERIFIED_CLAUSE'),
        'curation_required':sum(1 for x in rows if x.get('clause_verification')!='VERIFIED_CLAUSE'),
    }
