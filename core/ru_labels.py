from __future__ import annotations
from typing import Any

_LABELS = {
 'VERIFIED_EVIDENCE':'Подтверждённое доказательство','CANDIDATE_EVIDENCE':'Кандидат в доказательства','NO_EVIDENCE':'Доказательства не найдены',
 'PROJECT_GLOBAL':'Весь проект','SITE_SPECIFIC':'Площадка / земельный участок','OBJECT_SPECIFIC':'Конкретный объект','SYSTEM_SPECIFIC':'Инженерная система','EQUIPMENT_SPECIFIC':'Оборудование','DOCUMENT_SPECIFIC':'Документ / раздел','UNRESOLVED':'Область не определена',
 'VALUE_COMPARISON':'Сверка числового значения','SET_COMPARISON':'Сверка состава / перечня','CROSS_DOCUMENT_TRACE':'Прослеживаемость между документами','PRESENCE_REQUIREMENT':'Проверка наличия','NORMATIVE_COMPLIANCE':'Проверка требования НТД','CALCULATION_PRESENCE':'Проверка наличия расчёта','DRAWING_REQUIREMENT':'Проверка графического материала','PROHIBITION_OR_NOT_REQUIRED':'Проверка запрета / неприменимости','DESIGN_DETERMINED':'Определяется проектом','SEMANTIC_ENGINEERING':'Смысловая инженерная проверка',
 'TRACE_CHAIN':'Прослеживаемость цепочки источников','CALCULATION_PRESENCE':'Проверка наличия расчёта','DRAWING_EVIDENCE':'Доказательство на чертеже','NORMATIVE_LINK':'Связь с верифицированным требованием НТД','APPLICABILITY_REVIEW':'Проверка применимости','AI_EVIDENCE_REVIEW':'Смысловая проверка доказательств AI',
 'KB_GAP':'Не покрыто нормативной базой ExpertCheck','EVIDENCE_GAP':'Недостаточно проектных доказательств','READY_FOR_REVIEW':'Готово к проверке по доказательствам',
 'LAW_REQUIREMENT':'Нормативное требование','ENGINEERING_RULE':'Инженерное правило ExpertCheck','EXPERT_PRACTICE_RULE':'Правило из практики экспертизы',
 'CONFIRMED_ISSUE':'Подтверждённое несоответствие','REVIEW':'Требует проверки','INSUFFICIENT_DATA':'Недостаточно данных','UNVERIFIED_BY_SYSTEM':'Не проверено системой','OK':'Проверено',
 'ROW_LOCKED':'Привязано к строке','POSITION_LOCKED':'Привязано к позиции','HOLD':'Не допущено в модель','SUPPORTED':'Подтверждено','REJECT':'Отклонено',
 'CELL_TABLE':'Ячейка таблицы','TABLE_CELL':'Ячейка таблицы','GEOMETRIC_FALLBACK':'Геометрическое восстановление','TEXT_FALLBACK':'Текстовое восстановление',
}

def ru_label(value: Any) -> str:
    if value is None: return '—'
    raw=str(value).strip()
    if not raw: return '—'
    return _LABELS.get(raw, _LABELS.get(raw.upper(), raw))

def ru_join(values: Any, sep: str=', ') -> str:
    if isinstance(values,(list,tuple,set)):
        return sep.join(ru_label(x) for x in values)
    return ru_label(values)
