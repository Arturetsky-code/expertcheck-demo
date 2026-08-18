
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .normalization import normalize_text

class PP87Compliance:
    def __init__(self, knowledge_root):
        self.data=json.loads((Path(knowledge_root)/"pp87_project_profiles.json").read_text(encoding="utf-8"))
        self.profiles=self.data.get("profiles",[])
    def infer_profiles(self, project_context:dict[str,Any]):
        blob=normalize_text(" ".join(str(project_context.get(k,"")) for k in ("project_type","object_type","name","description")))
        scores=[]
        rules={
          "MINING_PRIMARY_PROCESSING":["добыч","переработ","горн","карьер","зиф","дск","кучн"],
          "RESERVOIR_HYDRAULIC":["водохранилищ","гидротехническ"],
          "ROAD":["автомобильн дорог","автодорог"],
          "LINEAR":["линейн","трубопровод","линия","дорог"],
        }
        for p in self.profiles:
            score=sum(1 for t in rules.get(p["project_type"],[]) if t in blob)
            if p["project_type"]=="CAPITAL_PRODUCTION_NONPRODUCTION": score=.25
            if score: scores.append((score,p))
        scores.sort(key=lambda x:x[0],reverse=True)
        return [dict(p,match_score=s) for s,p in scores]
    def checklist_contract(self, project_context):
        profiles=self.infer_profiles(project_context)
        return {
          "document":self.data["title"],"revision":self.data["revision"],
          "applicable_profiles":profiles,
          "decision":"Профиль ПП №87 должен быть подтвержден специалистом до категоричного вывода о комплектности.",
          "verification_status":"PRELIMINARY" if profiles else "SPECIALIST_REQUIRED"
        }
