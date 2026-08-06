from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .normalization import normalize_text

PARAMETER_HINTS = {
    'площад': {'AREA_BUILD','AREA_TOTAL'},
    'строительн объем': {'VOLUME_BUILD','VOLUME'},
    'строительн объём': {'VOLUME_BUILD','VOLUME'},
    'высот': {'HEIGHT_BUILD'},
    'этаж': {'FLOORS'},
    'мощност': {'POWER_INSTALLED','POWER_CALCULATED','POWER_KTP'},
    'производительност': {'CAPACITY'},
    'пропускн способност': {'CAPACITY','FLOW_RATE'},
    'расход': {'FLOW_RATE'},
    'давлен': {'PRESSURE'},
    'диаметр': {'DIAMETER'},
    'протяж': {'LENGTH'},
    'длин': {'LENGTH'},
    'ширин': {'WIDTH'},
    'объем': {'VOLUME','RES_VOLUME','VOLUME_BUILD'},
    'объём': {'VOLUME','RES_VOLUME','VOLUME_BUILD'},
    'вместимост': {'VOLUME','RES_VOLUME'},
    'количеств': {'QUANTITY'},
    'напряжен': {'VOLTAGE'},
    'глубин': {'DEPTH'},
}

PRESENCE_PATTERNS = (
    'наличие','представлен','приведен','приведён','указан','отражен','отражён',
    'разработан','выполнен','предусмотрен','содержит','экспликац','ведомост','перечень',
)
MANUAL_PATTERNS = (
    'обоснованност','рациональност','достаточност','корректност','целесообразност',
    'удобство','визуальн','качество','оценить','проверить решения','соответствие требованиям заказчика',
)
NEGATIVE_STATUSES = ('РАСХОЖД','КОНФЛИКТ','НЕ СОВПАД','ОТСУТСТВ','НЕ НАЙДЕН')
POSITIVE_STATUSES = ('СОВПАД','ПОДТВЕРЖД','СООТВЕТСТВ')


