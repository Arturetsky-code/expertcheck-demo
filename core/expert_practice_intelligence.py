
from __future__ import annotations
import json, math, re, collections
from pathlib import Path
from typing import Any
from .normalization import normalize_text

_TOKEN_RE=re.compile(r"[а-яa-z0-9-]{4,}",re.I)
_STOP={"проектной","документации","раздел","представить","привести","необходимо","требования","сведения","проектируемого","объекта"}

def _tokens(text):
    return {x for x in _TOKEN_RE.findall(normalize_text(text)) if x not in _STOP}

class ExpertPracticeIntelligence:
    """Searches only real imported expert remarks and derived recurrence rules."""
    _CACHE = {}
    def __init__(self, knowledge_root):
        root=Path(knowledge_root).resolve()
        key=str(root)
        cached=self._CACHE.get(key)
        if cached is not None:
            self.patterns,self.remarks,self.rules,self.summary_data,self._tokens,self._idf,self._by_id,self._inverted=cached
            return
        self.patterns=self._load(root/"expert_practice_patterns_v1.json")
        self.remarks=self._load(root/"expert_remarks_verified.json")
        self.rules=self._load(root/"expert_practice_rules_v1.json")
        self.summary_data=self._load_obj(root/"expert_practice_summary.json")
        self._build_index()
        self._CACHE[key]=(self.patterns,self.remarks,self.rules,self.summary_data,self._tokens,self._idf,self._by_id,self._inverted)
    @staticmethod
    def _load(path):
        try:
            x=json.loads(Path(path).read_text(encoding="utf-8"))
            return x if isinstance(x,list) else []
        except Exception:return []
    @staticmethod
    def _load_obj(path):
        try:
            x=json.loads(Path(path).read_text(encoding="utf-8"))
            return x if isinstance(x,dict) else {}
        except Exception:return {}
    def _build_index(self):
        self._tokens=[]
        df=collections.Counter()
        for r in self.remarks:
            ts=_tokens(" ".join(str(r.get(k) or "") for k in ("remark","proposal","section","expert_direction","materials")))
            self._tokens.append(ts)
            df.update(ts)
        n=max(1,len(self.remarks))
        self._idf={t:math.log((n+1)/(c+1))+1 for t,c in df.items()}
        self._by_id={r.get("remark_id"):r for r in self.remarks}
        inv=collections.defaultdict(list)
        for i,ts in enumerate(self._tokens):
            for t in ts:
                inv[t].append(i)
        self._inverted=dict(inv)
    def classify(self,text:str):
        low=normalize_text(text)
        ranked=[]
        for p in self.patterns:
            hits=[s for s in p.get("signals",[]) if normalize_text(s) in low]
            if hits: ranked.append((len(hits)*float(p.get("risk_weight",.5)),p,hits))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return [{"pattern_id":p["pattern_id"],"category":p["category"],"check_strategy":p["check_strategy"],
                 "risk_weight":p["risk_weight"],"matched_signals":hits} for _,p,hits in ranked]
    def _similarity(self,q,doc):
        if not q or not doc:return 0.0
        inter=q&doc
        numerator=sum(self._idf.get(t,1) for t in inter)
        denominator=sum(self._idf.get(t,1) for t in q|doc)
        return numerator/denominator if denominator else 0.0
    def analogs(self,text:str,section:str="",target_code:str="",issue_families=None,limit:int=5):
        qt=_tokens(text); sec=normalize_text(section); fam=set(issue_families or [])
        scored=[]
        # Candidate generation via inverted token index avoids scanning the whole knowledge base
        # for every checklist item. Rare/high-IDF terms are the most informative.
        overlap=collections.Counter()
        for token in sorted(qt,key=lambda t:self._idf.get(t,1),reverse=True)[:18]:
            for i in self._inverted.get(token,()):
                overlap[i]+=1
        candidates=[i for i,_ in overlap.most_common(500)] if overlap else []
        for i in candidates:
            r=self.remarks[i]
            sim=self._similarity(qt,self._tokens[i])
            score=sim*70
            if sec and sec in normalize_text(r.get("section","")): score+=10
            if target_code and target_code==r.get("target_code"): score+=9
            rf=set(r.get("issue_families") or [])
            if fam and fam&rf: score+=8
            if r.get("is_repeat_iteration"): score+=3
            if score>=9:
                scored.append((score,r))
        scored.sort(key=lambda x:x[0],reverse=True)
        out=[]
        seen_groups=set()
        for score,r in scored:
            group=r.get("remark_group_id") or r.get("remark_id")
            if group in seen_groups: continue
            seen_groups.add(group)
            out.append({
              "remark_id":r.get("remark_id"),"project":r.get("project"),"source_type":r.get("source_type"),
              "section":r.get("section"),"remark":r.get("remark"),"basis":r.get("basis"),
              "proposal":r.get("proposal"),"answer":r.get("answer"),"issue_families":r.get("issue_families"),
              "target_code":r.get("target_code"),"check_strategy":r.get("check_strategy"),
              "is_repeat_iteration":r.get("is_repeat_iteration"),"iteration_count":r.get("iteration_count"),
              "similarity_score":round(score,1),"normative_refs":r.get("normative_refs") or []
            })
            if len(out)>=limit: break
        return out
    def recurrent_rules(self,text:str="",section_family:str="",target_code:str="",issue_family:str="",limit:int=6):
        low=normalize_text(text)
        ranked=[]
        for r in self.rules:
            score=0
            if section_family and r.get("section_family")==section_family: score+=6
            if target_code and r.get("target_code")==target_code: score+=7
            if issue_family and r.get("issue_family")==issue_family: score+=8
            examples=" ".join(r.get("example_texts") or [])
            score+=sum(1 for t in _tokens(low) if t in _tokens(examples))
            score+=min(5,int(r.get("project_count") or 0)/3)
            if score: ranked.append((score,r))
        ranked.sort(key=lambda x:x[0],reverse=True)
        return [dict(x[1],match_score=round(x[0],1)) for x in ranked[:limit]]
    def risk_from_evidence(self,current_issue:str,section:str="",target_code:str="",issue_families=None,normative_hits=None):
        patterns=self.classify(current_issue)
        analogs=self.analogs(current_issue,section,target_code,issue_families,limit=5)
        primary=(issue_families or [None])[0]
        rr=self.recurrent_rules(current_issue,target_code=target_code,issue_family=primary or "",limit=4)
        analog_strength=sum(max(0,a["similarity_score"]-10) for a in analogs[:3])/12
        recurrence=sum(min(12,(r.get("project_count") or 0)*1.5) for r in rr[:2])
        score=min(100,round(sum(p["risk_weight"]*16 for p in patterns)+analog_strength+recurrence+len(normative_hits or [])*2))
        return {"risk_score":score,"patterns":patterns,"remark_analogs":analogs,"recurrent_rules":rr,
                "status":"Высокий риск повторения замечания" if score>=70 else "Требует внимания" if score>=40 else "Недостаточно доказательств риска"}
    def enrich_comparisons(self,comparisons):
        changed=0
        for row in comparisons:
            text=" ".join(str(row.get(k) or "") for k in ("object","parameter","status","explanation","dependency_rationale"))
            status=normalize_text(row.get("status") or "")
            if not any(x in status for x in ("расхожд","конфликт","недостат","требует")):
                continue
            fam=["CROSS_SECTION_MISMATCH"] if any(x in status for x in ("расхожд","конфликт")) else ["MISSING_INFORMATION"]
            target=str(row.get("parameter_code") or "GENERAL")
            risk=self.risk_from_evidence(text,str(row.get("sections") or row.get("sources") or ""),target,fam,row.get("normative_requirements") or [])
            row["expert_practice_risk"]=risk
            row["expert_practice_analogs"]=risk["remark_analogs"]
            row["expert_practice_rules"]=risk["recurrent_rules"]
            changed+=1
        return changed
    def summary(self):
        return dict(self.summary_data or {},loaded_records=len(self.remarks),loaded_rules=len(self.rules))
