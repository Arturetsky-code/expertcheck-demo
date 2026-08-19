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
    if hasattr(docs,'empty') and not docs.empty:
        first_doc=docs.iloc[0].to_dict()
        normative_rows=list(first_doc.get('normative_validity_audit') or [])
    elif isinstance(docs,list) and docs:
        normative_rows=list((docs[0] or {}).get('normative_validity_audit') or [])
    normative_statuses={}
    for row in normative_rows:
        status=str(row.get('status') or 'Требует верификации')
        normative_statuses[status]=normative_statuses.get(status,0)+1
    normative_attention=sum(v for k,v in normative_statuses.items() if k not in {'Действует','Действует с изменениями'})
    normative_high=sum(1 for x in normative_rows if x.get('impact_risk')=='Высокий' and x.get('status') not in {'Действует','Действует с изменениями'})

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
        ['Нормативных ссылок проверено', len(normative_rows)],
        ['НТД действуют / с изменениями', normative_statuses.get('Действует',0)+normative_statuses.get('Действует с изменениями',0)],
        ['НТД требуют внимания', normative_attention],
        ['Нормативных рисков высокого влияния', normative_high],
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
        'Пункт': f"{r.get('item_no') or r.get('position') or ''} — {r.get('question') or r.get('Позиция по чек-листу') or ''}".strip(' —'),
        'Результат': r.get('status') or r.get('Соответствие') or r.get('result'),
        'Обоснование': r.get('evidence') or r.get('Обоснование') or '',
        'Источники': r.get('sources') or r.get('Источники') or '',
    } for r in report['checklist_results'] if str(r.get('status') or r.get('Соответствие') or r.get('result') or '').lower() in {'нет','частично','требует проверки','нет данных','не соответствует'}])
    recommendations_df = pd.DataFrame({'Приоритетное действие': report['recommendations'] or ['Дополнительные рекомендации не сформированы.']})
    normative_df = pd.DataFrame([{
        'НТД':x.get('reference'),
        'Статус':x.get('status'),
        'Статус редакции':(x.get('edition_assessment') or {}).get('edition_status',''),
        'Актуальная редакция / замена':(x.get('edition_assessment') or {}).get('current_reference','') or x.get('replacement',''),
        'Файл':x.get('document'),
        'Страница':x.get('page'),
        'Риск влияния':x.get('impact_risk'),
        'Приоритет базы':x.get('verification_priority'),
        'Замечаний экспертизы':x.get('expert_occurrences',0),
        'Дата проверки':x.get('verified_on') or x.get('last_verified_at') or '',
        'Источник проверки':x.get('official_source'),
    } for x in normative_rows])

    summary_df = _excel_safe_frame(pd.DataFrame(summary_rows, columns=['Показатель', 'Значение']))
    risks_df = _excel_safe_frame(risks_df)
    problems_df = _excel_safe_frame(problems_df)
    object_df = _excel_safe_frame(object_df)
    checklist_problem_df = _excel_safe_frame(checklist_problem_df)
    recommendations_df = _excel_safe_frame(recommendations_df)
    normative_df = _excel_safe_frame(normative_df)

    sheets: list[tuple[str, pd.DataFrame]] = [('Резюме', summary_df)]
    if not risks_df.empty:
        sheets.append(('Ключевые риски', risks_df))
    if not problems_df.empty:
        sheets.append(('Межраздельные вопросы', problems_df))
    # Состав проекта в стандартном отчёте не дублируется: только в техническом приложении.
    if report_kind == 'technical' and not object_df.empty:
        sheets.append(('Состав проекта', object_df))
    if report_kind != 'manager' and not checklist_problem_df.empty:
        sheets.append(('Чек-листы — вопросы', checklist_problem_df))
    if report_kind == 'manager' and not normative_df.empty:
        attention_norm=normative_df[~normative_df['Статус'].isin(['Действует','Действует с изменениями'])].head(12)
        if not attention_norm.empty:
            sheets.append(('НТД — внимание', attention_norm))
    elif report_kind in {'gip','technical'} and not normative_df.empty:
        sheets.append(('Актуальность НТД', normative_df if report_kind=='technical' else normative_df.head(80)))
    sheets.append(('План действий', recommendations_df))
    if report_kind == 'technical':
        for sheet_name, frame in _compact_technical_frames(docs, findings, comparisons, report).items():
            if not frame.empty:
                sheets.append((_safe_sheet_name(sheet_name), frame))

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
