from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load(path:Path)->dict[str,Any]:
    try:
        obj=json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) else {}
    except Exception:
        return {}


class ExpertHistoryCorpus20:
    """Read-only corpus of real expert remark/response history.

    The corpus is evidence for recurrence and prioritisation only.  It is never
    a normative source and cannot by itself produce VERIFIED_OK or
    PROJECT_FINDING.
    """

    def __init__(self, knowledge_root:str|Path):
        self.root=Path(knowledge_root)
        self.project_dir=self.root/"evidence"/"projects"
        self.projects=[]
        self.records=[]
        if self.project_dir.exists():
            for path in sorted(self.project_dir.glob("*.json")):
                obj=_load(path)
                project_id=str(obj.get("project_id") or path.stem)
                records=[dict(x) for x in (obj.get("records") or []) if isinstance(x,dict)]
                self.projects.append({
                    "project_id":project_id,
                    "source_kind":str(obj.get("source_kind") or ""),
                    "records_count":len(records),
                    "file":path.name,
                })
                for row in records:
                    row["_project_id"]=project_id
                    self.records.append(row)

    @staticmethod
    def _has_text(value:Any)->bool:
        return bool(str(value or "").strip() and str(value or "").strip()!="-")

    def summary(self)->dict[str,Any]:
        with_response=sum(1 for r in self.records if self._has_text(r.get("response")))
        resolved=sum(1 for r in self.records if "устран" in str(r.get("status") or "").casefold())
        repeated=sum(1 for r in self.records if self._has_text(r.get("repeat_reason")))
        normative_basis=sum(1 for r in self.records if self._has_text(r.get("basis")))
        return {
            "projects":len(self.projects),
            "records":len(self.records),
            "records_with_response":with_response,
            "resolved_records":resolved,
            "repeat_records":repeated,
            "records_with_normative_basis":normative_basis,
            "usage_policy":"PRIORITIZATION_AND_ANALOGS_ONLY",
        }

    def top_patterns(self,limit:int=20)->list[dict[str,Any]]:
        counts=Counter()
        resolved=Counter()
        repeated=Counter()
        parameters=defaultdict(Counter)
        examples={}
        for row in self.records:
            section=str(row.get("section_code") or row.get("section_raw") or "Не определён")
            violation_rows=row.get("violation_types") or []
            if violation_rows:
                labels=[]
                for item in violation_rows:
                    if isinstance(item,dict):
                        labels.append(str(item.get("code") or item.get("name") or "UNKNOWN"))
                    else:
                        labels.append(str(item))
            else:
                labels=[str(row.get("remark_kind") or "OTHER")]
            for label in labels:
                key=(section,label)
                counts[key]+=1
                if "устран" in str(row.get("status") or "").casefold():
                    resolved[key]+=1
                if self._has_text(row.get("repeat_reason")):
                    repeated[key]+=1
                for code in row.get("parameter_codes") or []:
                    if str(code).strip():
                        parameters[key][str(code).strip()]+=1
                examples.setdefault(key,str(row.get("nonconformity") or "")[:300])

        out=[]
        for (section,label),count in counts.most_common(limit):
            key=(section,label)
            out.append({
                "section":section,
                "pattern":label,
                "occurrences":count,
                "resolved":resolved[key],
                "repeated":repeated[key],
                "parameter_codes":[x for x,_ in parameters[key].most_common(5)],
                "example":examples.get(key,""),
                "history_policy":"PRIORITIZATION_AND_ANALOGS_ONLY",
            })
        return out
