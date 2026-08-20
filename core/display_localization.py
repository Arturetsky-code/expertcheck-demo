from __future__ import annotations
from typing import Any

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
    'POWER_CALCULATED': 'Расчётная мощность',
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
