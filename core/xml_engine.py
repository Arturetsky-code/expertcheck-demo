from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re
import xml.etree.ElementTree as ET

from .normalization import canonical_parameter, normalize_measure, normalize_numeric


@dataclass
class XmlParseResult:
    document: dict[str, Any]
    findings: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _text(node: ET.Element | None, *paths: str, default: str = "") -> str:
    if node is None:
        return default
    for path in paths:
        found = node.find(path)
        if found is not None and found.text and found.text.strip():
            return found.text.strip()
    return default


def _all_text(node: ET.Element, path: str) -> list[str]:
    return [e.text.strip() for e in node.findall(path) if e.text and e.text.strip()]


def _float_value(value: str) -> float | None:
    return normalize_numeric(value)


def _split_tei_name(name: str) -> tuple[str, str]:
    """Разделяет имя объекта и характеристику в XML 01.06/01.07.

    В 01.07 обычно используется запятая, а в 01.06 — точка:
    «Общежитие, площадь застройки» и «Пионерная дамба. Высота».
    """
    keywords = (
        "площад", "объем", "объём", "этаж", "высот", "длин", "мощност",
        "производитель", "вместим", "количеств", "протяж", "диаметр", "класс"
    )
    for separator in (",", "."):
        parts = [p.strip() for p in name.rsplit(separator, 1)]
        if len(parts) == 2 and parts[0] and any(k in parts[1].lower() for k in keywords):
            return parts[0], parts[1]
    return "Не определён", name


