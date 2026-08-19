
from __future__ import annotations
import hashlib
from typing import Any

def file_fingerprint(file:Any)->dict:
    data=file.getvalue() if hasattr(file,"getvalue") else bytes(getattr(file,"data",b"") or b"")
    return {
      "name":str(getattr(file,"name","")),
      "size":len(data),
      "sha256":hashlib.sha256(data).hexdigest(),
      "declared_document_type":str(getattr(file,"declared_document_type","") or ""),
    }

def diff_fingerprints(previous:list[dict]|None,current:list[dict])->dict:
    prev={x.get("name"):x for x in (previous or [])}
    cur={x.get("name"):x for x in current}
    added=[n for n in cur if n not in prev]
    removed=[n for n in prev if n not in cur]
    changed=[n for n in cur if n in prev and (cur[n].get("sha256")!=prev[n].get("sha256") or cur[n].get("declared_document_type")!=prev[n].get("declared_document_type"))]
    unchanged=[n for n in cur if n in prev and n not in changed]
    return {"added":added,"removed":removed,"changed":changed,"unchanged":unchanged}
