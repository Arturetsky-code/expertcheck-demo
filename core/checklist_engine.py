from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .normalization import normalize_text
from .checklist_compiler import compile_item
from .pp87_matrix import evaluate_pp87
from .engineering_review_engine import CrossSectionDependencyEngine
from .expert_practice_intelligence import ExpertPracticeIntelligence
from .typed_check_engine import execute_typed_check
from .verification_factory import build_factory_catalog, recipe_lookup
from .page_evidence_store import section_matches

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
    'влажност': {'MOISTURE'},
    'насыпн плотност': {'BULK_DENSITY'},
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
        self.items.extend(self._load_pack_checklists())
        self.review_engine = CrossSectionDependencyEngine(self.catalog_path.parent)
        self.expert_practice = ExpertPracticeIntelligence(self.catalog_path.parent)
        try:
            self.verification_factory = build_factory_catalog(self.catalog_path.parent)
            self.recipe_lookup = recipe_lookup(self.verification_factory)
        except Exception:
            self.verification_factory = {'total':0,'trusted_count':0,'experimental_count':0,'by_domain':{}}
            self.recipe_lookup = {}
        self._mark_hierarchy()

    def _load_pack_checklists(self) -> list[dict[str, Any]]:
        """Load curated checklist packs that were previously shipped but not executed.

        Pack rows are converted to the same stable contract as the base catalog.
        IDs are deduplicated so the loader remains safe when a pack is later
        incorporated into ``checklist_catalog.json``.
        """
        known = {str(item.get('id') or '') for item in self.items}
        result: list[dict[str, Any]] = []
        pack_paths = (
            self.catalog_path.parent / 'packs' / 'corporate' / 'checklists' / 'technology.json',
        )
        automation_map = {
            'автоматическая': 'A',
            'автоматическая/частичная': 'B',
            'частичная': 'B',
            'ручная': 'C',
        }
        for path in pack_paths:
            if not path.exists():
                continue
            try:
                rows = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                continue
            for index, row in enumerate(rows if isinstance(rows, list) else [], 1):
                if not isinstance(row, dict) or row.get('enabled') is False:
                    continue
                row_id = str(row.get('id') or f'PACK-{path.stem.upper()}-{index:04d}')
                if row_id in known:
                    continue
                known.add(row_id)
                scope = [str(value) for value in row.get('scope') or ['ALL'] if str(value).strip()]
                result.append({
                    'id': row_id,
                    'source_file': str(row.get('source') or path.stem),
                    'sheet': str(row.get('section') or (scope[0] if scope else 'Общее')),
                    'row': index,
                    'item_no': str(row.get('source_ref') or index),
                    'section': str(row.get('section') or (scope[0] if scope else 'Общее')),
                    'priority': str(row.get('priority') or ''),
                    'question': str(row.get('title') or ''),
                    'where_to_check': '',
                    'risk': '',
                    'automation_level': automation_map.get(str(row.get('automation') or '').lower(), 'C'),
                    'document_types': scope or ['ALL'],
                    'pack_source': str(path.relative_to(self.catalog_path.parent)),
                    'rule_kind': str(row.get('rule_kind') or 'checklist_requirement'),
                })
        return result

    def _mark_hierarchy(self) -> None:
        section_titles = {
            'конструктивные решения', 'архитектурные решения',
            'технологические решения', 'система электроснабжения',
            'система водоснабжения', 'система водоотведения',
            'схема планировочной организации земельного участка',
            'организация строительства', 'пояснительная записка',
        }
        groups: dict[tuple[str,str], list[dict[str,Any]]] = defaultdict(list)
        for item in self.items:
            groups[(str(item.get('source_file')), str(item.get('sheet')))].append(item)
        for rows in groups.values():
            numbers = [str(x.get('item_no') or '').strip() for x in rows]
            for item in rows:
                no = str(item.get('item_no') or '').strip()
                question = normalize_text(item.get('question') or '')
                explicit_section_title = bool(
                    re.fullmatch(r'\d{1,2}', no)
                    and question in section_titles
                )
                item['is_heading'] = bool(
                    no and any(x.startswith(no + '.') for x in numbers)
                    or explicit_section_title
                )

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
            if section and not section_matches(dtype or doc,[section]):
                continue
            if section and not doc and not dtype:
                continue
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
                # Section codes are accepted, but an unrelated comparison must
                # not become evidence for the selected checklist profile.
                selected_sections={str(x).upper() for x in selected_docs if len(str(x))<=8}
                if not any(section_matches(sources,[section]) for section in selected_sections):
                    continue
            relevant.append(c)
        if not relevant: return None,''
        statuses=[str(c.get('status') or c.get('Статус') or '').upper() for c in relevant]
        if any(any(tok in s for tok in NEGATIVE_STATUSES) for s in statuses):
            return 'Нет','Выявлено расхождение или отсутствие данных в структурированной сверке.'
        if any(any(tok in s for tok in POSITIVE_STATUSES) for s in statuses):
            return 'Да','Имеется положительный структурированный результат межраздельной сверки.'
        return 'Требует проверки','Структурированные сведения найдены, но автоматический вывод недостаточен.'

    def evaluate(self, documents: list[dict[str,Any]], comparisons: list[dict[str,Any]], findings: list[dict[str,Any]], *, source_file: str | None = None, section: str | None = None, include_practice: bool = True) -> list[dict[str,Any]]:
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
            compiled=compile_item(item)
            applicable=self._matches_doc(required,doc_types)
            evidence=''
            proof_kind='UNSUPPORTED'
            if item.get('is_heading'):
                status='Раздел'
                evidence='Группирующая позиция чек-листа.'
                proof_kind='HEADING'
            elif not applicable or not documents:
                status='Нет данных'
                evidence='Выбранный раздел или документ не соответствует пункту чек-листа.'
                proof_kind='NOT_APPLICABLE_OR_MISSING_SCOPE'
            else:
                codes=set(compiled.parameter_codes)
                if compiled.rule_type in {'numeric_crosscheck','parameter_evidence'} and codes:
                    status,evidence=self._comparison_status(comparisons,codes,selected_doc_names)
                    if status is not None:
                        proof_kind='STRUCTURED_COMPARISON'
                    if status is None:
                        # A parameter may be present in one selected document but not yet cross-comparable.
                        present=[f for f in selected_findings if str(f.get('parameter_code') or '').upper() in codes]
                        if present and compiled.rule_type=='parameter_evidence':
                            status='Да'; evidence=f'Найдено структурированных значений: {len(present)}. Источник: выбранный раздел.'; proof_kind='STRUCTURED_VALUE'
                        else:
                            status='Не проверено системой'; evidence='Для параметра не получено достаточного структурированного доказательства.'; proof_kind='UNSUPPORTED'
                elif compiled.rule_type in {'presence','semantic_review'} or compiled.typed_check in {'DRAWING_TITLE_BLOCK_CHECK','DRAWING_PRESENCE_CHECK','DOCUMENT_CONTENT_PRESENCE','ENGINEERING_SEMANTIC_REVIEW','NORMATIVE_CONTENT_REVIEW','SPECIALIST_REVIEW'}:
                    typed=execute_typed_check(compiled.to_dict(),selected_findings,documents)
                    if typed:
                        status=typed['status']; evidence=typed['evidence']; proof_kind=typed.get('proof_kind','UNSUPPORTED')
                    else:
                        status='Не проверено системой'; evidence='Для пункта отсутствует доказательный автоматический алгоритм.'
                else:
                    status='Не проверено системой'; evidence='Пункт пока не имеет надёжного автоматического правила.'
            compiled_dict=compiled.to_dict()
            recipe=self.recipe_lookup.get(str(item.get('id') or ''))
            if recipe is None:
                # Experimental recipe metadata is useful diagnostically, but never grants a positive result.
                factory_rows=(self.verification_factory.get('experimental') or []) if isinstance(self.verification_factory,dict) else []
                recipe=next((x for x in factory_rows if str(x.get('source_id') or '')==str(item.get('id') or '')),None)
            if recipe and recipe.get('recipe_status')!='TRUSTED' and status=='Да':
                status='Не проверено системой'
                evidence=(evidence+' ' if evidence else '')+'Автоматический рецепт пока не прошёл critic/regression gate; положительный вывод удержан.'
                proof_kind='UNSUPPORTED'
            deterministic_checkers={
                'ENGINEERING_VALUE_CROSSCHECK', 'ENGINEERING_PARAMETER_PRESENCE',
            }
            automatic_verdict_eligible=compiled.typed_check in deterministic_checkers
            if status=='Да' and not automatic_verdict_eligible:
                status='Требует проверки'
                evidence=(evidence+' ' if evidence else '')+(
                    'Найденный фрагмент сохранён как кандидат; данный тип пункта не имеет '
                    'специализированного детерминированного checker-а для автоматического закрытия.'
                )
                proof_kind='CANDIDATE_EVIDENCE'
            normative_context=self.review_engine.checklist_context(q, compiled_dict)
            if include_practice:
                practice_context=self.expert_practice.risk_from_evidence(
                    q, section or "", "",
                    ["MISSING_INFORMATION"] if compiled.rule_type in {"presence","mandatory_document"} else
                    ["CROSS_SECTION_MISMATCH"] if compiled.rule_type=="numeric_crosscheck" else
                    ["INSUFFICIENT_JUSTIFICATION"],
                    normative_context
                )
            else:
                practice_context={}
            public_recipe={
                key:(recipe or {}).get(key) for key in (
                    'recipe_id','recipe_status','check_method','verification_level',
                    'expected_sections','required_modality','specialized_checker_id',
                    'categorical_verdict_allowed','retrieval_only',
                ) if (recipe or {}).get(key) not in (None,'',[],{})
            }
            results.append({**item,'compiled_rule':compiled_dict,'verification_recipe':public_recipe,'recipe_id':(recipe or {}).get('recipe_id'),'recipe_status':(recipe or {}).get('recipe_status','EXPERIMENTAL'),'recipe_quality':(recipe or {}).get('critic_score',0),'proof_kind':proof_kind,'typed_check':compiled.typed_check,'execution_class':compiled.automation_class,'required_evidence_types':list(compiled.evidence_types),'automatic_verdict_eligible':automatic_verdict_eligible,'automatic_verdict_policy':'SPECIALIZED_DETERMINISTIC_CHECKER' if automatic_verdict_eligible else 'CANDIDATE_EVIDENCE_ONLY','candidate_evidence_only':not automatic_verdict_eligible,'normative_context':normative_context,'expert_practice_context':practice_context,'status':status,'evidence':evidence,'applicable':applicable,'user_decision':'Не рассмотрено','user_comment':''})
        return results

    def evaluate_with_pp87(self, documents: list[dict[str,Any]], comparisons: list[dict[str,Any]], findings: list[dict[str,Any]], *, source_file: str | None = None, section: str | None = None, include_practice: bool = True) -> list[dict[str,Any]]:
        results = self.evaluate(documents, comparisons, findings, source_file=source_file, section=section, include_practice=include_practice)
        if section:
            selected = self._selected_findings(findings, documents, section)
            results.extend(evaluate_pp87(section, selected))
        return results

    def summary(self, results: Iterable[dict[str,Any]]):
        results=list(results)
        return {
            'total':sum(1 for x in results if x['status']!='Раздел'),
            'yes':sum(1 for x in results if x['status']=='Да'),
            'no':sum(1 for x in results if x['status']=='Нет'),
            'review':sum(1 for x in results if x['status']=='Требует проверки'),
            'no_data':sum(1 for x in results if x['status']=='Нет данных'),
            'unsupported':sum(1 for x in results if x['status']=='Не проверено системой'),
        }
