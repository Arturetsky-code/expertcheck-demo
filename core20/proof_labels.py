from __future__ import annotations

from typing import Any


PROOF_TYPE_LABELS={
    "PRESENCE":"Наличие сведений",
    "STRUCTURE":"Структура раздела",
    "SET_COMPLETENESS":"Полнота обязательного набора",
    "SEMANTIC_REQUIREMENT":"Смысловое выполнение требования",
    "GRAPHIC_CONTENT":"Содержание графической части",
    "TYPED_VALUE":"Структурированное значение",
    "CROSS_SECTION":"Межраздельная согласованность",
}
PROOF_STATE_LABELS={
    "RETAINED_FAIL_CLOSED":"Удержано исходное неопределённое состояние",
    "DETERMINISTIC_STRUCTURE_PROOF":"Структура подтверждена детерминированно",
    "ADDRESSABLE_PRESENCE_PROOF":"Наличие подтверждено адресным фрагментом",
    "PRESENCE_PROOF_NOT_ADDRESSABLE":"Адресное доказательство наличия не сформировано",
    "VISUAL_PROOF_REQUIRED":"Требуется визуальная проверка графической части",
    "SET_PROOF_CONTRACT_REQUIRED":"Требуется контракт полноты обязательного набора",
    "STRUCTURED_PROOF_REQUIRED":"Требуется структурированный доказательный контракт",
    "SEMANTIC_PROOF_REQUIRED":"Требуется независимая смысловая проверка",
    "SEMANTIC_CONSENSUS_PROOF":"Смысл подтверждён независимым консенсусом",
}
JUDGE_LABELS={
    "SUPPORTS":"Подтверждает",
    "CONTRADICTS":"Противоречит",
    "INSUFFICIENT":"Недостаточно доказательств",
    "OTHER_ENTITY":"Другой объект",
    "OTHER_METRIC":"Другой показатель",
}


def _label(value:Any,mapping:dict[str,str])->str:
    code=str(value or "").strip().upper()
    return mapping.get(code,code or "—")


def proof_type_label(value:Any)->str:
    return _label(value,PROOF_TYPE_LABELS)


def proof_state_label(value:Any)->str:
    return _label(value,PROOF_STATE_LABELS)


def judge_label(value:Any)->str:
    return _label(value,JUDGE_LABELS)
