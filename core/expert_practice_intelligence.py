
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .normalization import normalize_text

class ExpertPracticeIntelligence:
    def __init__(self, knowledge_root):
        root=Path(knowledge_root)
        self.patterns=self._load(root/"expert_practice_patterns_v1.json")
        self.remarks=self._load(root/"expert_remarks_verified.json")
    @staticmethod
    def _load(path):
        try:
            x=json.loads(Path(path).read_text(encoding="utf-8"))
            return x if isinstance(x,list) else []
        except Exception:return []
    def classify(self,text:str):
        low=normalize_text(text)
        ranked=[]
        for p in self.patterns:
            hits=[s for s in p.get("signals",[]) if normalize_text(s) in low]
            if hits:
                ranked.append((len(hits)*float(p.get("risk_weight",.5)),p,hits))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return [{"pattern_id":p["pattern_id"],"category":p["category"],"check_strategy":p["check_strategy"],
                 "risk_weight":p["risk_weight"],"matched_signals":hits} for _,p,hits in ranked]
    def analogs(self,text:str,section:str="",limit:int=5):
        low=normalize_text(text); sec=normalize_text(section)
        scored=[]
        for r in self.remarks:
            score=0
            if sec and sec in normalize_text(r.get("section","")): score+=4
            for token in set(low.split()):
                if len(token)>5 and token in normalize_text(r.get("remark","")): score+=1
            if score: scored.append((score,r))
        scored.sort(key=lambda x:x[0],reverse=True)
        return [dict(x[1]) for x in scored[:limit]]
    def risk_from_evidence(self, current_issue:str, section:str="", normative_hits=None):
        patterns=self.classify(current_issue)
        analogs=self.analogs(current_issue,section)
        score=min(100, round(sum(p["risk_weight"]*20 for p in patterns)+len(analogs)*12+len(normative_hits or [])*4))
        return {"risk_score":score,"patterns":patterns,"remark_analogs":analogs,
                "status":"Высокий риск" if score>=70 else "Требует внимания" if score>=40 else "Низкая доказанность риска"}
