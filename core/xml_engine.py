from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re
import xml.etree.ElementTree as ET


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
    try:
        return float(value.replace(" ", "").replace(",", "."))
    except (ValueError, AttributeError):
        return None


def _split_tei_name(name: str) -> tuple[str, str]:
    """Разделяет 'Общежитие, площадь застройки' на объект и характеристику."""
    parts = [p.strip() for p in name.rsplit(",", 1)]
    if len(parts) == 2 and any(k in parts[1].lower() for k in (
        "площад", "объем", "объём", "этаж", "высот", "длин", "мощност",
        "производитель", "вместим", "количеств", "протяж"
    )):
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
            "core_version": "3.0-alpha1",
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
                "unit": unit,
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
                add("XML_TEI", characteristic, value, unit=measure, object_hint=obj_name, method="XML TEI")
                if obj_name != "Не определён":
                    add("OBJECT_CANDIDATE", "Кандидат объекта из ТЭП XML", obj_name, object_hint=obj_name, method="XML TEI object")

            power = object_node.find("PowerIndicator")
            if power is not None:
                add("PROJECT_POWER", _text(power, "Name") or "Проектная мощность", _text(power, "Value"), unit=_text(power, "Measure"), object_hint=main_name, method="XML PowerIndicator")

            for resource in object_node.findall("./Resources/Resource"):
                name = _text(resource, "Name")
                add("RESOURCE", f"Потребность: {name}", _text(resource, "Value"), unit=_text(resource, "Measure"), object_hint=main_name, method="XML Resource")

        document["xml_summary"] = {
            "schema_version": self.version,
            "findings": len(findings),
            "tei_count": sum(1 for f in findings if f.get("parameter_code") == "XML_TEI"),
            "object_candidates": len({f.get("object_hint") for f in findings if f.get("parameter_code") == "OBJECT_CANDIDATE"}),
            "used_norms": len(root.findall("./UsedNorms/UsedNorm")),
            "initial_documents": len(root.findall("./ProjectInitialDocuments/Document")),
            "survey_documents": len(root.findall("./EngineeringSurveyDocuments/Document")),
        }
        return XmlParseResult(document=document, findings=findings)

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
