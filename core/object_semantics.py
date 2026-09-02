from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from .normalization import normalize_text
from .knowledge_engine import default_knowledge_engine

# Единые коды Core для исторических обозначений legacy-анализатора.
PARAMETER_CODE_ALIASES: dict[str, str] = {
    "POWER_INST": "POWER_INSTALLED",
    "POWER_CALC": "POWER_CALCULATED",
    "STAFF": "PERSONNEL",
    "HEIGHT": "HEIGHT_BUILD",
    "FLOOR_COUNT": "FLOORS",
    "STOREYS": "FLOORS",
    "PRODUCTIVITY": "CAPACITY",
}

ENGINEERING_PARAMETERS = {
    "AREA_BUILD", "AREA_TOTAL", "VOLUME_BUILD", "HEIGHT_BUILD", "FLOORS",
    "CAPACITY", "RES_VOLUME", "POWER_KTP", "POWER_INSTALLED",
    "PRESSURE", "TEMPERATURE", "DIAMETER", "FLOW_RATE", "VOLTAGE", "DEPTH",
    "POWER_CALCULATED", "PERSONNEL", "LENGTH", "QUANTITY",
    "MOISTURE", "BULK_DENSITY",
    "PRESSURE", "VOLTAGE", "DIAMETER", "LINE_COUNT", "TEMPERATURE",
    "VOLUME", "DEPTH", "WIDTH", "AREA_ROOM", "AREA_ROOM_SUM",
    "SHIFT_DURATION", "DESIGN_CAPACITY", "STORAGE_CAPACITY", "STORAGE_MASS",
    "EQUIPMENT_COUNT", "PIPELINE_CAPACITY", "PUMP_HEAD",
}

FILE_EXTENSIONS = (".pdf", ".xml", ".sig", ".zip", ".rar", ".7z", ".dwg", ".dxf", ".docx", ".xlsx")
SERVICE_PATTERNS = (
    r"\bраздел\s+пд\b", r"\bподраздел\b", r"\bчасть\s*№?\s*\d+\b",
    r"\bтом\s*№?\s*\d+\b", r"\bлист\s*№?\s*\d+\b", r"\bимя файла\b",
    r"\bпроектная документация\b", r"\bрабочая документация\b",
    r"\bведомость документов\b", r"\bсодержание\b", r"\bоглавление\b",
)
PROJECT_CODE_RE = re.compile(r"\b(?:RAM|РД|ПД|СТРМ|[A-ZА-Я]{2,8})[-_.][A-ZА-Я0-9._-]{5,}\b", re.I)

DOCUMENT_CODE_PATTERN = re.compile(
    r"(?:^|[\s_\-])(?:ПЗ|ПЗУ\d*|АР\d*|КР\d*|ТХ\d*|ИОС\d*(?:\.\d+)?|ПОС|ПОД|ООС|ПБ|ОДИ|ЭЭ|СМ|ППО|ТКР|ИЛО)(?:$|[\s_\-.])",
    re.I,
)
DOCUMENT_LIST_ROW_RE = re.compile(
    r"^(?:\d+[.)]?\s+)?(?:раздел|подраздел|часть|том|книга|приложение|лист|документ|отчет|отчёт)\b",
    re.I,
)
DOCUMENT_FILE_RE = re.compile(r"[^\s]+\.(?:pdf|xml|sig|zip|docx?|xlsx?|dwg|dxf)$", re.I)
DOCUMENT_CONTEXT_TOKENS = (
    "состав проектной документации", "перечень проектной документации",
    "ведомость основного комплекта", "ведомость рабочих чертежей",
    "ведомость прилагаемых документов", "содержание тома", "оглавление",
    "перечень документов", "наименование документа", "обозначение документа",
    "номер тома", "шифр документа", "состав раздела", "состав тома",
)