class ChecklistEngine:
    def __init__(self, catalog_path: str | Path):
        self.catalog_path = Path(catalog_path)
        self.items = json.loads(self.catalog_path.read_text(encoding='utf-8')) if self.catalog_path.exists() else []
        self._mark_hierarchy()

    def _mark_hierarchy(self) -> None:
        groups: dict[tuple[str,str], list[dict[str,Any]]] = defaultdict(list)
        for item in self.items:
            groups[(str(item.get('source_file')), str(item.get('sheet')))].append(item)
        for rows in groups.values():
            numbers = [str(x.get('item_no') or '').strip() for x in rows]
            for item in rows:
                no = str(item.get('item_no') or '').strip()
                item['is_heading'] = bool(no and any(x.startswith(no + '.') for x in numbers))

    def sections(self) -> list[str]:
        values = set()
        for item in self.items:
            values.update(str(x) for x in (item.get('document_types') or []) if str(x) != 'ALL')
        return sorted(values)

    def checklist_files(self, section: str | None = None) -> list[str]:
        files=[]
        for item in self.items:
            required=set(item.get('document_types') or ['ALL'])
            if section and section not in required and 'ALL' not in required:
                continue
            files.append(str(item.get('source_file') or ''))
        return sorted(x for x in set(files) if x)

    def primary_section(self, source_file: str) -> str:
        c=Counter()
        for item in self.items:
            if item.get('source_file') != source_file:
                continue
            c.update(x for x in (item.get('document_types') or []) if x != 'ALL')
        return c.most_common(1)[0][0] if c else 'ALL'

    @staticmethod
    def _doc_types(documents: list[dict[str,Any]]) -> set[str]:
        result=set()
        for d in documents:
            for key in ('Раздел','Тип документа','document_type','family'):
                value=str(d.get(key) or '').strip()
                if value: result.add(value)
        return result

    @staticmethod
    def _document_names(documents: list[dict[str,Any]]) -> set[str]:
        result=set()
        for d in documents:
            for key in ('Файл','Имя файла','name','filename','document'):
                value=str(d.get(key) or '').strip()
                if value: result.add(normalize_text(value))
        return result

    @staticmethod
    def _matches_doc(required: set[str], doc_types: set[str]) -> bool:
        if 'ALL' in required: return True
        return any(req in doc_types or any(dt.startswith(req) or req.startswith(dt) for dt in doc_types) for req in required)

    @staticmethod
    def _selected_findings(findings: list[dict[str,Any]], documents: list[dict[str,Any]], section: str | None) -> list[dict[str,Any]]:
        names=ChecklistEngine._document_names(documents)
        out=[]
        for f in findings:
            doc=normalize_text(f.get('document') or f.get('Файл') or '')
            dtype=str(f.get('document_type') or f.get('Раздел') or '')
            if names and doc and doc not in names and not any(n in doc or doc in n for n in names):
                continue
            if section and dtype and not (dtype.startswith(section) or section.startswith(dtype)):
                # filename match has priority; otherwise keep only selected section
                if not doc or not names: continue
            out.append(f)
        return out

    @staticmethod
    def _finding_blob(findings: list[dict[str,Any]]) -> str:
        fields=('parameter_name','parameter_code','value_text','object_hint','context','section_title','structural_zone','table_title','table_evidence','match_method')
        return normalize_text(' '.join(' '.join(str(f.get(k) or '') for k in fields) for f in findings))

    @staticmethod
    def _comparison_codes(question: str) -> set[str]:
        low=normalize_text(question)
        codes=set()
        for hint,values in PARAMETER_HINTS.items():
            if hint in low: codes.update(values)
        return codes

    @staticmethod
    def _comparison_status(comparisons: list[dict[str,Any]], codes: set[str], selected_docs: set[str]) -> tuple[str|None,str]:
        relevant=[]
        for c in comparisons:
            code=str(c.get('parameter_code') or c.get('code') or '').upper()
            if codes and code not in codes: continue
            sources=normalize_text(c.get('sources') or c.get('Источники') or c.get('sections') or '')
            if selected_docs and sources and not any(n in sources or sources in n for n in selected_docs):
                # comparisons may store section names rather than filenames; do not over-filter
                pass
            relevant.append(c)
        if not relevant: return None,''
        statuses=[str(c.get('status') or c.get('Статус') or '').upper() for c in relevant]
        if any(any(tok in s for tok in NEGATIVE_STATUSES) for s in statuses):
            return 'Нет','Выявлено расхождение или отсутствие данных в структурированной сверке.'
        if any(any(tok in s for tok in POSITIVE_STATUSES) for s in statuses):
            return 'Да','Имеется положительный структурированный результат межраздельной сверки.'
        return 'Требует проверки','Структурированные сведения найдены, но автоматический вывод недостаточен.'

    def evaluate(self, documents: list[dict[str,Any]], comparisons: list[dict[str,Any]], findings: list[dict[str,Any]], *, source_file: str | None = None, section: str | None = None) -> list[dict[str,Any]]:
        doc_types=self._doc_types(documents)
        selected_findings=self._selected_findings(findings,documents,section)
        blob=self._finding_blob(selected_findings)
        selected_doc_names=self._document_names(documents)
        results=[]
        for item in self.items:
            if source_file and item.get('source_file') != source_file: continue
            required=set(item.get('document_types') or ['ALL'])
            if section and section not in required and 'ALL' not in required: continue
            q=str(item.get('question') or '').strip()
            low=normalize_text(q)
            applicable=self._matches_doc(required,doc_types)
            evidence=''
            if item.get('is_heading'):
                status='Раздел'
                evidence='Группирующая позиция чек-листа.'
            elif not applicable or not documents:
                status='Нет данных'
                evidence='Выбранный раздел или документ не соответствует пункту чек-листа.'
            else:
                codes=self._comparison_codes(q)
                if codes:
                    status,evidence=self._comparison_status(comparisons,codes,selected_doc_names)
                    if status is None:
                        status='Требует проверки'; evidence='Для параметра не найден достаточный структурированный результат.'
                elif any(x in low for x in MANUAL_PATTERNS):
                    status='Требует проверки'; evidence='Пункт требует инженерной оценки содержания и качества решений.'
                elif any(x in low for x in PRESENCE_PATTERNS):
                    # Use significant words from the checklist item, not generic full-text matching.
                    words=[w for w in re.findall(r'[а-яa-z0-9]{4,}',low) if w not in {'наличие','проверить','соответствие','раздела','проектной','документации','требованиям','должен','должна','должны'}]
                    matched=[w for w in words if w in blob]
                    threshold=1 if len(words)<=3 else 2
                    if len(matched)>=threshold:
                        status='Да'; evidence='В выбранном разделе найдены релевантные структурированные признаки: '+', '.join(matched[:5])+'.'
                    else:
                        status='Требует проверки'; evidence='Наличие требуемого решения не подтверждено структурированными данными.'
                else:
                    status='Требует проверки'; evidence='Пункт пока не имеет надёжного автоматического правила.'
            results.append({**item,'status':status,'evidence':evidence,'applicable':applicable,'user_decision':'Не рассмотрено','user_comment':''})
        return results

    def summary(self, results: Iterable[dict[str,Any]]):
        results=list(results)
        return {
            'total':sum(1 for x in results if x['status']!='Раздел'),
            'yes':sum(1 for x in results if x['status']=='Да'),
            'no':sum(1 for x in results if x['status']=='Нет'),
            'review':sum(1 for x in results if x['status']=='Требует проверки'),
            'no_data':sum(1 for x in results if x['status']=='Нет данных'),
        }
