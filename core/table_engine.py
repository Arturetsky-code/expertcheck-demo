from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any


@dataclass
class StructuredRow:
    parameter_code: str
    parameter_name: str
    unit: str
    value_text: str
    value_num: float | None
    source_lines: list[str] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TableCandidate:
    table_type: str
    score: float
    headers: list[str]
    rows: list[list[str]]
    evidence: list[str]
    structured_rows: list[StructuredRow] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


class TableEngine:
    """Каталожно-управляемый классификатор и извлекатель инженерных таблиц.

    Alpha 4 распознаёт тип таблицы и восстанавливает типовые строки ТЭП,
    даже если показатель, единица и значение находятся на соседних строках
    текстового слоя PDF.
    """

    _NUMBER = re.compile(r"(?<![\w.])[-+]?\d{1,3}(?:[ \u00a0]\d{3})*(?:[,.]\d+)?(?![\w.])")
    _UNIT = re.compile(
        r"(?:м²|м2|кв\.?\s*м|м³|м3|куб\.?\s*м|ква|квт|мвт|т/ч|т/год|м³/ч|м3/ч|"
        r"чел\.?|шт\.?|ед\.?|км|мм|м)",
        re.IGNORECASE,
    )

    def __init__(self, catalog: list[dict], parameter_catalog: list[dict] | None = None):
        self.catalog = catalog
        self.parameters = parameter_catalog or []
        self.alias_index: list[tuple[str, dict]] = []
        for parameter in self.parameters:
            aliases = [parameter.get("name", ""), *(parameter.get("aliases") or [])]
            for alias in aliases:
                normalized = self._normalize(alias)
                if normalized:
                    self.alias_index.append((normalized, parameter))
        self.alias_index.sort(key=lambda item: len(item[0]), reverse=True)

    @staticmethod
    def _normalize(value: str) -> str:
        value = (value or "").lower().replace("ё", "е")
        value = value.replace("²", "2").replace("³", "3")
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _lines(cls, text: str) -> list[str]:
        return [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]

    @staticmethod
    def _to_float(value: str) -> float | None:
        try:
            return float(value.replace("\u00a0", "").replace(" ", "").replace(",", "."))
        except (TypeError, ValueError):
            return None

    def _parameter_at(self, line: str) -> dict | None:
        normalized = self._normalize(line)
        for alias, parameter in self.alias_index:
            if alias in normalized:
                return parameter
        return None

    def _extract_structured_rows(self, lines: list[str]) -> list[StructuredRow]:
        rows: list[StructuredRow] = []
        seen: set[tuple[str, str, str]] = set()
        for index, line in enumerate(lines):
            parameter = self._parameter_at(line)
            if not parameter:
                continue
            window = [line]
            for following in lines[index + 1:index + 5]:
                # Следующий распознанный показатель начинает новую строку таблицы.
                if self._parameter_at(following):
                    break
                window.append(following)
            combined = " | ".join(window)
            unit_match = self._UNIT.search(combined)
            numbers: list[str] = []
            for candidate_line in window:
                numbers.extend(match.group(0) for match in self._NUMBER.finditer(candidate_line))
            # Убираем номера пунктов/позиций, совпадающие с началом строки показателя.
            numbers = [n for n in numbers if not re.match(r"^\d+(?:\.\d+)+$", n.strip())]
            if not numbers:
                continue
            expected_unit = str(parameter.get("unit") or "")
            unit = unit_match.group(0) if unit_match else expected_unit
            # Последнее число до начала следующего показателя является значением строки ТЭП.
            value_text = numbers[-1]
            key = (str(parameter.get("id")), value_text, unit.lower())
            if key in seen:
                continue
            seen.add(key)
            score = 0.55
            if unit_match:
                score += 0.20
            if expected_unit and self._normalize(expected_unit) in self._normalize(unit):
                score += 0.10
            if len(window) >= 2:
                score += 0.05
            rows.append(
                StructuredRow(
                    parameter_code=str(parameter.get("id") or ""),
                    parameter_name=str(parameter.get("name") or ""),
                    unit=unit,
                    value_text=value_text,
                    value_num=self._to_float(value_text),
                    source_lines=window,
                    score=round(min(score, 0.95), 3),
                )
            )
        return rows

    def detect(self, text: str, document_type: str = "") -> list[TableCandidate]:
        lines = self._lines(text)
        low = "\n".join(lines).lower().replace("ё", "е")
        result: list[TableCandidate] = []
        for template in self.catalog:
            scope = set(template.get("scope") or [])
            if document_type and scope and document_type not in scope:
                continue
            tokens = [x.lower().replace("ё", "е") for x in template.get("header_tokens", [])]
            hits = [x for x in tokens if x in low]
            score = len(hits) / max(1, len(tokens))
            row_hits = [x for x in template.get("row_tokens", []) if x.lower().replace("ё", "е") in low]
            if row_hits:
                score = min(1.0, score + min(0.20, 0.04 * len(row_hits)))
            if score < template.get("threshold", 0.5):
                continue
            rows: list[list[str]] = []
            for line in lines:
                if re.match(r"^\d+(?:\.\d+)*\s+", line) or any(
                    keyword in line.lower() for keyword in template.get("row_tokens", [])
                ):
                    rows.append([line])
            structured = []
            if "TEP" in str(template.get("id", "")):
                structured = self._extract_structured_rows(lines)
            evidence = [f"найдено заголовков: {len(hits)}", f"найдено признаков строк: {len(row_hits)}"]
            if structured:
                evidence.append(f"восстановлено строк ТЭП: {len(structured)}")
            result.append(
                TableCandidate(
                    str(template["id"]),
                    round(score, 3),
                    hits,
                    rows[:100],
                    evidence,
                    structured,
                )
            )
        return sorted(result, key=lambda x: (x.score, len(x.structured_rows)), reverse=True)
