from __future__ import annotations
import io
import json
import math
import re
from datetime import datetime, date
import pandas as pd
from core.ru_labels import ru_label, ru_join
from core.display_localization import parameter_label, status_label, scope_label, header_label, localize_service_value
from core.report_engine import build_decision_report, build_structured_report
from core.evidence_registry import build_evidence_index
from core.object_intelligence import build_object_decisions
from core.project_assembly import (
    build_assembly_rows, filter_comparisons_by_keys, filter_passports_by_keys,
    filter_registry_by_keys, selected_keys,
)


def frames(result):
    if not result: return pd.DataFrame(),pd.DataFrame(),pd.DataFrame()
    d,f,c=result; return pd.DataFrame(d),pd.DataFrame(f),pd.DataFrame(c)

def status_group(value: str) -> str:
    t=str(value or '').upper()
    if 'РАСХОЖД' in t or 'КОНФЛИКТ' in t:return 'bad'
    if 'УТОЧ' in t or 'НЕДОСТАТОЧ' in t or 'НЕ ПРОВЕРЕНО' in t:return 'warn'
    if 'СОВПАД' in t or 'ПОДТВЕРЖ' in t:return 'ok'
    return 'info'

def metrics(df):
    if df.empty or 'status' not in df:return {'total':0,'ok':0,'warn':0,'bad':0}
    g=df['status'].map(status_group);return {'total':len(df),'ok':int(g.eq('ok').sum()),'warn':int(g.eq('warn').sum()),'bad':int(g.eq('bad').sum())}

def engineer_findings(df):
    if df.empty:return df.copy()
    excluded={'PROJECT_NAME','PROJECT_CODE','PROJECT_YEAR','ISSUE_AUTHOR','CHIEF_ENGINEER','SIGNER','DOCUMENT_CODE','DOCUMENT_YEAR','XML_SCHEMA','FILE_NAME','FILE_CHECKSUM','OBJECT_ENTRY','OBJECT_CANDIDATE'}
    out=df.copy()
    if 'parameter_code' in out:out=out[~out['parameter_code'].fillna('').astype(str).isin(excluded)]
    return out

def composition_baseline(docs):
    if docs.empty or 'composition_baseline' not in docs:return pd.DataFrame()
    return pd.DataFrame(docs.iloc[0].get('composition_baseline') or [])

def raw_registry(docs):
    if docs.empty:return pd.DataFrame()
    # Structured project composition is the fail-safe engineer-facing registry.
    # If present, it cannot be replaced by generic narrative extraction results.
    base = composition_baseline(docs)
    if not base.empty:
        consolidated = pd.DataFrame(docs.iloc[0].get('consolidated_registry') or [])
        if not consolidated.empty and 'Позиция по ГП' in consolidated.columns:
            extra_cols=[c for c in consolidated.columns if c not in base.columns]
            if extra_cols:
                enrich=consolidated[['Позиция по ГП']+extra_cols].drop_duplicates('Позиция по ГП')
                base=base.merge(enrich,on='Позиция по ГП',how='left')
        return base
    if 'consolidated_registry' not in docs:return pd.DataFrame()
    return pd.DataFrame(docs.iloc[0].get('consolidated_registry') or [])

def raw_candidates(docs):
    if docs.empty or 'consolidated_candidates' not in docs:return pd.DataFrame()
    return pd.DataFrame(docs.iloc[0].get('consolidated_candidates') or [])

def raw_passports(docs):
    if docs.empty or 'object_passports' not in docs:return []
    return docs.iloc[0].get('object_passports') or []

def assembly_rows(docs, findings=None):
    finding_rows=(findings.to_dict('records') if hasattr(findings,'to_dict') else findings) or []
    evidence_index=build_evidence_index(finding_rows)
    intelligence=build_object_decisions(finding_rows)
    trusted=raw_registry(docs).to_dict('records')
    # With an explicit composition baseline, generic text candidates belong only
    # to developer diagnostics. The primary table must show the actual project
    # composition, not sentences, TEP labels or section headings.
    candidates=[] if not composition_baseline(docs).empty else raw_candidates(docs).to_dict('records')
    return build_assembly_rows(trusted, candidates, evidence_index, intelligence)