_PARAMETER_ENTITY_PATTERNS = (
    r"^площадь\s+застройки\b", r"^общая\s+площадь\b", r"^полезная\s+площадь\b",
    r"^строительн(?:ый|ого)\s+об[ъь]?[её]м\b", r"^об[ъь]?[её]м\b", r"^вместимость\b",
    r"^высота\b", r"^высотность\b", r"^этажность\b", r"^количество\s+этаж",
    r"^мощность\b", r"^проектная\s+мощность\b", r"^установленная\s+мощность\b",
    r"^производительность\b", r"^пропускная\s+способность\b", r"^расход\b",
    r"^давление\b", r"^напор\b", r"^диаметр\b", r"^протяж[её]нность\b", r"^длина\b",
    r"^ширина\b", r"^глубина\b", r"^напряжение\b", r"^освещ[её]нность\b",
    r"^уровень\s+ответственности\b", r"^степень\s+огнестойкости\b",
    r"^влажность\b", r"^насыпная\s+плотность\b", r"^об[ъь]?[её]мная\s+масса\b",
    r"^класс\s+функциональной\s+пожарной\s+опасности\b", r"^категория\s+над[её]жности\b",
    r"^отметка\b", r"^уклон\b", r"^количество\b", r"^число\b",
)

def is_parameter_entity_name(value: Any) -> bool:
    """A metric/property label can never be the canonical project-object name."""
    raw=re.sub(r"\s+"," ",str(value or "")).strip(" .;:-")
    if not raw:
        return False
    low=normalize_text(raw)
    if any(re.search(p,low,re.I) for p in _PARAMETER_ENTITY_PATTERNS):
        return True
    # Very common table labels with units/value appended.
    if re.match(r"^(?:площадь|мощность|производительность|объем|объём|высота|этажность|расход|давление|диаметр|протяженность|протяжённость)\b",low):
        return True
    return False


def canonical_parameter_code(value: Any) -> str:
    code = str(value or "").strip().upper()
    return PARAMETER_CODE_ALIASES.get(code, code)


def is_service_object_candidate(item: dict[str, Any]) -> tuple[bool, list[str]]:
    """Определяет, является ли объектная находка служебной строкой.

    Имена файлов, пути, шифры и заголовки документа не могут создавать объект,
    даже если legacy-парсер пометил их как OBJECT_CANDIDATE.
    """
    reasons: list[str] = []
    raw = str(item.get("value_text") or item.get("object_hint") or "").strip()
    if is_parameter_entity_name(raw):
        return True, ["наименование является инженерным показателем/ТЭП, а не объектом"]
    low = normalize_text(raw)
    document = str(item.get("document") or "").strip()
    method = normalize_text(item.get("match_method") or "")
    zone = normalize_text(item.get("structural_zone") or "")
    context = normalize_text(" ".join(str(item.get(k) or "") for k in (
        "context", "structural_zone", "table_type", "table_evidence",
        "match_method", "parameter_name", "extraction_profile",
    )))

    if not raw:
        return True, ["пустое наименование"]
    if any(low.endswith(ext) for ext in FILE_EXTENSIONS):
        reasons.append("наименование заканчивается расширением файла")
    if os.path.basename(document).lower() == raw.lower() or os.path.splitext(os.path.basename(document))[0].lower() == raw.lower():
        reasons.append("наименование совпадает с именем загруженного файла")
    if "/" in raw or "\\" in raw:
        reasons.append("обнаружен путь к файлу")
    if any(re.search(pattern, low, flags=re.I) for pattern in SERVICE_PATTERNS):
        reasons.append("служебный заголовок документа")
    if PROJECT_CODE_RE.search(raw) and len(re.findall(r"[а-я]{3,}", low)) < 2:
        reasons.append("строка похожа на шифр документа")
    if any(token in method for token in ("имя файла", "filename", "метаданные загруз", "путь zip")):
        reasons.append("источник находки — метаданные файла")
    if any(token in zone for token in ("титульный лист", "ведомость документов", "содержание")):
        reasons.append("находка расположена в служебной зоне")
    if DOCUMENT_FILE_RE.search(raw):
        reasons.append("строка является именем файла")
    if DOCUMENT_LIST_ROW_RE.search(low):
        reasons.append("строка похожа на позицию перечня документов")
    if any(title == low or (title in low and len(low) < len(title) + 25) for title in DOCUMENT_TITLES):
        reasons.append("наименование является названием раздела или документа")
    if any(token in context for token in DOCUMENT_CONTEXT_TOKENS):
        reasons.append("контекст относится к перечню документов")
    # Шифр + марка раздела без сильного объектного контекста — это документ, а не объект.
    if DOCUMENT_CODE_PATTERN.search(raw) and not str(item.get("genplan_position") or "").strip():
        engineering_context = any(token in context for token in (
            "состав сложного объекта", "экспликация зданий", "экспликация сооружений",
            "объектная строка тэп", "таблица тэп объекта", "позиция по генплану",
        ))
        if not engineering_context:
            reasons.append("обнаружена марка/шифр раздела проектной документации")
    # Наименования из document/source metadata не могут быть объектами.
    source_kind = normalize_text(item.get("source_kind") or item.get("record_kind") or "")
    if source_kind in {"document", "file", "metadata", "project_metadata"}:
        reasons.append("запись относится к документу или метаданным")

    # Очень длинные строки с типовыми реквизитами обычно являются названием проекта/титулом.
    if len(raw) > 220:
        reasons.append("чрезмерно длинная служебная строка")
    if any(token in low for token in ("главный инженер проекта", "генеральный проектировщик", "инн", "огрн", "снилс")):
        reasons.append("реквизиты или участники проекта")
    return bool(reasons), reasons



