from __future__ import annotations
import io
import json
import math
import re
from datetime import datetime, date
import pandas as pd
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

def raw_registry(docs):
    if docs.empty or 'consolidated_registry' not in docs:return pd.DataFrame()
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
    return build_assembly_rows(raw_registry(docs).to_dict('records'), raw_candidates(docs).to_dict('records'), evidence_index, intelligence)

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
        ['Итоговый вывод', report['conclusion']],
    ]

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
    } for r in report['risks'] if r.get('level') in ({'Высокий','Средний'} if report_kind != 'technical' else {'Высокий','Средний','Низкий'})])

    problems_df = pd.DataFrame(report['problems']).rename(columns={
        'id':'ID', 'object':'Объект', 'parameter':'Показатель', 'status':'Результат',
        'priority':'Приоритет', 'values':'Значения по разделам', 'explanation':'Пояснение', 'sources':'Источники',
    })
    object_df = pd.DataFrame(report['confirmed_objects']).rename(columns={
        'position':'Поз.', 'name':'Наименование объекта', 'status':'Статус', 'source':'Основной источник',
    })
    checklist_problem_df = pd.DataFrame([{
        'Пункт': f"{r.get('item_no') or r.get('position') or ''} — {r.get('question') or r.get('Позиция по чек-листу') or ''}".strip(' —'),
        'Результат': r.get('status') or r.get('Соответствие') or r.get('result'),
        'Обоснование': r.get('evidence') or r.get('Обоснование') or '',
        'Источники': r.get('sources') or r.get('Источники') or '',
    } for r in report['checklist_results'] if str(r.get('status') or r.get('Соответствие') or r.get('result') or '').lower() in {'нет','частично','требует проверки','нет данных','не соответствует'}])
    recommendations_df = pd.DataFrame({'Приоритетное действие': report['recommendations'] or ['Дополнительные рекомендации не сформированы.']})

    summary_df = _excel_safe_frame(pd.DataFrame(summary_rows, columns=['Показатель', 'Значение']))
    risks_df = _excel_safe_frame(risks_df)
    problems_df = _excel_safe_frame(problems_df)
    object_df = _excel_safe_frame(object_df)
    checklist_problem_df = _excel_safe_frame(checklist_problem_df)
    recommendations_df = _excel_safe_frame(recommendations_df)

    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Резюме', index=False)
        if not risks_df.empty:
            risks_df.to_excel(writer, sheet_name='Ключевые риски', index=False)
        if not problems_df.empty:
            problems_df.to_excel(writer, sheet_name='Межраздельные вопросы', index=False)
        if report_kind != 'manager' and not object_df.empty:
            object_df.to_excel(writer, sheet_name='Состав проекта', index=False)
        if report_kind != 'manager' and not checklist_problem_df.empty:
            checklist_problem_df.to_excel(writer, sheet_name='Чек-листы — вопросы', index=False)
        recommendations_df.to_excel(writer, sheet_name='План действий', index=False)

        if report_kind == 'technical':
            # Compact technical appendix: only reproducible engineering fields, without
            # raw nested payloads, full page text or internal Python structures.
            for sheet_name, frame in _compact_technical_frames(docs, findings, comparisons, report).items():
                if not frame.empty:
                    frame.to_excel(writer, sheet_name=_safe_sheet_name(sheet_name), index=False)

        _style_workbook(writer.book, report_kind)
        writer.book.properties.title = f'ExpertCheck — {project}'
        writer.book.properties.subject = 'Автоматизированная проверка проектной документации'
        writer.book.properties.creator = 'ExpertCheck'
        writer.book.active = 0
        try:
            writer.book.calculation.fullCalcOnLoad = True
            writer.book.calculation.forceFullCalc = True
        except Exception:
            pass
    payload = out.getvalue()
    # Validate container signature before returning it to Streamlit.
    if not payload.startswith(b'PK'):
        raise ValueError('Не удалось сформировать корректный XLSX-файл.')
    return payload


def excel_report(project, version, docs, findings, comparisons):
    """Backward-compatible default: compact GIP report."""
    return structured_excel_report(project, version, docs, findings, comparisons, report_kind='gip')