def apply_project_assembly(docs, passports, comparisons, state_rows, confirmed):
    if not confirmed:
        return pd.DataFrame(), [], pd.DataFrame()
    allowed=selected_keys(state_rows)
    reg=pd.DataFrame(filter_registry_by_keys(raw_registry(docs).to_dict('records'),allowed))
    pas=filter_passports_by_keys(passports,allowed)
    cmp=pd.DataFrame(filter_comparisons_by_keys(comparisons.to_dict('records'),state_rows,allowed))
    return reg,pas,cmp

def registry(docs): return raw_registry(docs)
def passports(docs): return raw_passports(docs)

_ILLEGAL_XML_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
_EXCEL_MAX_TEXT = 32000


def _excel_safe_value(value):
    """Convert arbitrary diagnostic values to valid, compact XLSX cell values."""
    if value is None:
        return ''
    if isinstance(value, float):
        return '' if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, (int, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value
    if isinstance(value, (dict, list, tuple, set)):
        try:
            value = json.dumps(value, ensure_ascii=False, default=str, separators=(',', ': '))
        except Exception:
            value = str(value)
    text = _ILLEGAL_XML_CHARS.sub('', str(value)).replace('\x00', '').strip()
    # Do not allow project text to be interpreted as an Excel formula.
    if text.startswith(('=', '+', '-', '@')):
        text = "'" + text
    return text[:_EXCEL_MAX_TEXT]


def _excel_safe_frame(frame: pd.DataFrame, *, columns: list[str] | None = None, max_rows: int | None = None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=columns or [])
    result = frame.copy()
    if columns is not None:
        available = [column for column in columns if column in result.columns]
        result = result[available]
    if max_rows is not None:
        result = result.head(max_rows)
    result.columns = [_excel_safe_value(column) for column in result.columns]
    for column in result.columns:
        result[column] = result[column].map(_excel_safe_value)
    return result


def _compact_technical_frames(docs, findings, comparisons, report):
    registry_columns = [
        'Позиция по ГП','Наименование объекта','Статус проектирования','Статус',
        'Источники','Страницы','Уверенность','Решение инспектора','Причины решения',
    ]
    comparison_columns = [
        'check_id','object','parameter','status','priority','values_by_section',
        'explanation','sources','genplan_position','strong_evidence_count',
    ]
    document_columns = [
        'document','document_type','page_count','size_mb','status','completeness_status',
        'processing_error','document_profile',
    ]
    finding_columns = [
        'document','document_type','page','section_title','table_title','table_row',
        'parameter_code','parameter_name','object_hint','genplan_position','value_text',
        'unit','confidence','binding_status','match_method','structural_zone',
    ]
    object_columns = [
        'Ключ','Позиция по ГП','Наименование объекта','Статус проектирования',
        'Основание включения','Блокировка','Решение пользователя','Комментарий пользователя',
    ]
    return {
        'Тех_реестр': _excel_safe_frame(registry(docs), columns=registry_columns, max_rows=5000),
        'Тех_сверки': _excel_safe_frame(comparisons, columns=comparison_columns, max_rows=10000),
        'Тех_документы': _excel_safe_frame(docs, columns=document_columns, max_rows=3000),
        'Тех_извлечение': _excel_safe_frame(engineer_findings(findings), columns=finding_columns, max_rows=10000),
        'Тех_исключённые': _excel_safe_frame(pd.DataFrame(report.get('excluded_objects') or []), columns=object_columns, max_rows=5000),
        'Тех_спорные': _excel_safe_frame(pd.DataFrame(report.get('unresolved_objects') or []), columns=object_columns, max_rows=5000),
    }


def _safe_sheet_name(name: str) -> str:
    for ch in '[]:*?/\\':
        name = name.replace(ch, '_')
    return (name or 'Лист')[:31]


def _style_workbook(book, report_kind: str = 'gip'):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    dark = '1F4E78'
    blue = 'D9EAF7'
    light = 'F3F6F9'
    green = 'E2F0D9'
    yellow = 'FFF2CC'
    red = 'FCE4D6'
    gray = 'E7E6E6'
    thin = Side(style='thin', color='B8C2CC')

    for ws in book.worksheets:
        ws.sheet_view.showGridLines = False
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        ws.row_dimensions[1].height = 30
        for cell in ws[1]:
            cell.fill = PatternFill('solid', fgColor=dark)
            cell.font = Font(color='FFFFFF', bold=True, size=11)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = Border(bottom=thin)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                cell.border = Border(bottom=thin)
                value = str(cell.value or '').lower()
                if 'высок' in value or 'расхожд' in value or value == 'нет':
                    cell.fill = PatternFill('solid', fgColor=red)
                elif 'средн' in value or 'требует' in value or 'частично' in value or 'недостат' in value:
                    cell.fill = PatternFill('solid', fgColor=yellow)
                elif 'подтверж' in value or 'совпад' in value or value == 'да':
                    cell.fill = PatternFill('solid', fgColor=green)
        for idx, cells in enumerate(ws.columns, 1):
            values = [str(c.value or '') for c in cells[:120]]
            width = min(max(max((len(v) for v in values), default=0) + 2, 12), 52)
            ws.column_dimensions[get_column_letter(idx)].width = width
        ws.auto_filter.ref = ws.dimensions

    if 'Резюме' in book.sheetnames:
        ws = book['Резюме']
        ws.freeze_panes = None
        ws.auto_filter.ref = None
        ws.column_dimensions['A'].width = 34
        ws.column_dimensions['B'].width = 68
        for row in range(2, ws.max_row + 1):
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'A{row}'].fill = PatternFill('solid', fgColor=blue)
            ws[f'B{row}'].fill = PatternFill('solid', fgColor=light)
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0


