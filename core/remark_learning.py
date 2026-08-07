from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable
from .normalization import normalize_text

_STOPWORDS = {
    'проектной','документации','документация','представлены','представлено','представлена','требуется','необходимо',
    'сведения','раздел','часть','объект','объекта','объектов','соответствии','требования','пункт','федерального','закона',
    'российской','федерации','постановления','проектом','проектных','проектируемых','проектируемого','указаны','отсутствуют',
}
_TOKEN_RE = re.compile(r'[а-яёa-z0-9]{4,}', re.I)


def _tokens(text: str) -> set[str]:
    vals={normalize_text(x) for x in _TOKEN_RE.findall(str(text or ''))}
    return {x for x in vals if x and x not in _STOPWORDS and not x.isdigit()}


class RemarkLearningEngine:
    """Case-based matcher over normalized GGE remark scenarios and raw historical remarks.

    The curated scenarios are used for executable logic. The raw case library is
    an evidence-oriented analog search over previously received expert remarks.
    """
    def __init__(self, knowledge_root: str | Path):
        root=Path(knowledge_root)
        p=root/'gge_risk_scenarios.json'
        try:self.cases=json.loads(p.read_text(encoding='utf-8'))
        except Exception:self.cases=[]
        raw=root/'gge_remark_cases_v2.json'
        try:self.raw_cases=json.loads(raw.read_text(encoding='utf-8')) if raw.exists() else []
        except Exception:self.raw_cases=[]
        self._raw_tokens=[_tokens(x.get('remark','')) for x in self.raw_cases]

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

    def match_raw(self, *, text: str, section: str='', limit: int=5) -> list[dict[str,Any]]:
        query=_tokens(text)
        if not query:return []
        section_low=normalize_text(section)
        ranked=[]
        for idx,case in enumerate(self.raw_cases):
            toks=self._raw_tokens[idx]
            if not toks:continue
            common=len(query & toks)
            if common < 2:continue
            coverage=common/max(1,min(len(query),12))
            precision=common/max(1,min(len(toks),30))
            score=round((coverage*0.7+precision*0.3)*100,1)
            if section_low and any(section_low in normalize_text(x) or normalize_text(x) in section_low for x in case.get('sections') or [] if x):
                score += 12
            score += min(int(case.get('recurrence') or 0),10)
            if score >= 22:
                ranked.append((score,case))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return [{**dict(case),'similarity_score':round(score,1)} for score,case in ranked[:limit]]

    def enrich_comparisons(self, comparisons: Iterable[dict[str, Any]]) -> int:
        count=0
        for row in comparisons:
            text=' '.join(str(row.get(k) or '') for k in ('object','parameter_name','status','explanation','sources','document_values'))
            matches=self.match(text=text,parameter_code=str(row.get('parameter_code') or ''),limit=3)
            raw_matches=self.match_raw(text=text, section=str(row.get('section') or row.get('sections') or ''), limit=4)
            if matches:
                row['remark_analogs']=matches
                row['remark_best_scenario']=matches[0].get('scenario_id')
                row['remark_recurrence']=matches[0].get('recurrence')
                row['remark_recommendation']=matches[0].get('recommendation')
                count+=1
            if raw_matches:
                row['historical_remark_analogs']=raw_matches
                row['historical_remark_count']=len(raw_matches)
                row['historical_best_similarity']=raw_matches[0].get('similarity_score')
                count+=1
        return count