DOCUMENT_REGISTER_TOKENS = (
    "состав проектной документации", "перечень разделов проектной документации",
    "ведомость документов", "ведомость ссылочных и прилагаемых документов",
    "содержание тома", "содержание", "перечень файлов",
    "исходно разрешительная документация", "исходно-разрешительная документация",
    "инженерные изыскания", "проектная документация",
)

DOCUMENT_TITLES = (
    "пояснительная записка", "схема планировочной организации земельного участка",
    "архитектурные решения", "объемно планировочные и архитектурные решения",
    "объёмно планировочные и архитектурные решения", "конструктивные решения",
    "технологические решения", "проект организации строительства",
    "проект организации работ по сносу", "мероприятия по обеспечению пожарной безопасности",
    "мероприятия по охране окружающей среды", "система электроснабжения",
    "система водоснабжения", "система водоотведения", "отопление вентиляция и кондиционирование",
    "сети связи", "смета на строительство", "иная документация",
    "технический отчет по результатам инженерных изысканий",
)

def object_candidate_evidence(item: dict[str, Any]) -> tuple[int, list[str]]:
    """Возвращает силу положительных оснований включения кандидата в реестр.

    3 — официальный объектный источник; 2 — сильное инженерное подтверждение;
    1 — слабый текстовый кандидат; 0 — документ/служебная запись.
    """
    reasons: list[str] = []
    raw = str(item.get("value_text") or item.get("object_hint") or "").strip()
    if is_parameter_entity_name(raw):
        return True, ["наименование является инженерным показателем/ТЭП, а не объектом"]
    low = normalize_text(raw)
    context = normalize_text(" ".join(str(item.get(k) or "") for k in (
        "context", "structural_zone", "table_type", "table_evidence", "match_method", "parameter_name"
    )))
    code = str(item.get("parameter_code") or "")
    position = str(item.get("genplan_position") or "").strip()

    if any(token in context for token in DOCUMENT_REGISTER_TOKENS):
        return 0, ["строка находится в перечне/ведомости документов"]
    if any(title == low or (title in low and len(low) < len(title) + 25) for title in DOCUMENT_TITLES):
        return 0, ["наименование является названием раздела или документа"]
    if item.get("record_kind") == "document":
        return 0, ["запись классифицирована как документ"]

    if code == "OBJECT_ENTRY" and str(item.get("document_type") or "") == "ПЗ":
        # OBJECT_ENTRY от legacy-парсера считается официальным только в подтвержденной
        # объектной зоне. Это блокирует строки состава ПД, ошибочно размеченные как объекты.
        if any(token in context for token in (
            "состав сложного объекта", "перечень объектов", "объекты капитального строительства",
            "позиция по генплану", "реестр объектов пз", "таблица состава объекта",
        )):
            reasons.append("официальная строка состава объекта в ПЗ")
            return 3, reasons
        reasons.append("OBJECT_ENTRY вне подтвержденной объектной зоны")
        return 1, reasons
    if bool(item.get("general_plan_explication")):
        reasons.append("строка экспликации генерального плана")
        return 3, reasons
    if position and bool(item.get("general_plan_field")):
        reasons.append("позиция обнаружена на поле генерального плана")
        return 3, reasons
    if bool(item.get("general_plan_named_label")):
        reasons.append("инженерная выноска обнаружена на поле генерального плана")
        return 2, reasons
    if "xml object node" in context or (code == "OBJECT_ENTRY" and item.get("source_kind") == "xml"):
        reasons.append("структурированный объектный узел XML")
        return 3, reasons
    if position:
        reasons.append("присутствует корректная позиция по генплану")
        return 2, reasons
    if any(token in context for token in ("таблица тэп", "объектная строка тэп", "экспликация зданий", "состав сложного объекта")):
        reasons.append("объектная строка инженерной таблицы")
        return 2, reasons
    if code == "OBJECT_CANDIDATE":
        reasons.append("текстовый кандидат без сильного объектного основания")
        return 1, reasons
    return 0, ["положительное объектное основание отсутствует"]


