from __future__ import annotations
import streamlit as st
from core.expert_review_engine import build_expert_risks
from core.report_engine import build_structured_report
from studio.components import card,empty,hero,section
from studio.data import structured_excel_report
from core.project_snapshot import project_snapshot_bytes


def _report_documents(docs):
    """Inject user decisions kept in session state into exported snapshots."""
    report_docs = docs.copy()
    if report_docs.empty:
        return report_docs
    report_docs['completeness_user_confirmed'] = bool(st.session_state.get('completeness_user_confirmed'))
    report_docs['object_registry_confirmed'] = bool(st.session_state.get('object_registry_confirmed'))
    report_docs['completeness_decisions'] = [dict(st.session_state.get('completeness_decisions') or {}) for _ in range(len(report_docs))]
    return report_docs


def _checklist_results(first:dict)->list[dict]:
    run=st.session_state.get('checklist_run') or {}
    rows=run.get('results') if isinstance(run,dict) else None
    if isinstance(rows,list):return rows
    return list((first.get('automatic_checklist_review') or {}).get('results') or [])


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero('Отчёт','Короткий рабочий результат без технического шума.','Резюме → несоответствия → контроль соответствия → действия')
    if docs.empty:return empty('Сначала выполните проверку проекта.')
    docs=_report_documents(docs)
    first=docs.iloc[0].to_dict(); checklist=_checklist_results(first)
    assembly=st.session_state.get('object_assembly_rows') or []
    risks=build_expert_risks(comparisons.to_dict('records') if not comparisons.empty else [],assembly,checklist,documents=docs.to_dict('records'))
    report=build_structured_report(st.session_state.project_name,docs.to_dict('records'),comparisons.to_dict('records'),risks=risks,checklist_results=checklist,assembly_rows=assembly)
    plan=first.get('project_review_plan') or {}
    domains=plan.get('domains') or {}
    coverage=first.get('coverage_matrix') or {}
    c1,c2,c3,c4,c5=st.columns(5)
    with c1:card('Несоответствия',report['summary'].get('project_findings',0),'Доказанные выводы','bad' if report['summary'].get('project_findings') else 'ok')
    with c2:card('Строгое покрытие',f"{coverage.get('coverage_pct',0)}%",'Завершено на L5')
    with c3:card('Доказательства',f"{coverage.get('evidence_coverage_pct',0)}%",'Адресные уровни L3–L5')
    with c4:card('Готово для Judge',int((coverage.get('evidence_levels') or {}).get('L4',0)),'Пакеты L4')
    with c5:card('AI-консенсус',coverage.get('semantic_consensus_completed',0),'Независимые Judge + Critic')
    st.info(report['conclusion'])

    section('Скачать отчёт','Основные отчёты сокращены. Полная диагностика доступна только в техническом приложении.')
    cols=st.columns(3)
    with cols[0]:
        card('Резюме руководителя','3–4 листа','Статус проекта, готовность проверки, риски и действия')
        st.download_button('Скачать резюме',data=structured_excel_report(st.session_state.project_name,ctx.version,docs,findings,comparisons,report_kind='manager',risks=risks,checklist_results=checklist,assembly_rows_data=assembly),file_name='ExpertCheck_Резюме_руководителя.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
    with cols[1]:
        card('Отчёт ГИПа','до 6 листов','Резюме, проблемы, Задание, НТД, чек-листы и действия')
        st.download_button('Скачать отчёт ГИПа',data=structured_excel_report(st.session_state.project_name,ctx.version,docs,findings,comparisons,report_kind='gip',risks=risks,checklist_results=checklist,assembly_rows_data=assembly),file_name='ExpertCheck_Отчёт_ГИПа.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
    with cols[2]:
        card('Техническое приложение','Полное','Evidence, извлечение и диагностика')
        st.download_button('Скачать техническое приложение',data=structured_excel_report(st.session_state.project_name,ctx.version,docs,findings,comparisons,report_kind='technical',risks=risks,checklist_results=checklist,assembly_rows_data=assembly),file_name='ExpertCheck_Техническое_приложение.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
    with st.expander('Цифровой снимок для повторной проверки', expanded=False):
        st.caption('Содержит извлечённые страницы, факты, атомарные требования и результаты. Позволяет повторять regression- и AI-проверки без повторного чтения исходных PDF.')
        st.download_button(
            'Скачать цифровой снимок проекта',
            data=project_snapshot_bytes(
                docs.to_dict('records'), findings.to_dict('records'), comparisons.to_dict('records'),
            ),
            file_name='ExpertCheck_Цифровой_снимок.json.gz',
            mime='application/gzip', width='stretch',
        )
