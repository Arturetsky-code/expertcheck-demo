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
    "POWER_CALCULATED", "PERSONNEL", "LENGTH", "QUANTITY",
    "PRESSURE", "VOLTAGE", "DIAMETER", "LINE_COUNT", "TEMPERATURE",
    "VOLUME", "DEPTH", "WIDTH",
}

FILE_EXTENSIONS = (".pdf", ".xml", ".sig", ".zip", ".rar", ".7z", ".dwg", ".dxf", ".docx", ".xlsx")
SERVICE_PATTERNS = (
    r"\bраздел\s+пд\b", r"\bподраздел\b", r"\bчасть\s*№?\s*\d+\b",
    r"\bтом\s*№?\s*\d+\b", r"\bлист\s*№?\s*\d+\b", r"\bимя файла\b",
    r"\bпроектная документация\b", r"\bрабочая документация\b",
    r"\bведомость документов\b", r"\bсодержание\b", r"\bоглавление\b",
)
PROJECT_CODE_RE = re.compile(r"\b(?:RAM|РД|ПД|СТРМ|[A-ZА-Я]{2,8})[-_.][A-ZА-Я0-9._-]{5,}\b", re.I)


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
    low = normalize_text(raw)
    document = str(item.get("document") or "").strip()
    method = normalize_text(item.get("match_method") or "")
    zone = normalize_text(item.get("structural_zone") or "")

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
        reasons.append("официальная строка состава объекта в ПЗ")
        return 3, reasons
    if bool(item.get("general_plan_explication")):
        reasons.append("строка экспликации генерального плана")
        return 3, reasons
    if position and bool(item.get("general_plan_field")):
        reasons.append("позиция обнаружена на поле генерального плана")
        return 3, reasons
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
    },
    "PIPELINE": {
        "LENGTH": "required", "DIAMETER": "expected", "PRESSURE": "expected", "CAPACITY": "conditional", "LINE_COUNT": "conditional",
    },
    "ROAD": {"LENGTH": "required", "QUANTITY": "conditional"},
    "LINEAR_STRUCTURE": {"LENGTH": "expected", "CAPACITY": "conditional", "POWER_INSTALLED": "conditional", "QUANTITY": "conditional"},
    "HYDRAULIC_STRUCTURE": {"HEIGHT_BUILD": "expected", "LENGTH": "expected", "CAPACITY": "conditional", "RES_VOLUME": "conditional"},
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