@dataclass(frozen=True)
class ObjectTypeDecision:
    code: str
    name: str
    confidence: float
    reasons: tuple[str, ...]


_TYPE_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("PUMP_STATION", "Насосная станция", ("насосн", "пульпонасосн", "водоподъемн")),
    ("TRANSFORMER_STATION", "Трансформаторная подстанция", ("ктп", "трансформаторн", "подстанц")),
    ("DIESEL_POWER", "Дизельная электростанция", ("дэс", "дизельн электростанц", "дизель генератор")),
    ("RESERVOIR", "Резервуар или ёмкость", ("резервуар", "емкост", "ёмкост", "бак ", "силос")),
    ("PIPELINE", "Трубопровод", ("трубопровод", "водовод", "пульпопровод", "газопровод", "нефтепровод")),
    ("ROAD", "Автомобильная дорога", ("автомобильн дорог", "автодорог", "проезд", "подъездн дорог")),
    ("LINEAR_STRUCTURE", "Линейное сооружение", ("эстакад", "конвейер", "канал", "канава", "линия электропередач", "лэп")),
    ("TECHNOLOGICAL_COMPLEX", "Технологический комплекс", ("дробильн комплекс", "технологическ комплекс", "установк", "фабрик", "цех", "комплекс переработ")),
    ("BUILDING", "Здание", ("корпус", "здание", "общежит", "столов", "гостиниц", "кпп", "операторн", "котельн", "склад", "пункт обогрева")),
    ("PLATFORM", "Площадка", ("площадка", "карта кучного", "карта складирования")),
    ("HYDRAULIC_STRUCTURE", "Гидротехническое сооружение", ("дамб", "пруд", "хвостохранилищ", "водосброс", "гидроотвал")),
    ("STRUCTURE", "Сооружение", ("сооружен", "стена", "навес", "огражден", "мачт", "опора")),
)


