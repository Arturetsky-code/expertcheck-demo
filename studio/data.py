from __future__ import annotations
import io
from datetime import datetime
import pandas as pd

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

def registry(docs):
    if docs.empty or 'consolidated_registry' not in docs:return pd.DataFrame()
    return pd.DataFrame(docs.iloc[0].get('consolidated_registry') or [])

def passports(docs):
    if docs.empty or 'object_passports' not in docs:return []
    return docs.iloc[0].get('object_passports') or []

def excel_report(project, version, docs, findings, comparisons):
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as w:
        pd.DataFrame([['Проект',project],['Версия',version],['Дата проверки',datetime.now().strftime('%d.%m.%Y %H:%M')],['Документов',len(docs)],['Инженерных характеристик',len(engineer_findings(findings))],['Проверок',len(comparisons)]],columns=['Показатель','Значение']).to_excel(w,sheet_name='Сводка',index=False)
        docs.to_excel(w,sheet_name='Документы',index=False);registry(docs).to_excel(w,sheet_name='Реестр объектов',index=False);engineer_findings(findings).to_excel(w,sheet_name='Характеристики',index=False);comparisons.to_excel(w,sheet_name='Сверки',index=False)
        for ws in w.book.worksheets:
            ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
            for cells in ws.columns:
                width=min(max(len(str(c.value or '')) for c in cells)+2,62);ws.column_dimensions[cells[0].column_letter].width=max(12,width)
    return out.getvalue()
