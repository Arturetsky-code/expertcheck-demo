from __future__ import annotations

import re
from typing import Any

from .normalization import normalize_text

# Conservative rules: a candidate is an object only when its name has object semantics.
GENERIC_NON_OBJECTS = {
    'проектная документация','рабочая документация','пояснительная записка',
    'схема планировочной организации земельного участка','архитектурные решения',
    'конструктивные решения','технологические решения','система электроснабжения',
    'система водоснабжения','система водоотведения','отопление вентиляция и кондиционирование воздуха',
    'сети связи','проект организации строительства','мероприятия по охране окружающей среды',
    'мероприятия по обеспечению пожарной безопасности','содержание','оглавление',
    'состав проектной документации','ведомость документов','перечень документов',
    'основные технико экономические показатели','технико экономические показатели',
    'общие данные','условные обозначения','примечания','исходные данные',
}

GENERIC_FIELD_LABELS = {
    'наименование','наименование объекта','показатель','значение','единица измерения',
    'номер на плане','позиция по генплану','количество','площадь','площадь застройки',
    'общая площадь','строительный объем','строительный объём','высота','этажность',
    'мощность','производительность','протяженность','протяжённость','диаметр','давление',
}

OBJECT_NOUNS = (
    'здание','сооружение','площадка','корпус','станция','подстанция','насосная','компрессорная',
    'резервуар','емкость','ёмкость','склад','цех','комплекс','установка','узел','камера','колодец',
    'эстакада','галерея','конвейер','дорога','проезд','съезд','трубопровод','водовод','газопровод',
    'нефтепровод','канал','лоток','дамба','плотина','карьер','отвал','хвостохранилище','пруд',
    'очистные сооружения','линия','сеть','мачта','опора','кпп','ктп','дэс','абк','ремонтная',
    'котельная','венткамера','трансформатор','скважина','куст','факел','сепаратор','манифольд',
    'блок','модуль','пункт','пост','навес','укрытие','гараж','стоянка','ограждение','мост',
)

DOCUMENT_MARK_RE = re.compile(
    r'(?:^|[\s_\-])(?:ПЗ|ПЗУ\d*|АР\d*|КР\d*|ТХ\d*|ИОС\d*(?:\.\d+)?|ПОС|ПОД|ООС|ПБ|ОДИ|ЭЭ|СМ)(?:$|[\s_\-.])',
    re.I,
)
FILE_RE = re.compile(r'\.(?:pdf|xml|sig|zip|rar|7z|docx?|xlsx?|dwg|dxf)$', re.I)
CODE_RE = re.compile(r'\b(?:RAM|РД|ПД|[A-ZА-Я]{2,8})[-_.][A-ZА-Я0-9._-]{4,}\b', re.I)
ONLY_NUMERIC_RE = re.compile(r'^[\d\s.,:+\-/№()]+$')



def position_like_prefix(value: str) -> bool:
    return bool(re.match(r'^\s*\d+(?:\.\d+){0,3}\s*[-–—|]', str(value or '')))

def name_rejection_reasons(value: Any) -> list[str]:
    raw = str(value or '').strip()
    low = normalize_text(raw)
    reasons: list[str] = []
    if not low:
        return ['пустое наименование']
    if FILE_RE.search(raw) or '/' in raw or '\\' in raw:
        reasons.append('имя или путь файла')
    if low in GENERIC_NON_OBJECTS:
        reasons.append('название раздела или служебного блока')
    if low in GENERIC_FIELD_LABELS:
        reasons.append('заголовок поля или характеристика, а не объект')
    if ONLY_NUMERIC_RE.fullmatch(raw):
        reasons.append('числовая или координатная строка')
    if CODE_RE.search(raw) and len(re.findall(r'[а-яё]{3,}', raw.lower())) < 2:
        reasons.append('шифр документа')
    if DOCUMENT_MARK_RE.search(raw) and not any(noun in low for noun in OBJECT_NOUNS):
        reasons.append('марка раздела проектной документации')
    if len(low) > 220:
        reasons.append('слишком длинный текстовый фрагмент')
    if len(low.split()) > 22:
        reasons.append('абзац текста, а не наименование объекта')
    if low.startswith(('проверить ', 'предусмотреть ', 'выполнить ', 'обеспечить ', 'разработать ')):
        reasons.append('формулировка требования или действия')
    if re.match(r'^(?:раздел|подраздел|том|часть|книга|лист|таблица|рисунок|приложение|пункт)\b', low):
        if not any(noun in low for noun in OBJECT_NOUNS):
            reasons.append('служебный заголовок документа')
    if re.search(r'\b(?:гост|сп|снип|фз|постановлен|приказ|техническ(?:ий|ое) регламент)\b', low):
        if not any(noun in low for noun in OBJECT_NOUNS):
            reasons.append('нормативная ссылка, а не объект')
    if ':' in raw and len(low.split()) > 10 and not position_like_prefix(raw):
        reasons.append('описательная строка, а не наименование объекта')
    return list(dict.fromkeys(reasons))


def has_object_semantics(value: Any) -> bool:
    low = normalize_text(value)
    return bool(low and any(noun in low for noun in OBJECT_NOUNS))


def strong_object_name(value: Any, *, position: str = '', official: bool = False) -> tuple[bool, list[str]]:
    reasons = name_rejection_reasons(value)
    if reasons:
        return False, reasons
    if official and position:
        return True, []
    if has_object_semantics(value):
        return True, []
    return False, ['не обнаружены признаки самостоятельного инженерного объекта']
