from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class ChecklistEngine:
    def __init__(self, catalog_path: str | Path):
        self.catalog_path=Path(catalog_path)
        self.items=json.loads(self.catalog_path.read_text(encoding='utf-8')) if self.catalog_path.exists() else []

    def evaluate(self, documents: list[dict[str,Any]], comparisons: list[dict[str,Any]], findings: list[dict[str,Any]]) -> list[dict[str,Any]]:
        doc_types={str(d.get('Раздел') or d.get('Тип документа') or '') for d in documents}
        comparison_text=' '.join(' '.join(str(v) for v in c.values()) for c in comparisons).lower()
        finding_text=' '.join(' '.join(str(v) for v in f.values()) for f in findings).lower()
        results=[]
        for item in self.items:
            required=set(item.get('document_types') or ['ALL'])
            applicable='ALL' in required or bool(required & doc_types) or any(any(dt.startswith(x) for dt in doc_types) for x in required)
            level=item.get('automation_level','C')
            q=item.get('question','')
            low=q.lower()
            if not applicable:
                status='Нет данных / не применено'
                evidence='Требуемый раздел не загружен или применимость не подтверждена.'
            elif level=='C':
                status='Требуется ручная проверка'; evidence='Пункт требует инженерной оценки.'
            elif level=='B':
                status='Подготовлено к проверке'; evidence='Документы найдены; требуется подтверждение специалиста.'
            else:
                tokens=[t for t in ('площад','мощност','производительност','высот','этажност','объем','объём','количеств','экспликац','комплектност') if t in low]
                has_result=any(t in comparison_text or t in finding_text for t in tokens) if tokens else True
                status='Проверено автоматически' if has_result else 'Недостаточно данных'
                evidence='Связанные автоматические результаты найдены.' if has_result else 'Не найдено достаточных структурированных доказательств.'
            results.append({**item,'status':status,'evidence':evidence,'applicable':applicable})
        return results

    def summary(self, results):
        return {
            'total':len(results),
            'automatic':sum(1 for x in results if x['status']=='Проверено автоматически'),
            'prepared':sum(1 for x in results if x['status']=='Подготовлено к проверке'),
            'manual':sum(1 for x in results if x['status']=='Требуется ручная проверка'),
            'no_data':sum(1 for x in results if x['status'] in {'Недостаточно данных','Нет данных / не применено'}),
        }
