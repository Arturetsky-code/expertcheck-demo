from __future__ import annotations
import json
from typing import Any

from .normative_intelligence import NormativeIntelligence

SYSTEM_PROMPT = """Вы — модуль нормативной инженерной предпроверки ExpertCheck. Работайте ТОЛЬКО с переданным текстом нормы и доказательствами проекта. Не вспоминайте и не придумывайте нормы. Верните JSON: {\"applicable\":true|false,\"project_evidence_status\":\"confirmed|possible_gap|insufficient\",\"reason\":\"...\",\"evidence_ids\":[],\"confidence\":0.0}. Статус possible_gap допустим только если переданный текст нормы применим и проектные доказательства содержательно противоречат ему. Отсутствие найденного текста само по себе не является нарушением."""


def build_review_packet(req:dict[str,Any], context:dict[str,Any], evidence:list[dict[str,Any]]) -> dict[str,Any]:
    compact=[]
    for e in evidence[:12]:
        compact.append({
            "evidence_id":e.get("evidence_id"),"document":e.get("document"),"page":e.get("page"),
            "object":e.get("object_hint") or e.get("project_understanding_object_name"),
            "parameter":e.get("parameter_name"),"value":e.get("value_text") or e.get("value"),
            "context":str(e.get("context") or e.get("table_evidence") or "")[:500],
        })
    return {
        "normative_requirement":{
            "document_id":req.get("document_id"),"source":req.get("source"),"paragraph":req.get("paragraph"),
            "requirement":req.get("requirement"),"verification_status":req.get("verification_status"),
            "categorical_conclusion_allowed":req.get("categorical_conclusion_allowed",False),
        },
        "project_context":context,
        "project_evidence":compact,
    }


def ai_review_requirement(provider:Any, req:dict[str,Any], context:dict[str,Any], evidence:list[dict[str,Any]]) -> dict[str,Any]:
    """Optional semantic reviewer. It cannot upgrade an unverified clause to a violation."""
    if provider is None:
        return {"status":"AI_NOT_CONFIGURED","categorical":False}
    packet=build_review_packet(req,context,evidence)
    result=provider.generate(json.dumps(packet,ensure_ascii=False),system=SYSTEM_PROMPT)
    if not getattr(result,"ok",False):
        return {"status":"AI_ERROR","error":getattr(result,"error",""),"categorical":False}
    try:
        parsed=json.loads(str(result.text).strip().strip('`').replace('json\n','',1))
    except Exception:
        return {"status":"AI_INVALID_RESPONSE","raw":str(result.text)[:800],"categorical":False}
    categorical=bool(req.get("categorical_conclusion_allowed")) and parsed.get("project_evidence_status")=="possible_gap" and float(parsed.get("confidence") or 0)<1.01
    parsed["categorical"]=categorical
    parsed["policy"]="AI сопоставляет норму и проект, но не создаёт нормативное нарушение без верифицированного пункта."
    return parsed
