from __future__ import annotations
from typing import Any

from .ru_labels import ru_label

PARAMETER_LABELS = {
    'AREA_BUILD': 'Площадь застройки',
    'AREA_TOTAL': 'Общая площадь',
    'VOLUME_BUILD': 'Строительный объём',
    'VOLUME': 'Объём',
    'RES_VOLUME': 'Объём/вместимость резервуара',
    'HEIGHT_BUILD': 'Высота',
    'FLOORS': 'Этажность',
    'CAPACITY': 'Производительность/пропускная способность',
    'POWER_KTP': 'Мощность КТП/трансформатора',
    'POWER_INSTALLED': 'Установленная мощность',
    'POWER_CALCULATED': 'Расчётная/максимальная мощность',
    'MOISTURE': 'Влажность материала',
    'BULK_DENSITY': 'Насыпная плотность',
    'FLOW_RATE': 'Расход',
    'PRESSURE': 'Давление',
    'DIAMETER': 'Диаметр',
    'LENGTH': 'Протяжённость',
    'WIDTH': 'Ширина',
    'DEPTH': 'Глубина',
    'VOLTAGE': 'Напряжение',
    'QUANTITY': 'Количество',
    'PERSONNEL': 'Численность персонала',
    'TEMPERATURE': 'Температура',
    'LINE_COUNT': 'Количество линий',
    'AREA_ROOM': 'Площадь помещения',
    'AREA_ROOM_SUM': 'Сумма площадей помещений по экспликации',
    'SHIFT_DURATION': 'Продолжительность смены',
    'BODY_VOLUME': 'Объём кузова',
    'BUCKET_VOLUME': 'Объём ковша',
}

STATUS_LABELS = {
    'CONFIRMED_ISSUE': 'Выявлено несоответствие',
    'REVIEW': 'Требует проверки',
    'INSUFFICIENT_DATA': 'Недостаточно данных',
    'UNVERIFIED_BY_SYSTEM': 'Не проверено системой',
    'OK': 'Проверено',
    'VERIFIED': 'Подтверждено',
    'SUPPORTED': 'Подтверждено частично',
    'HOLD': 'Требует проверки',
    'REJECT': 'Отклонено как недостоверное',
    'BLOCKED_SHIFTED_VALUE': 'Заблокировано: вероятное смещение значения',
    'MATCH': 'Совпадает',
    'MISMATCH': 'Расхождение',
    'POTENTIAL_MISMATCH': 'Потенциальное расхождение',
    'NOT_APPLICABLE': 'Не применимо',
    'ADMIT': 'Допущено в модель',
    'TRUSTED': 'Доверенный рецепт',
    'EXPERIMENTAL': 'Экспериментальный рецепт',
    'RETRIEVAL_ONLY': 'Только поиск кандидатов',
    'PASSED': 'Пройдено',
    'FAILED': 'Не пройдено',
    'BLOCKED': 'Заблокировано',
    'NOT_REQUIRED': 'Не требуется',
    'SATISFIED': 'Выполнен',
    'UNSATISFIED': 'Не выполнен',
    'VERIFIED_OK': 'Соответствует',
    'PROJECT_FINDING': 'Выявлено несоответствие',
    'REVIEW_QUESTION': 'Требует проверки специалистом',
    'SYSTEM_LIMITATION': 'Не проверено автоматически',
}

SCOPE_LABELS = {
    'default': 'Основной показатель',
    'total': 'Суммарное значение',
    'per_unit': 'На единицу',
    'room_area_sum': 'Сумма площадей помещений',
    'room_area': 'Площадь помещения',
    'room_schedule_sum': 'Сумма площадей помещений по экспликации',
    'building_total_area': 'Общая площадь здания',
    'site_area': 'Площадь территории/площадки',
    'building_footprint': 'Площадь застройки объекта',
    'fence_length': 'Протяжённость ограждения',
    'trestle_length': 'Протяжённость эстакады',
}


def parameter_label(value: Any) -> str:
    text = str(value or '').strip()
    return PARAMETER_LABELS.get(text.upper(), text or 'Показатель')


def status_label(value: Any) -> str:
    text = str(value or '').strip()
    return STATUS_LABELS.get(text.upper(), text or '—')


def scope_label(value: Any) -> str:
    text = str(value or '').strip()
    return SCOPE_LABELS.get(text, text or '—')


def localize_parameter_list(values: Any) -> list[str]:
    return [parameter_label(v) for v in (values or [])]

EVIDENCE_LABELS = {
    'VERIFIED_EVIDENCE':'Подтверждённое доказательство',
    'VERIFIED_SET_EVIDENCE':'Подтверждённое структурное доказательство',
    'CANDIDATE_EVIDENCE':'Кандидат в доказательства',
    'NO_EVIDENCE':'Доказательства не найдены',
    'TABLE_CELL_LOCKED':'Ячейка таблицы восстановлена',
    'GEOMETRIC_ROW':'Строка восстановлена по геометрии',
    'TEXT_FALLBACK':'Резервное текстовое извлечение',
    'PROJECT_FINDING':'Проблема проекта',
    'REVIEW_QUESTION':'Вопрос специалисту',
    'SYSTEM_LIMITATION':'Ограничение автоматической проверки',
    'PROJECT_STATUS':'Статус проекта',
    'REQUIREMENT_DIRECTED_TEXT':'Направленный поиск по требованию',
    'SEMANTIC_CONTRACT_MATCH':'Смысловое сопоставление с контрактом доказательства',
}

HEADER_LABELS = {
    'table_title':'Наименование таблицы','table_row':'Строка таблицы','explanation':'Пояснение',
    'reference':'Ссылка/обозначение','canonical_id':'Канонический ID','verified_on':'Дата верификации',
    'verified_revision':'Верифицированная редакция','replacement':'Заменяющий документ',
    'effective_until':'Действует до','official_source':'Официальный источник','official_source_kind':'Тип официального источника',
    'impact_risk':'Оценка влияния','cell_reconstruction':'Способ восстановления','evidence_quality_state':'Качество доказательства',
    'requirement_scope':'Область требования','requirement_type':'Тип требования','finding_type':'Тип результата',
    'promotion_method':'Способ подтверждения','semantic_evidence_score':'Смысловая достоверность',
}

def evidence_label(value: Any) -> str:
    text=str(value or '').strip()
    return EVIDENCE_LABELS.get(text.upper(), text or '—')

def header_label(value: Any) -> str:
    text=str(value or '').strip()
    return HEADER_LABELS.get(text, text)

def localize_service_value(value: Any) -> Any:
    if not isinstance(value,str): return value
    text=value.strip()
    localized=EVIDENCE_LABELS.get(text.upper(), STATUS_LABELS.get(text.upper(), SCOPE_LABELS.get(text,text)))
    return ru_label(localized)
