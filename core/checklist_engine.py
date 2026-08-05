from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


class ChecklistEngine:
    def __init__(self, catalog_path: str | Path):
        self.catalog_path=Path(catalog_path)
        self.items=json.loads(self.catalog_path.read_text(encoding='utf-8')) if self.catalog_path.exists() else []

    def sections(self) -> list[str]:
        values=set()
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
        return {str(d.get('Раздел') or d.get('Тип документа') or '') for d in documents}

    @staticmethod
    def _matches_doc(required: set[str], doc_types: set[str]) -> bool:
        if 'ALL' in required:
            return True
        for req in required:
            if req in doc_types or any(dt.startswith(req) or req.startswith(dt) for dt in doc_types):
                return True
        return False

    def evaluate(self, documents: list[dict[str,Any]], comparisons: list[dict[str,Any]], findings: list[dict[str,Any]], *, source_file: str | None = None, section: str | None = None) -> list[dict[str,Any]]:
        doc_types=self._doc_types(documents)
        comparison_text=' '.join(' '.join(str(v) for v in c.values()) for c in comparisons).lower()
        finding_text=' '.join(' '.join(str(v) for v in f.values()) for f in findings).lower()
        results=[]
        for item in self.items:
            if source_file and item.get('source_file') != source_file:
                continue
            required=set(item.get('document_types') or ['ALL'])
            if section and section not in required and 'ALL' not in required:
                continue
            applicable=self._matches_doc(required,doc_types)
            level=item.get('automation_level','C')
            q=item.get('question','')
            low=q.lower()
            if not applicable:
                status='Нет данных'
                evidence='Для пункта не найден требуемый раздел документации.'
            elif level=='C':
                status='Требуется ручная проверка'; evidence='Пункт требует инженерной оценки пользователя.'
            elif level=='B':
                status='Подготовлено к проверке'; evidence='Требуемый раздел загружен. Необходимо изучить документ и подтвердить результат.'
            else:
                tokens=[t for t in ('площад','мощност','производительност','высот','этажност','объем','объём','количеств','экспликац','комплектност','давлен','диаметр','протяж') if t in low]
                linked=[t for t in tokens if t in comparison_text or t in finding_text]
                if tokens and linked:
                    status='Проверено автоматически'; evidence='Найдены связанные структурированные результаты: '+', '.join(linked)+'.'
                else:
                    status='Требуется подтверждение'; evidence='Автоматическое правило ещё не имеет достаточных структурированных доказательств.'
            results.append({**item,'status':status,'evidence':evidence,'applicable':applicable,'user_decision':'Не рассмотрено','user_comment':''})
        return results

    def summary(self, results: Iterable[dict[str,Any]]):
        results=list(results)
        return {
            'total':len(results),
            'automatic':sum(1 for x in results if x['status']=='Проверено автоматически'),
            'prepared':sum(1 for x in results if x['status'] in {'Подготовлено к проверке','Требуется подтверждение'}),
            'manual':sum(1 for x in results if x['status']=='Требуется ручная проверка'),
            'no_data':sum(1 for x in results if x['status']=='Нет данных'),
        }