def classify_object(name: Any) -> ObjectTypeDecision:
    # Основная классификация выполняется библиотекой Knowledge Engine.
    profile = default_knowledge_engine().classify(name)
    if profile.code != "GENERIC_OBJECT":
        return ObjectTypeDecision(
            profile.code, profile.name, profile.confidence,
            tuple(f"профиль Knowledge Engine: {alias}" for alias in profile.matched_aliases),
        )
    # Legacy-правила остаются резервным механизмом для обратной совместимости.
    low = normalize_text(name)
    for code, title, aliases in _TYPE_RULES:
        matches = [alias for alias in aliases if alias in low]
        if matches:
            confidence = min(0.92, 0.78 + 0.03 * len(matches))
            return ObjectTypeDecision(code, title, confidence, tuple(f"legacy-признак: {m}" for m in matches))
    return ObjectTypeDecision("GENERIC_OBJECT", "Инженерный объект", 0.35, ("тип не определён однозначно",))


# required — почти всегда ожидается; expected — обычно приводится; conditional — только при применимости.
_APPLICABILITY: dict[str, dict[str, str]] = {
    "BUILDING": {
        "AREA_BUILD": "expected", "AREA_TOTAL": "expected", "VOLUME_BUILD": "expected",
        "HEIGHT_BUILD": "expected", "FLOORS": "expected", "PERSONNEL": "conditional", "QUANTITY": "conditional",
    },
    "PUMP_STATION": {
        "CAPACITY": "required", "POWER_INSTALLED": "expected", "POWER_CALCULATED": "conditional",
        "AREA_BUILD": "expected", "AREA_TOTAL": "conditional", "VOLUME_BUILD": "conditional",
        "HEIGHT_BUILD": "conditional", "FLOORS": "conditional", "QUANTITY": "expected",
    },
    "TRANSFORMER_STATION": {
        "POWER_KTP": "required", "POWER_INSTALLED": "expected", "POWER_CALCULATED": "expected",
        "VOLTAGE": "expected", "AREA_BUILD": "conditional", "QUANTITY": "expected",
    },
    "DIESEL_POWER": {
        "POWER_INSTALLED": "required", "POWER_CALCULATED": "conditional", "AREA_BUILD": "conditional", "QUANTITY": "expected",
    },
    "RESERVOIR": {
        "RES_VOLUME": "required", "QUANTITY": "required", "HEIGHT_BUILD": "conditional", "DIAMETER": "conditional",
        "AREA_BUILD": "conditional", "VOLUME_BUILD": "conditional",
    },
    "TECHNOLOGICAL_COMPLEX": {
        "CAPACITY": "required", "POWER_INSTALLED": "expected", "POWER_CALCULATED": "conditional",
        "PERSONNEL": "expected", "QUANTITY": "conditional", "AREA_BUILD": "conditional",
        "MOISTURE": "expected", "BULK_DENSITY": "expected",
        "DESIGN_CAPACITY": "required", "SHIFT_DURATION": "expected",
        "EQUIPMENT_COUNT": "expected", "STORAGE_CAPACITY": "conditional",
        "STORAGE_MASS": "conditional", "PIPELINE_CAPACITY": "conditional",
        "PUMP_HEAD": "conditional",
    },
    "PIPELINE": {
        "LENGTH": "required", "DIAMETER": "expected", "PRESSURE": "expected", "CAPACITY": "conditional", "FLOW_RATE": "expected", "TEMPERATURE": "conditional", "LINE_COUNT": "conditional",
    },
    "COMPRESSOR_STATION": {"CAPACITY": "required", "POWER_INSTALLED": "required", "POWER_CALCULATED": "expected", "PRESSURE": "required", "FLOW_RATE": "expected", "TEMPERATURE": "conditional", "QUANTITY": "expected", "AREA_BUILD": "conditional", "HEIGHT_BUILD": "conditional"},
    "PROCESSING_PLANT": {"CAPACITY": "required", "POWER_INSTALLED": "expected", "PRESSURE": "expected", "FLOW_RATE": "expected", "TEMPERATURE": "expected", "RES_VOLUME": "conditional", "QUANTITY": "conditional", "AREA_BUILD": "conditional", "MOISTURE":"expected", "BULK_DENSITY":"expected"},
    "OIL_TREATMENT_UNIT": {"CAPACITY": "required", "POWER_INSTALLED": "expected", "PRESSURE": "expected", "FLOW_RATE": "expected", "TEMPERATURE": "expected", "RES_VOLUME": "conditional", "QUANTITY": "conditional", "AREA_BUILD": "conditional"},
    "WELL": {"DEPTH": "required", "CAPACITY": "expected", "PRESSURE": "expected", "DIAMETER": "conditional", "QUANTITY": "conditional"},
    "SEPARATOR": {"CAPACITY": "expected", "PRESSURE": "required", "TEMPERATURE": "expected", "RES_VOLUME": "conditional", "DIAMETER": "conditional", "HEIGHT_BUILD": "conditional", "QUANTITY": "expected"},
    "METERING_UNIT": {"CAPACITY": "expected", "FLOW_RATE": "required", "PRESSURE": "expected", "DIAMETER": "conditional", "QUANTITY": "conditional"},
    "FLARE_SYSTEM": {"CAPACITY": "expected", "PRESSURE": "conditional", "FLOW_RATE": "expected", "HEIGHT_BUILD": "required", "DIAMETER": "conditional", "QUANTITY": "conditional"},
    "ROAD": {"LENGTH": "required", "WIDTH": "expected", "QUANTITY": "conditional"},
    "LINEAR_STRUCTURE": {"LENGTH": "expected", "WIDTH": "conditional", "DIAMETER": "conditional", "FLOW_RATE": "conditional", "PRESSURE": "conditional", "CAPACITY": "conditional", "POWER_INSTALLED": "conditional", "QUANTITY": "conditional", "LINE_COUNT": "conditional"},
    "HYDRAULIC_STRUCTURE": {"HEIGHT_BUILD": "expected", "LENGTH": "expected", "WIDTH": "conditional", "CAPACITY": "conditional", "RES_VOLUME": "expected", "VOLUME": "conditional", "FLOW_RATE": "conditional", "QUANTITY": "conditional"},
    "PLATFORM": {"AREA_BUILD": "conditional", "CAPACITY": "conditional", "QUANTITY": "conditional"},
    "STRUCTURE": {"AREA_BUILD": "conditional", "VOLUME_BUILD": "conditional", "HEIGHT_BUILD": "conditional", "LENGTH": "conditional", "QUANTITY": "conditional"},
    "GENERIC_OBJECT": {code: "conditional" for code in ENGINEERING_PARAMETERS},
}