def _report_context(project, docs, comparisons, risks=None, checklist_results=None, assembly_rows_data=None):
    return build_structured_report(
        project,
        docs.to_dict('records') if hasattr(docs, 'to_dict') else (docs or []),
        comparisons.to_dict('records') if hasattr(comparisons, 'to_dict') else (comparisons or []),
        risks=risks or [],
        checklist_results=checklist_results or [],
        assembly_rows=assembly_rows_data or [],
    )


def structured_excel_report(project, version, docs, findings, comparisons, *, report_kind='gip', risks=None, checklist_results=None, assembly_rows_data=None):
    report = _report_context(project, docs, comparisons, risks, checklist_results, assembly_rows_data)
    summary = report['summary']
    out = io.BytesIO()

    # Normative validity is attached to every document by the pipeline; use the first
    # project record as the shared audit payload to avoid duplicating rows.
    normative_rows=[]
    normative_reference_details=[]
    assignment_rows=[]
    assignment_summary={}
    normative_requirement_rows=[]
    normative_compliance_rows=[]
    normative_compliance_summary={}
    project_understanding={}
    project_understanding_quality={}
    if hasattr(docs,'empty') and not docs.empty:
        first_doc=docs.iloc[0].to_dict()
        normative_reference_details=list(first_doc.get('normative_validity_audit') or [])
        normative_rows=list(first_doc.get('normative_reference_summary') or normative_reference_details)
        assignment_rows=list(first_doc.get('assignment_compliance') or [])
        assignment_summary=dict(first_doc.get('assignment_compliance_summary') or {})
        normative_requirement_rows=list(first_doc.get('normative_requirement_audit') or [])
        normative_compliance_rows=list(first_doc.get('normative_compliance_audit') or [])
        normative_compliance_summary=dict(first_doc.get('normative_compliance_summary') or {})
        project_understanding=dict(first_doc.get('project_understanding') or {})
        project_understanding_quality=dict(first_doc.get('project_understanding_quality') or {})
    elif isinstance(docs,list) and docs:
        normative_reference_details=list((docs[0] or {}).get('normative_validity_audit') or [])
        normative_rows=list((docs[0] or {}).get('normative_reference_summary') or normative_reference_details)
        assignment_rows=list((docs[0] or {}).get('assignment_compliance') or [])
        assignment_summary=dict((docs[0] or {}).get('assignment_compliance_summary') or {})
        normative_requirement_rows=list((docs[0] or {}).get('normative_requirement_audit') or [])
        normative_compliance_rows=list((docs[0] or {}).get('normative_compliance_audit') or [])
        normative_compliance_summary=dict((docs[0] or {}).get('normative_compliance_summary') or {})
        project_understanding=dict((docs[0] or {}).get('project_understanding') or {})
        project_understanding_quality=dict((docs[0] or {}).get('project_understanding_quality') or {})
    normative_statuses={}
    for row in normative_rows:
        status=str(row.get('status') or 'Требует верификации')
        normative_statuses[status]=normative_statuses.get(status,0)+1
    normative_attention=sum(v for k,v in normative_statuses.items() if k not in {'Действует','Действует с изменениями'})
    normative_high=sum(1 for x in normative_rows if x.get('status') in {'Заменён','Утратил силу'} and x.get('impact_risk')=='Высокий')

    summary_rows = [
        ['Наименование проекта', project],
        ['Дата и время проверки', datetime.now().strftime('%d.%m.%Y %H:%M')],
        ['Версия ExpertCheck', version],
        ['Вид отчёта', {'manager':'Резюме руководителя','gip':'Отчёт ГИПа','technical':'Техническое приложение'}.get(report_kind, report_kind)],
        ['Комплектность', summary['completeness']],
        ['Загружено документов', summary['documents']],
        ['Подтверждено объектов', summary['objects']],
        ['Проверено характеристик', summary['checks']],
        ['Результатов, требующих внимания', summary['requires_attention']],
        ['Рисков высокого уровня', summary['risks_high']],
        ['Рисков среднего уровня', summary['risks_medium']],
        ['Рассмотрено пунктов чек-листов', summary['checklist_total']],
        ['Уникальных НТД в проекте', len(normative_rows)],
        ['Упоминаний НТД проанализировано', len(normative_reference_details)],
        ['НТД действуют / с изменениями', normative_statuses.get('Действует',0)+normative_statuses.get('Действует с изменениями',0)],
        ['НТД требуют внимания', normative_attention],
        ['Подтверждённых проблем актуальности НТД высокого влияния', normative_high],
        ['Требований Задания проверено', assignment_summary.get('total',len(assignment_rows))],
        ['Соответствуют Заданию', assignment_summary.get('compliant',0)],
        ['Отклонений от Задания', assignment_summary.get('deviation',0)],
        ['Требования Задания требуют проверки', assignment_summary.get('unconfirmed',0)+assignment_summary.get('semantic',0)],
        ['Требования Задания не проверены системой', assignment_summary.get('not_checked',0)],
        ['Структурированных требований НТД в базе', normative_compliance_summary.get('requirements',0)],
        ['Верифицированных пунктов НТД', normative_compliance_summary.get('verified_clause',0)],
        ['Покрытие НТД верифицированными пунктами, %', normative_compliance_summary.get('verified_coverage_pct',0)],
        ['НТД готовы к проверке по доказательствам, %', normative_compliance_summary.get('review_ready_pct',0)],
        ['Структурированность требований Задания, %', assignment_summary.get('structured_requirement_pct',0)],
        ['Автоматическое покрытие Задания, %', assignment_summary.get('automatic_coverage_pct',0)],
        ['Объектов в модели проекта', project_understanding_quality.get('objects',0)],
        ['Объектов с привязанными показателями', project_understanding_quality.get('objects_with_properties',0)],
        ['Неразрешённых привязок объект–показатель', project_understanding_quality.get('unresolved_properties',0)],
        ['Качество объектно-параметрической привязки, %', project_understanding_quality.get('binding_precision_proxy_pct',0)],
        ['Итоговый вывод', report['conclusion']],
    ]

    selected_risks = [r for r in report['risks'] if r.get('level') in ({'Высокий','Средний'} if report_kind != 'technical' else {'Высокий','Средний','Низкий'})]
    if report_kind == 'manager': selected_risks = selected_risks[:12]
    elif report_kind == 'gip': selected_risks = selected_risks[:30]
    risks_df = pd.DataFrame([{
        'ID': r.get('risk_id'),
        'Уровень': r.get('level'),
        'Категория': r.get('category'),
        'Объект / раздел': r.get('object') or '—',
        'Вопрос': r.get('parameter'),
        'Выявленная проблема': r.get('finding'),
        'Возможное замечание': r.get('possible_remark'),
        'Рекомендуемое действие': r.get('recommendation'),
        'Источники': r.get('sources'),
        'Сценарий базы': r.get('scenario_id'),
        'Повторяемость': r.get('recurrence'),
        'Проекты-аналоги': ', '.join(r.get('analog_projects') or []),
        'Решение пользователя': r.get('user_status') or 'Не рассмотрено',
        'Комментарий пользователя': r.get('user_comment') or '',
    } for r in selected_risks])

    selected_problems = report['problems'] if report_kind == 'technical' else report['problems'][:(12 if report_kind == 'manager' else 35)]
    problems_df = pd.DataFrame(selected_problems).rename(columns={
        'id':'ID', 'object':'Объект', 'parameter':'Показатель', 'status':'Результат',
        'priority':'Приоритет', 'values':'Значения по разделам', 'explanation':'Пояснение', 'sources':'Источники',
    })
    object_df = pd.DataFrame(report['confirmed_objects']).rename(columns={
        'position':'Поз.', 'name':'Наименование объекта', 'status':'Статус', 'source':'Основной источник',
    })
    checklist_problem_df = pd.DataFrame([{
        'Раздел': r.get('automatic_section') or r.get('section') or r.get('Раздел') or 'Не определён',
        'Чек-лист': r.get('automatic_checklist') or r.get('source_file') or r.get('Чек-лист') or '',
        'Пункт': f"{r.get('item_no') or r.get('position') or ''} — {r.get('question') or r.get('Позиция по чек-листу') or ''}".strip(' —'),
        'Результат': r.get('status') or r.get('Соответствие') or r.get('result'),
        'Обоснование': r.get('evidence') or r.get('Обоснование') or '',
        'Источники': r.get('sources') or r.get('Источники') or '',
    } for r in report['checklist_results'] if str(r.get('status') or r.get('Соответствие') or r.get('result') or '').lower() in {'нет','частично','требует проверки','нет данных','не соответствует'}])
    recommendations_df = pd.DataFrame({'Приоритетное действие': report['recommendations'] or ['Дополнительные рекомендации не сформированы.']})
    understanding_rows=[]
    for obj in project_understanding.get('objects') or []:
        for prop in obj.get('property_summary') or []:
            understanding_rows.append({
              'ID объекта':obj.get('object_id'),'Объект':obj.get('name'),'Позиция по ГП':obj.get('position') or '—',
              'Тип объекта':obj.get('object_type'),'Показатель':prop.get('parameter_name'),
              'Код показателя':parameter_label(prop.get('parameter_code')),'Разделы':', '.join(prop.get('sections') or []),
              'Количество доказательств':prop.get('evidence_count',0),
              'Профильный источник':'Да' if prop.get('owner_evidence') else 'Нет',
              'Конфликт значений':'Да' if prop.get('value_conflict') else 'Нет',
              'Значения':' | '.join(str(x) for x in prop.get('values') or []),
            })
    understanding_df=pd.DataFrame(understanding_rows)

    assignment_df = pd.DataFrame([{
        'ID требования':x.get('requirement_id'),
        'Строка Задания':x.get('source_row') or '—',
        'Раздел / вопрос Задания':x.get('source_row_title') or '—',
        'Тип проверки':ru_label(x.get('requirement_type')),
        'Область требования':ru_label(x.get('requirement_scope') or (x.get('evidence_contract_v2') or {}).get('scope')),
        'Метод проверки':ru_label((x.get('evidence_contract_v2') or {}).get('check_method')),
        'Ожидаемые разделы':', '.join((x.get('evidence_contract_v2') or {}).get('expected_sections') or []),
        'Способ восстановления':ru_label(x.get('cell_reconstruction')),
        'Требование Задания':x.get('requirement_text'),
        'Объект':x.get('object_name') or '—',
        'Показатель':parameter_label(x.get('parameter_code')) if x.get('parameter_code') else '—',
        'Требуемое значение':x.get('required_value'),
        'Ед. изм.':x.get('unit'),
        'Результат':x.get('status'),
        'Документ':x.get('source_document'),
        'Страница':x.get('page'),
        'Доказательства':' | '.join(x.get('evidence') or []),
        'Качество доказательства':ru_label(x.get('evidence_quality_state')),
        'Направленных кандидатов':len(x.get('directed_evidence_candidates') or []),
        'Ожидаемое доказательство':x.get('expected_evidence') or '',
        'Основание вывода':x.get('decision_basis') or '',
        'Рекомендация':x.get('recommendation'),
    } for x in assignment_rows])

    normative_requirement_df = pd.DataFrame([{
        'НТД':x.get('reference'),
        'Пункт / статья':x.get('clause') or '—',
        'Тип требования':x.get('modality'),
        'Тип проверки':ru_label(x.get('check_kind')) or '—',
        'Качество нормативного основания':x.get('requirement_quality') or '—',
        'Контекст в проекте':x.get('project_context'),
        'Статус НТД':x.get('normative_status'),
        'Статус редакции':x.get('edition_status'),
        'Структурированное требование':x.get('curated_requirement') or 'Не загружено',
        'Статус анализа требования':x.get('analysis_status'),
        'Файл':x.get('document'),
        'Страница':x.get('page'),
        'Риск влияния':x.get('impact_risk'),
    } for x in normative_requirement_rows])

    normative_df = pd.DataFrame([{
        'НТД':x.get('reference'),
        'Статус':x.get('status'),
        'Статус редакции':(x.get('edition_assessment') or {}).get('edition_status',''),
        'Актуальная редакция / замена':(x.get('edition_assessment') or {}).get('current_reference','') or x.get('replacement',''),
        'Количество упоминаний':x.get('mentions',1),
        'Документов':x.get('documents_count',1 if x.get('document') else 0),
        'Где встречается':'; '.join(x.get('pages') or []) if isinstance(x.get('pages'),list) else f"{x.get('document') or ''}, стр. {x.get('page') or ''}",
        'Риск влияния':x.get('impact_risk') if x.get('coverage_status')!='Требует наполнения KB' else 'Не оценивается — пробел KB',
        'Покрытие ExpertCheck':x.get('coverage_status') or '—',
        'Приоритет базы':x.get('verification_priority'),
        'Дата проверки':x.get('verified_on') or x.get('last_verified_at') or '',
        'Источник проверки':x.get('official_source'),
    } for x in normative_rows])

    summary_df = _excel_safe_frame(pd.DataFrame(summary_rows, columns=['Показатель', 'Значение']))
    risks_df = _excel_safe_frame(risks_df)
    problems_df = _excel_safe_frame(problems_df)
    object_df = _excel_safe_frame(object_df)
    checklist_problem_df = _excel_safe_frame(checklist_problem_df)
    recommendations_df = _excel_safe_frame(recommendations_df)

    normative_compliance_df = pd.DataFrame([{
        'ID требования':x.get('requirement_id'),
        'Тип знания':ru_label(x.get('knowledge_kind') or 'LAW_REQUIREMENT'),
        'НТД':x.get('source'),
        'Пункт / статья':x.get('paragraph') or '—',
        'Тема':x.get('topic'),
        'Требование':x.get('requirement'),
        'Тип проверки':ru_label(x.get('check_kind')),
        'Пункт верифицирован':'Да' if x.get('verified_clause') else 'Нет',
        'Готово для AI-review':'Да' if x.get('ai_review_ready') else 'Нет',
        'Результат':x.get('status'),
        'Покрытие':ru_label(x.get('coverage_state')),
        'Основание вывода':x.get('decision_basis'),
        'Доказательства':' | '.join(f"{e.get('document')}, стр. {e.get('page')}: {e.get('context') or e.get('value') or ''}" for e in (x.get('evidence') or [])[:5]),
    } for x in normative_compliance_rows])
    normative_df = _excel_safe_frame(normative_df)
    assignment_df = _excel_safe_frame(assignment_df)
    understanding_df = _excel_safe_frame(understanding_df)
    normative_requirement_df = _excel_safe_frame(normative_requirement_df)
    normative_compliance_df = _excel_safe_frame(normative_compliance_df)

    sheets: list[tuple[str, pd.DataFrame]] = [('Резюме', summary_df)]
    if not risks_df.empty:
        sheets.append(('Ключевые риски', risks_df))
    if not problems_df.empty:
        sheets.append(('Межраздельные вопросы', problems_df))
    # Состав проекта в стандартном отчёте не дублируется: только в техническом приложении.
    if report_kind == 'technical' and not object_df.empty:
        sheets.append(('Состав проекта', object_df))
    if report_kind != 'manager' and not checklist_problem_df.empty:
        checklist_problem_df=checklist_problem_df.sort_values(['Раздел','Чек-лист','Пункт'],kind='stable')
        sheets.append(('Чек-листы — сводка', checklist_problem_df))
        # One compact sheet per section: the user immediately sees which requirement belongs where.
        for section_name, section_frame in checklist_problem_df.groupby('Раздел',dropna=False):
            safe_section=str(section_name or 'Не определён')
            sheets.append((_safe_sheet_name('ЧЛ '+safe_section), section_frame.reset_index(drop=True)))
    if report_kind == 'manager' and not normative_df.empty:
        attention_norm=normative_df[normative_df['Статус'].isin(['Заменён','Утратил силу'])].head(12)
        if not attention_norm.empty:
            sheets.append(('НТД — внимание', attention_norm))
    elif report_kind in {'gip','technical'} and not normative_df.empty:
        sheets.append(('Актуальность НТД', normative_df if report_kind=='technical' else normative_df.head(80)))
    if report_kind in {'gip','technical'} and not normative_compliance_df.empty:
        sheets.append(('Проверка требований НТД', normative_compliance_df if report_kind=='technical' else normative_compliance_df.head(100)))
    if report_kind == 'technical' and not normative_requirement_df.empty:
        sheets.append(('Контекст ссылок НТД', normative_requirement_df))
    if report_kind in {'gip','technical'} and not understanding_df.empty:
        sheets.append(('Модель проекта', understanding_df if report_kind=='technical' else understanding_df.head(150)))
    if report_kind == 'manager' and not assignment_df.empty:
        assignment_attention=assignment_df[assignment_df['Результат'].isin(['Выявлено отклонение','Требование не подтверждено','Требуется смысловая проверка'])].head(12)
        if not assignment_attention.empty:
            sheets.append(('Задание — внимание',assignment_attention))
    elif report_kind in {'gip','technical'} and not assignment_df.empty:
        sheets.append(('Задание на проектирование',assignment_df))
    sheets.append(('План действий', recommendations_df))
    if report_kind == 'technical' and normative_reference_details:
        detailed_normative_df=pd.DataFrame(normative_reference_details)
        if not detailed_normative_df.empty:
            sheets.append(('НТД — все упоминания', _excel_safe_frame(detailed_normative_df)))
    if report_kind == 'technical':
        for sheet_name, frame in _compact_technical_frames(docs, findings, comparisons, report).items():
            if not frame.empty:
                sheets.append((_safe_sheet_name(sheet_name), frame))


    header_ru = {
      "document":"Документ","document_type":"Тип документа","page":"Страница","parameter_code":"Код показателя",
      "parameter_name":"Показатель","object":"Объект","object_id":"ID объекта","object_hint":"Объект",
      "value":"Значение","value_text":"Исходное значение","unit":"Ед. изм.","status":"Статус",
      "category":"Категория","finding":"Выявленная проблема","recommendation":"Рекомендация",
      "sources":"Источники","source":"Источник","confidence":"Достоверность","reason":"Обоснование",
      "section":"Раздел","section_family":"Раздел","checklist":"Чек-лист","question":"Проверка",
      "result":"Результат","priority":"Приоритет","risk_score":"Оценка риска","risk_level":"Уровень риска",
      "genplan_position":"Позиция по ГП","comparison_scope":"Контур сравнения","binding_key":"Ключ привязки",
      "project":"Проект","project_name":"Проект","analysis_time":"Дата проверки","core_version":"Версия ядра",
      "requirement_id":"ID требования","requirement_text":"Требование","required_value":"Требуемое значение",
      "automatic_section":"Раздел","automatic_checklist":"Чек-лист","execution_class":"Тип проверки",
      "table_title":"Наименование таблицы","table_row":"Строка таблицы","explanation":"Пояснение",
      "reference":"Ссылка/обозначение","canonical_id":"Канонический ID","verified_on":"Дата верификации",
      "verified_revision":"Верифицированная редакция","replacement":"Заменяющий документ",
      "effective_until":"Действует до","official_source":"Официальный источник","official_source_kind":"Тип официального источника",
      "impact_risk":"Оценка влияния","cell_reconstruction":"Способ восстановления требования",
      "evidence_quality_state":"Качество доказательства","requirement_scope":"Область требования",
      "requirement_type":"Тип требования","finding_type":"Тип результата","promotion_method":"Способ подтверждения",
      "semantic_evidence_score":"Смысловая достоверность",
    }
    normalized_sheets=[]
    for sheet_name,frame in sheets:
        if isinstance(frame,pd.DataFrame):
            frame=frame.rename(columns={c:header_ru.get(str(c),header_label(c)) for c in frame.columns})
            for col in frame.columns:
                if frame[col].dtype == object:
                    frame[col]=frame[col].map(localize_service_value)
        normalized_sheets.append((sheet_name,frame))
    sheets=normalized_sheets

    # XlsxWriter creates a clean OOXML package and avoids repair messages that
    # Excel can show for workbooks containing complex openpyxl metadata.
    with pd.ExcelWriter(
        out,
        engine='xlsxwriter',
        engine_kwargs={'options': {
            'strings_to_formulas': False,
            'strings_to_urls': False,
            'nan_inf_to_errors': False,
        }},
    ) as writer:
        workbook = writer.book
        workbook.set_properties({
            'title': f'ExpertCheck — {project}',
            'subject': 'Автоматизированная проверка проектной документации',
            'author': 'ExpertCheck',
            'company': 'ExpertCheck',
        })
        header_fmt = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#1F4E78',
            'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
            'border': 1, 'border_color': '#B8C2CC',
        })
        body_fmt = workbook.add_format({
            'valign': 'top', 'text_wrap': True,
            'bottom': 1, 'bottom_color': '#D9E0E6',
        })
        label_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#D9EAF7', 'valign': 'top',
            'text_wrap': True, 'border': 1, 'border_color': '#D9E0E6',
        })
        value_fmt = workbook.add_format({
            'bg_color': '#F3F6F9', 'valign': 'top', 'text_wrap': True,
            'border': 1, 'border_color': '#D9E0E6',
        })
        bad_fmt = workbook.add_format({'bg_color': '#FCE4D6'})
        warn_fmt = workbook.add_format({'bg_color': '#FFF2CC'})
        ok_fmt = workbook.add_format({'bg_color': '#E2F0D9'})

        used_names: set[str] = set()
        for raw_name, frame in sheets:
            name = _safe_sheet_name(raw_name)
            base = name
            suffix = 2
            while name in used_names:
                tail = f'_{suffix}'
                name = (base[:31-len(tail)] + tail)
                suffix += 1
            used_names.add(name)
            safe_frame = _excel_safe_frame(frame)
            safe_frame.to_excel(writer, sheet_name=name, index=False)
            worksheet = writer.sheets[name]
            worksheet.hide_gridlines(2)
            worksheet.set_row(0, 30, header_fmt)
            if name == 'Резюме':
                worksheet.set_column(0, 0, 34, label_fmt)
                worksheet.set_column(1, 1, 68, value_fmt)
                worksheet.set_landscape()
                worksheet.fit_to_pages(1, 0)
            else:
                worksheet.freeze_panes(1, 0)
                if len(safe_frame.columns):
                    worksheet.autofilter(0, 0, max(len(safe_frame), 1), len(safe_frame.columns)-1)
                for col_idx, column in enumerate(safe_frame.columns):
                    values = [str(column)] + [str(v or '') for v in safe_frame[column].head(120)]
                    width = min(max(max((len(v) for v in values), default=0) + 2, 12), 52)
                    worksheet.set_column(col_idx, col_idx, width, body_fmt)
                # Lightweight conditional highlighting without formulas.
                if len(safe_frame) and len(safe_frame.columns):
                    last_row = len(safe_frame)
                    last_col = len(safe_frame.columns)-1
                    worksheet.conditional_format(1, 0, last_row, last_col, {
                        'type': 'text', 'criteria': 'containing', 'value': 'Высокий', 'format': bad_fmt})
                    worksheet.conditional_format(1, 0, last_row, last_col, {
                        'type': 'text', 'criteria': 'containing', 'value': 'Расхождение', 'format': bad_fmt})
                    worksheet.conditional_format(1, 0, last_row, last_col, {
                        'type': 'text', 'criteria': 'containing', 'value': 'Требует', 'format': warn_fmt})
                    worksheet.conditional_format(1, 0, last_row, last_col, {
                        'type': 'text', 'criteria': 'containing', 'value': 'Средний', 'format': warn_fmt})
                    worksheet.conditional_format(1, 0, last_row, last_col, {
                        'type': 'text', 'criteria': 'containing', 'value': 'Совпадает', 'format': ok_fmt})
                    worksheet.conditional_format(1, 0, last_row, last_col, {
                        'type': 'text', 'criteria': 'containing', 'value': 'Подтвержден', 'format': ok_fmt})

    payload = out.getvalue()
    if not payload.startswith(b'PK'):
        raise ValueError('Не удалось сформировать корректный XLSX-файл.')

    # Full OOXML and workbook round-trip validation before download.
    import zipfile
    from openpyxl import load_workbook
    buffer = io.BytesIO(payload)
    with zipfile.ZipFile(buffer) as archive:
        broken = archive.testzip()
        if broken is not None:
            raise ValueError(f'Повреждён элемент XLSX: {broken}')
    buffer.seek(0)
    check_book = load_workbook(buffer, read_only=True, data_only=False)
    check_book.close()
    return payload


def excel_report(project, version, docs, findings, comparisons):
    """Backward-compatible default: compact GIP report."""
    return structured_excel_report(project, version, docs, findings, comparisons, report_kind='gip')
