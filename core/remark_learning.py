from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable
from .normalization import normalize_text

class RemarkLearningEngine:
    """Case-based matcher over normalized GGE remark scenarios."""
    def __init__(self, knowledge_root: str | Path):
        p=Path(knowledge_root)/'gge_risk_scenarios.json'
        try:self.cases=json.loads(p.read_text(encoding='utf-8'))
        except Exception:self.cases=[]

    def _score(self, text: str, case: dict[str, Any], parameter_code: str='') -> int:
        low=normalize_text(text); score=0
        triggers=case.get('triggers') or {}
        kws=list(triggers.get('keywords') or [])
        statuses=list(triggers.get('statuses') or [])
        score += 8*sum(1 for k in kws if normalize_text(k) in low)
        score += 5*sum(1 for k in statuses if normalize_text(k) in low)
        pcs=set(case.get('parameter_codes') or [])
        if parameter_code and parameter_code in pcs: score += 35
        score += min(int(case.get('recurrence') or 0)*2,20)
        return score

    def match(self, *, text: str, parameter_code: str='', limit: int=3) -> list[dict[str, Any]]:
        ranked=[]
        for case in self.cases:
            score=self._score(text,case,parameter_code)
            if score<=0:continue
            ranked.append((score,case))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return [{**dict(case),'match_score':score} for score,case in ranked[:limit]]

    def enrich_comparisons(self, comparisons: Iterable[dict[str, Any]]) -> int:
        count=0
        for row in comparisons:
            text=' '.join(str(row.get(k) or '') for k in ('object','parameter_name','status','explanation','sources'))
            matches=self.match(text=text,parameter_code=str(row.get('parameter_code') or ''),limit=3)
            if matches:
                row['remark_analogs']=matches
                row['remark_best_scenario']=matches[0].get('scenario_id')
                row['remark_recurrence']=matches[0].get('recurrence')
                row['remark_recommendation']=matches[0].get('recommendation')
                count+=1
        return count
