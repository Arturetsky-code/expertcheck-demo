
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code

class EngineeringVerification2:
    def __init__(self, knowledge_root:str|Path):
        root=Path(knowledge_root)
        self.profiles=self._load(root/"object_type_profiles_v2.json")
        self.dependencies=self._load(root/"cross_section_dependency_rules.json")

    @staticmethod
    def _load(path):
        try:
            data=json.loads(Path(path).read_text(encoding="utf-8"))
            return data if isinstance(data,list) else []
        except Exception:return []

    def classify_object(self,name:str) -> dict[str,Any]:
        low=normalize_text(name)
        ranked=[]
        for p in self.profiles:
            score=sum(3 for a in p.get("aliases") or [] if normalize_text(a) in low)
            if score: ranked.append((score,p))
        if not ranked:
            return {"object_type":"GENERIC","confidence":0.25,"profile":None}
        ranked.sort(key=lambda x:x[0],reverse=True)
        return {"object_type":ranked[0][1]["object_type"],"confidence":min(.98,.55+.1*ranked[0][0]),"profile":ranked[0][1]}

    def validate_binding(self,object_name:str,parameter_code:str,section:str="") -> dict[str,Any]:
        cls=self.classify_object(object_name)
        code=canonical_parameter_code(parameter_code)
        profile=cls.get("profile") or {}
        expected=set(profile.get("expected_parameters") or [])
        owners=(profile.get("owner_sections") or {}).get(code,[])
        valid=not expected or code in expected
        owner_ok=not owners or any(normalize_text(x) in normalize_text(section) for x in owners)
        return {
            "object_type":cls["object_type"],"object_type_confidence":cls["confidence"],
            "parameter_code":code,"parameter_expected_for_object":valid,
            "profile_owner_sections":owners,"profile_owner_section_ok":owner_ok,
            "binding_status":"Подтверждена типологически" if valid else "Нетипичный показатель — требуется проверка",
        }

    def evidence_confidence(self,evidence:list[dict[str,Any]],owner_ok:bool=False) -> dict[str,Any]:
        strong=0
        independent=set()
        for e in evidence or []:
            if e.get("page") or e.get("page_number"): strong+=1
            sec=str(e.get("section") or e.get("document_type") or "")
            if sec: independent.add(sec)
            if e.get("structured") or e.get("value") is not None: strong+=1
        if owner_ok: strong+=2
        score=min(100,15*strong+15*min(3,len(independent)))
        if score>=80: status="Подтверждено автоматически"
        elif score>=60: status="Предварительно соответствует"
        elif score>=35: status="Недостаточно доказательств"
        else: status="Требуется инженер"
        return {"evidence_confidence":score,"verification_status":status,"independent_sources":len(independent)}