class BaseAdapter:
    version = "unknown"

    def parse(self, root: ET.Element, filename: str) -> XmlParseResult:
        number = _text(root, "ExplanatoryNoteNumber")
        year = _text(root, "ExplanatoryNoteYear")
        issue_org = self.issue_org(root)
        signer = self.chief_engineer(root)
        project_name = self.project_name(root)
        object_node = self.primary_object(root)

        document = {
            "Файл": filename,
            "Раздел": "ПЗ XML",
            "Тип документа": "Пояснительная записка XML",
            "Формат": "XML",
            "XML версия": self.version,
            "Шифр": number,
            "Год": year,
            "Наименование проекта": project_name,
            "Организация-разработчик": issue_org,
            "ГИП": signer,
            "core_version": "3.0-alpha2",
        }
        findings: list[dict[str, Any]] = []

        def add(parameter_code: str, parameter_name: str, value: str, *, unit: str = "", object_hint: str = "Не определён", method: str = "XML"):
            if value in (None, ""):
                return
            findings.append({
                "document": filename,
                "page": 0,
                "section": "ПЗ XML",
                "parameter_code": parameter_code,
                "parameter_name": parameter_name,
                "value_text": str(value),
                "value_num": _float_value(str(value)),
                "value": _float_value(str(value)),
                "unit": unit,
                "document_type": "ПЗ XML",
                "object_hint": object_hint,
                "genplan_position": "",
                "confidence": 1.0,
                "match_method": method,
                "structural_zone": "xml",
                "xml_schema_version": self.version,
                "source_kind": "xml",
            })

        add("PROJECT_NAME", "Наименование проекта", project_name)
        add("PROJECT_CODE", "Шифр ПЗ", number)
        add("PROJECT_YEAR", "Год ПЗ", year)
        add("ISSUE_AUTHOR", "Организация-разработчик", issue_org)
        add("CHIEF_ENGINEER", "Главный инженер проекта", signer)

        if object_node is not None:
            main_name = _text(object_node, "Name") or project_name
            add("OBJECT_ENTRY", "Объект проекта", main_name, object_hint=main_name, method="XML object node")
            add("CONSTRUCTION_TYPE", "Вид строительства", _text(object_node, "ConstructionType"), object_hint=main_name)
            add("RESPONSIBILITY_LEVEL", "Уровень ответственности", _text(object_node, "ResponsibilityLevel"), object_hint=main_name)
            add("FIRE_DANGER", "Категория пожарной опасности", _text(object_node, "FireDangerCategory"), object_hint=main_name)

            for tei in object_node.findall("TEI"):
                raw_name = _text(tei, "Name")
                value = _text(tei, "Value")
                measure = _text(tei, "Measure")
                obj_name, characteristic = _split_tei_name(raw_name)
                normalized = canonical_parameter(characteristic)
                # Частные короткие показатели уточняем по типу объекта.
                characteristic_low = characteristic.lower().replace("ё", "е")
                object_low = obj_name.lower().replace("ё", "е")
                if normalized.code == "XML_TEI" and characteristic_low.strip() in {"объем", "объём", "вместимость"} and any(token in object_low for token in ("резервуар", "емкост", "ёмкост")):
                    normalized = canonical_parameter("объем резервуара")
                elif normalized.code == "XML_TEI" and characteristic_low.strip().startswith("высот"):
                    normalized = canonical_parameter("высота сооружения")
                normalized_unit, unit_confidence = normalize_measure(measure, normalized.unit)
                if normalized.code == "FLOORS":
                    normalized_unit, unit_confidence = "эт.", 1.0
                add(normalized.code, normalized.name, value, unit=normalized_unit, object_hint=obj_name, method="XML TEI normalized")
                if findings:
                    findings[-1]["raw_parameter_name"] = raw_name
                    findings[-1]["raw_measure"] = measure
                    findings[-1]["normalization_confidence"] = round(min(normalized.confidence, unit_confidence or normalized.confidence), 3)
                if obj_name != "Не определён":
                    add("OBJECT_CANDIDATE", "Кандидат объекта из ТЭП XML", obj_name, object_hint=obj_name, method="XML TEI object")

            power = object_node.find("PowerIndicator")
            if power is not None:
                power_name = _text(power, "Name") or "Проектная мощность"
                normalized = canonical_parameter(power_name)
                unit, unit_confidence = normalize_measure(_text(power, "Measure"), normalized.unit)
                add(normalized.code if normalized.code != "XML_TEI" else "CAPACITY", normalized.name if normalized.code != "XML_TEI" else power_name, _text(power, "Value"), unit=unit, object_hint=main_name, method="XML PowerIndicator normalized")
                if findings:
                    findings[-1]["raw_parameter_name"] = power_name
                    findings[-1]["raw_measure"] = _text(power, "Measure")
                    findings[-1]["normalization_confidence"] = round(unit_confidence, 3)

            for resource in object_node.findall("./Resources/Resource"):
                name = _text(resource, "Name")
                unit, unit_confidence = normalize_measure(_text(resource, "Measure"))
                add("RESOURCE", f"Потребность: {name}", _text(resource, "Value"), unit=unit, object_hint=main_name, method="XML Resource")
                if findings:
                    findings[-1]["raw_measure"] = _text(resource, "Measure")
                    findings[-1]["normalization_confidence"] = round(unit_confidence, 3)

        used_norms = _all_text(root, "./UsedNorms/UsedNorm")
        initial_documents = [self._document_card(node) for node in root.findall("./ProjectInitialDocuments/Document")]
        survey_documents = [self._document_card(node) for node in root.findall("./EngineeringSurveyDocuments/Document")]
        project_sections = self._project_sections(root)
        document["xml_summary"] = {
            "schema_version": self.version,
            "findings": len(findings),
            "tei_count": sum(1 for f in findings if f.get("match_method") == "XML TEI normalized"),
            "normalized_tei_count": sum(1 for f in findings if f.get("parameter_code") not in {"XML_TEI", "OBJECT_CANDIDATE", "OBJECT_ENTRY", "PROJECT_NAME", "PROJECT_CODE", "PROJECT_YEAR", "ISSUE_AUTHOR", "CHIEF_ENGINEER"}),
            "object_candidates": len({f.get("object_hint") for f in findings if f.get("parameter_code") == "OBJECT_CANDIDATE"}),
            "used_norms": len(used_norms),
            "initial_documents": len(initial_documents),
            "survey_documents": len(survey_documents),
            "project_sections": len(project_sections),
        }
        document["xml_used_norms"] = used_norms
        document["xml_initial_documents"] = initial_documents
        document["xml_survey_documents"] = survey_documents
        document["xml_project_sections"] = project_sections
        return XmlParseResult(document=document, findings=findings)


    def _document_card(self, node: ET.Element) -> dict[str, str]:
        return {
            "type": _text(node, "DocType"),
            "name": _text(node, "DocName"),
            "number": _text(node, "DocNumber"),
            "date": _text(node, "DocDate"),
            "issuer": _text(node, "DocIssueAuthor"),
            "file": _text(node, "./File/FileName"),
        }

    def _project_sections(self, root: ET.Element) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        project_docs = root.find(".//ProjectDocumentation")
        if project_docs is None:
            return sections
        for section in list(project_docs):
            docs = []
            for node in section.findall(".//Document"):
                card = self._document_card(node)
                card["files"] = _all_text(node, ".//FileName")
                docs.append(card)
            if docs:
                sections.append({"section": section.tag, "documents": docs})
        return sections

    def issue_org(self, root: ET.Element) -> str:
        raise NotImplementedError

    def chief_engineer(self, root: ET.Element) -> str:
        raise NotImplementedError

    def primary_object(self, root: ET.Element) -> ET.Element | None:
        for tag in ("NonIndustrialObject", "IndustrialObject", "LinearObject"):
            node = root.find(tag)
            if node is not None:
                return node
        return None

    def project_name(self, root: ET.Element) -> str:
        node = self.primary_object(root)
        return _text(node, "Name") if node is not None else ""


