
from __future__ import annotations
from .normative_intelligence import NormativeIntelligence
from .expert_practice_intelligence import ExpertPracticeIntelligence
from .pp87_compliance import PP87Compliance
from .engineering_verification_v2 import EngineeringVerification2

class ReviewContextBuilder:
    def __init__(self, knowledge_root):
        self.norms=NormativeIntelligence(knowledge_root)
        self.practice=ExpertPracticeIntelligence(knowledge_root)
        self.pp87=PP87Compliance(knowledge_root)
        self.engineering=EngineeringVerification2(knowledge_root)
    def build(self, question, *, object_name="", parameter_codes=None, section="", project_context=None, evidence=None):
        cls=self.engineering.classify_object(object_name)
        norms=self.norms.search(question=question,parameter_codes=parameter_codes or [],section=section,
                                object_type=cls.get("object_type",""),project_type=(project_context or {}).get("project_type",""),limit=6)
        practice=self.practice.risk_from_evidence(question,section,norms)
        pp87=self.pp87.checklist_contract(project_context or {})
        confidence=self.engineering.evidence_confidence(evidence or [],False)
        return {"object_classification":cls,"normative_context":norms,"expert_practice":practice,
                "pp87_context":pp87,"evidence_quality":confidence,
                "ai_instruction":"Отвечать по-русски. Не придумывать НТД. Разделять факт, предварительный вывод и требование проверки специалистом."}
