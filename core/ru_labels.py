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

 'TABLE_CELL_LOCKED':'Ячейка таблицы восстановлена и зафиксирована',
 'VERIFIED_SET_EVIDENCE':'Подтверждённое доказательство состава',
 'SYSTEM_LIMITATION':'Ограничение автоматической проверки','PROJECT_FINDING':'Проблема проекта','REVIEW_QUESTION':'Вопрос специалисту','INFORMATIONAL':'Информация','PROJECT_STATUS':'Статус проекта',
 'SEMANTIC_CONTRACT_MATCH':'Смысловое сопоставление с контрактом доказательства',
 'DIRECTED_VALUE':'Направленно найденное числовое доказательство','REQUIREMENT_DIRECTED_TEXT':'Направленный поиск по требованию',
 'building_footprint':'Площадь застройки здания','room_area':'Площадь помещения','room_schedule_sum':'Сумма площадей помещений по экспликации','site_area':'Площадь площадки','equipment_metric':'Показатель оборудования',
 'MINSTROY':'Минстрой России','VERIFIED_OFFICIAL_SOURCE':'Официальный источник подтверждён','SOURCE_CURATION_REQUIRED':'Требуется проверка официального источника','CURATION_REQUIRED':'Требуется кураторская проверка пункта','VERIFIED_CLAUSE':'Пункт верифицирован',
 'coverage_status':'Статус покрытия','project_risk_applicable':'Применимость риска к проекту','canonical_id':'Канонический идентификатор','official_source':'Официальный источник','official_source_kind':'Тип официального источника','verified_on':'Дата проверки','verified_revision':'Проверенная редакция','replacement':'Заменяющий документ','effective_until':'Действует до','impact_risk':'Влияние на проект','table_title':'Наименование таблицы','table_row':'Строка таблицы','explanation':'Пояснение','reference':'Нормативная ссылка',
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