class Adapter0106(BaseAdapter):
    version = "01.06"
    def issue_org(self, root: ET.Element) -> str:
        return _text(root, "./IssueAuthor/Organization/OrgFullName")
    def chief_engineer(self, root: ET.Element) -> str:
        node = root.find("./Signers/ChiefProjectEngineer")
        return " ".join(filter(None, [_text(node, "FamilyName"), _text(node, "FirstName"), _text(node, "SecondName")]))


class Adapter0107(BaseAdapter):
    version = "01.07"
    def issue_org(self, root: ET.Element) -> str:
        return _text(root, "./IssueAuthor/Organization/FullName")
    def chief_engineer(self, root: ET.Element) -> str:
        node = root.find("./Signers/ChiefProjectEngineer")
        return " ".join(filter(None, [_text(node, "Surname"), _text(node, "Name"), _text(node, "Patronymic")]))


class XmlEngine:
    adapters = {"01.06": Adapter0106(), "01.07": Adapter0107()}

    def detect_version(self, data: bytes) -> str:
        head = data[:4096].decode("utf-8", errors="ignore")
        match = re.search(r'SchemaVersion=["\']([^"\']+)', head)
        return match.group(1) if match else "unknown"

    def parse_bytes(self, data: bytes, filename: str) -> XmlParseResult:
        version = self.detect_version(data)
        adapter = self.adapters.get(version)
        if adapter is None:
            return XmlParseResult(
                document={"Файл": filename, "Раздел": "ПЗ XML", "Тип документа": "XML", "Формат": "XML", "XML версия": version},
                warnings=[f"XML-схема {version} пока не поддерживается"],
            )
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            return XmlParseResult(
                document={"Файл": filename, "Раздел": "ПЗ XML", "Тип документа": "XML", "Формат": "XML", "XML версия": version},
                warnings=[f"Ошибка разбора XML: {exc}"],
            )
        result = adapter.parse(root, filename)
        result.document["xml_warnings"] = result.warnings
        return result

    def parse_uploaded(self, files) -> tuple[list[dict], list[dict], list[str]]:
        docs, findings, warnings = [], [], []
        for uploaded in files:
            result = self.parse_bytes(uploaded.getvalue(), uploaded.name)
            docs.append(result.document)
            findings.extend(result.findings)
            warnings.extend([f"{uploaded.name}: {w}" for w in result.warnings])
        return docs, findings, warnings
