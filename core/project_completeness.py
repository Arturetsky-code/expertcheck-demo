from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

from core.project_upload import document_family

PROFILE_CAPITAL = "Капитальный объект"
PROFILE_LINEAR = "Линейный объект"

STATUS_PRESENT = "Загружен"
STATUS_MISSING = "Не загружен"
STATUS_NOT_APPLICABLE = "Не применим"
STATUS_INCLUDED = "Включён в другой раздел"
STATUS_LATER = "Будет добавлен позднее"
STATUS_REVIEW = "Требует решения"

USER_DECISIONS = [
    STATUS_REVIEW,
    STATUS_NOT_APPLICABLE,
    STATUS_INCLUDED,
    STATUS_LATER,
]

@dataclass(frozen=True)
class SectionRequirement:
    code: str
    title: str
    aliases: tuple[str, ...]
    required: bool = True
    note: str = ""

# Базовые матрицы верхнего уровня. Они предназначены для контроля наличия
# разделов, а не для юридического вывода о применимости каждого решения.
CAPITAL_SECTIONS = (
    SectionRequirement("ПЗ", "Пояснительная записка", ("ПЗ", "ПЗ XML")),
    SectionRequirement("ПЗУ", "Схема планировочной организации земельного участка", ("ПЗУ",)),
    SectionRequirement("АР", "Объемно-планировочные и архитектурные решения", ("АР",)),
    SectionRequirement("КР", "Конструктивные решения", ("КР",)),
    SectionRequirement("ИОС", "Сведения об инженерном оборудовании, сетях и системах", ("ИОС1", "ИОС2", "ИОС3", "ИОС4", "ИОС5", "ИОС6", "ИОС7")),
    SectionRequirement("ТХ", "Технологические решения", ("ТХ",)),
    SectionRequirement("ПОС", "Проект организации строительства", ("ПОС",)),
    SectionRequirement("ПОД", "Проект организации работ по сносу или демонтажу", ("ПОД",), required=False, note="При наличии сноса или демонтажа"),
    SectionRequirement("ООС", "Мероприятия по охране окружающей среды", ("ООС",)),
    SectionRequirement("ПБ", "Мероприятия по обеспечению пожарной безопасности", ("ПБ",)),
    SectionRequirement("ОДИ", "Мероприятия по обеспечению доступа инвалидов", ("ОДИ",), required=False, note="С учетом назначения объекта"),
    SectionRequirement("ЭЭ", "Требования энергетической эффективности и оснащенности приборами учета", ("ЭЭ",), required=False, note="Может быть распределен по другим разделам"),
    SectionRequirement("СМ", "Смета на строительство", ("СМ",), required=False, note="В случаях, предусмотренных законодательством и заданием"),
    SectionRequirement("ИНАЯ", "Иная документация в случаях, предусмотренных законодательством", ("ГОЧС", "Прочее"), required=False),
)

LINEAR_SECTIONS = (
    SectionRequirement("ПЗ", "Пояснительная записка", ("ПЗ", "ПЗ XML")),
    SectionRequirement("ППО", "Проект полосы отвода", ("ППО", "ПЗУ")),
    SectionRequirement("ТКР", "Технологические и конструктивные решения линейного объекта", ("ТКР", "ТХ", "КР")),
    SectionRequirement("ИЛО", "Инфраструктура линейного объекта", ("ИЛО", "ИОС1", "ИОС2", "ИОС3", "ИОС4", "ИОС5", "ИОС6", "ИОС7")),
    SectionRequirement("ПОС", "Проект организации строительства", ("ПОС",)),
    SectionRequirement("ПОД", "Проект организации работ по сносу или демонтажу", ("ПОД",), required=False, note="При наличии сноса или демонтажа"),
    SectionRequirement("ООС", "Мероприятия по охране окружающей среды", ("ООС",)),
    SectionRequirement("ПБ", "Мероприятия по обеспечению пожарной безопасности", ("ПБ",)),
    SectionRequirement("СМ", "Смета на строительство", ("СМ",), required=False),
    SectionRequirement("ИНАЯ", "Иная документация в случаях, предусмотренных законодательством", ("ГОЧС", "Прочее"), required=False),
)


def requirements(profile: str) -> tuple[SectionRequirement, ...]:
    return LINEAR_SECTIONS if profile == PROFILE_LINEAR else CAPITAL_SECTIONS


def detected_families(document_types: Iterable[str]) -> set[str]:
    return {document_family(value) for value in document_types if value}


def build_matrix(document_types: Iterable[str], profile: str, decisions: dict[str, dict] | None = None) -> list[dict]:
    families = detected_families(document_types)
    decisions = decisions or {}
    rows: list[dict] = []
    for req in requirements(profile):
        matched = sorted(alias for alias in req.aliases if alias in families)
        auto_present = bool(matched)
        decision = decisions.get(req.code, {})
        user_status = str(decision.get("status") or STATUS_REVIEW)
        justification = str(decision.get("justification") or "")
        if auto_present:
            status = STATUS_PRESENT
        elif user_status in (STATUS_NOT_APPLICABLE, STATUS_INCLUDED, STATUS_LATER):
            status = user_status
        elif req.required:
            status = STATUS_MISSING
        else:
            status = STATUS_REVIEW
        rows.append({
            "Код": req.code,
            "Раздел": req.title,
            "Обязательность": "Базово обязателен" if req.required else "По применимости",
            "Обнаружен": "Да" if auto_present else "Нет",
            "Найденные части": ", ".join(matched) if matched else "—",
            "Решение пользователя": user_status,
            "Обоснование": justification,
            "Итоговый статус": status,
            "Примечание": req.note,
        })
    return rows


def summarize(matrix: list[dict], user_confirmed: bool = False, forming: bool = True) -> dict:
    total = len(matrix)
    present = sum(row["Итоговый статус"] == STATUS_PRESENT for row in matrix)
    resolved = sum(row["Итоговый статус"] in (STATUS_PRESENT, STATUS_NOT_APPLICABLE, STATUS_INCLUDED) for row in matrix)
    missing = sum(row["Итоговый статус"] == STATUS_MISSING for row in matrix)
    later = sum(row["Итоговый статус"] == STATUS_LATER for row in matrix)
    review = sum(row["Итоговый статус"] == STATUS_REVIEW for row in matrix)
    if forming:
        status = "Комплект формируется"
    elif missing:
        status = "Неполный комплект"
    elif review or later:
        status = "Требует уточнения"
    elif user_confirmed:
        status = "Подтверждена пользователем"
    else:
        status = "Автоматически проверена"
    return {
        "total": total,
        "present": present,
        "resolved": resolved,
        "missing": missing,
        "later": later,
        "review": review,
        "user_confirmed": bool(user_confirmed),
        "forming": bool(forming),
        "status": status,
        "coverage": round((resolved / total * 100) if total else 0),
    }
