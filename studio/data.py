from __future__ import annotations
import io
from datetime import datetime
import pandas as pd
from core.report_engine import build_decision_report
from core.evidence_registry import build_evidence_index
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
    evidence_index=build_evidence_index((findings.to_dict('records') if hasattr(findings,'to_dict') else findings) or [])
    return build_assembly_rows(raw_registry(docs).to_dict('records'), raw_candidates(docs).to_dict('records'), evidence_index)

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

def excel_report(project, version, docs, findings, comparisons):
    out=io.BytesIO(); report=build_decision_report(docs.to_dict('records'),comparisons.to_dict('records')); summary=report['summary']
    summary_rows=[['Проект',project],['Версия',version],['Дата проверки',datetime.now().strftime('%d.%m.%Y %H:%M')],['Комплектность',summary['completeness']],['Документов',summary['documents']],['Объектов',summary['objects']],['Проверено характеристик',summary['checks']],['Совпадает',summary['confirmed']],['Требует внимания',summary['requires_attention']],['Высокий приоритет',summary['high_priority']]]
    problems=pd.DataFrame(report['problems']).rename(columns={'object':'Объект','parameter':'Характеристика','status':'Статус','priority':'Приоритет','values':'Значения','explanation':'Пояснение','sources':'Источники'})
    recommendations=pd.DataFrame({'Рекомендация':report['recommendations']})
    with pd.ExcelWriter(out,engine='openpyxl') as w:
        pd.DataFrame(summary_rows,columns=['Показатель','Значение']).to_excel(w,sheet_name='Сводка',index=False); problems.to_excel(w,sheet_name='Требует внимания',index=False); recommendations.to_excel(w,sheet_name='Рекомендации',index=False); registry(docs).to_excel(w,sheet_name='Реестр объектов',index=False); comparisons.to_excel(w,sheet_name='Все сверки',index=False); docs.to_excel(w,sheet_name='Документы',index=False)
        for ws in w.book.worksheets:
            ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
            for cells in ws.columns:
                width=min(max(len(str(c.value or '')) for c in cells)+2,62);ws.column_dimensions[cells[0].column_letter].width=max(12,width)
    return out.getvalue()