def parameter_applicability(object_type: str, parameter_code: Any) -> str:
    code = canonical_parameter_code(parameter_code)
    mapping = _APPLICABILITY.get(object_type, _APPLICABILITY["GENERIC_OBJECT"])
    return mapping.get(code, "not_applicable")


def expected_parameters(object_type: str, include_conditional: bool = False) -> list[str]:
    library_values = default_knowledge_engine().expected_properties(object_type)
    if library_values:
        return library_values
    mapping = _APPLICABILITY.get(object_type, _APPLICABILITY["GENERIC_OBJECT"])
    accepted = {"required", "expected", "conditional"} if include_conditional else {"required", "expected"}
    return [code for code, status in mapping.items() if status in accepted]


def enrich_findings_with_object_semantics(findings: list[dict[str, Any]]) -> None:
    for item in findings:
        item["parameter_code"] = canonical_parameter_code(item.get("parameter_code"))
        obj = str(item.get("semantic_anchor_name") or item.get("object_hint") or "").strip()
        if not obj or obj == "Не определён":
            continue
        decision = classify_object(obj)
        item["object_type_code"] = decision.code
        item["object_type_name"] = decision.name
        item["object_type_confidence"] = decision.confidence
        item["object_type_reasons"] = list(decision.reasons)
        if item.get("parameter_code") not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            item["parameter_applicability"] = parameter_applicability(decision.code, item.get("parameter_code"))
