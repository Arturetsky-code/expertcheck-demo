from __future__ import annotations

import pandas as pd
import streamlit as st

from core.expert_review_engine import build_expert_risks
from core.report_engine import build_structured_report
from studio.components import section, empty, card, hero
from studio.data import structured_excel_report


def _checklist_results() -> list[dict]:
    run = st.session_state.get('checklist_run') or {}
    rows = run.get('results') if isinstance(run, dict) else None
    return rows if isinstance(rows, list) else []


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero(
        'Центр отчётов',
        'Три уровня отчётности: краткое резюме для руководителя, рабочий отчёт ГИПа и полное техническое приложение.',
        'Structured Report Center · основной отчёт содержит только вопросы, требующие решения',
    )
    if docs.empty:
        return empty('Сначала выполните проверку проекта.')

    assembly = st.session_state.get('object_assembly_rows') or []
    checklist = _checklist_results()
    risks = build_expert_risks(
        comparisons.to_dict('records') if not comparisons.empty else [],
        assembly,
        checklist,
    )
    report = build_structured_report(
        st.session_state.project_name,
        docs.to_dict('records'),
        comparisons.to_dict('records'),
        risks=risks,
        checklist_results=checklist,
        assembly_rows=assembly,
    )
    summary = report['summary']

    c1, c2, c3, c4 = st.columns(4)
    with c1: card('Объектов', summary['objects'], 'Подтверждённый состав проекта')
    with c2: card('К проверке', summary['requires_attention'], 'Межраздельные вопросы', 'warn' if summary['requires_attention'] else 'ok')
    with c3: card('Высокий риск', summary['risks_high'], 'Приоритет до передачи', 'bad' if summary['risks_high'] else 'ok')
    with c4: card('Чек-листы', summary['checklist_total'], 'Рассмотрено пунктов')

    st.info(report['conclusion'])
    section('Выберите форму отчёта', 'Каждый вариант имеет собственный уровень детализации. Технические массивы не включаются в основной отчёт.')

    cols = st.columns(3)
    with cols[0]:
        card('Резюме руководителя', '1–2 стр.', 'Итог, ключевые риски и первоочередные действия')
        st.download_button(
            'Скачать резюме Excel',
            data=structured_excel_report(
                st.session_state.project_name, ctx.version, docs, findings, comparisons,
                report_kind='manager', risks=risks, checklist_results=checklist, assembly_rows_data=assembly,
            ),
            file_name='ExpertCheck_Резюме_руководителя.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            width='stretch',
        )
    with cols[1]:
        card('Отчёт ГИПа', 'Основной', 'Риски, состав проекта, проблемные сверки и чек-листы')
        st.download_button(
            'Скачать отчёт ГИПа Excel',
            data=structured_excel_report(
                st.session_state.project_name, ctx.version, docs, findings, comparisons,
                report_kind='gip', risks=risks, checklist_results=checklist, assembly_rows_data=assembly,
            ),
            file_name='ExpertCheck_Отчёт_ГИПа.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            width='stretch',
        )
    with cols[2]:
        card('Техническое приложение', 'Полное', 'Все извлечённые данные, доказательства и диагностика')
        st.download_button(
            'Скачать техническое приложение',
            data=structured_excel_report(
                st.session_state.project_name, ctx.version, docs, findings, comparisons,
                report_kind='technical', risks=risks, checklist_results=checklist, assembly_rows_data=assembly,
            ),
            file_name='ExpertCheck_Техническое_приложение.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            width='stretch',
        )

    tabs = st.tabs(['Ключевые риски', 'Межраздельные вопросы', 'Чек-листы', 'План действий'])
    with tabs[0]:
        risk_rows = [{
            'ID': r.get('risk_id'), 'Уровень': r.get('level'), 'Объект / раздел': r.get('object') or '—',
            'Вопрос': r.get('parameter'), 'Рекомендуемое действие': r.get('recommendation'),
        } for r in risks if r.get('level') in {'Высокий', 'Средний'}]
        if risk_rows:
            st.dataframe(pd.DataFrame(risk_rows), hide_index=True, width='stretch')
        else:
            empty('Высокие и средние риски не сформированы.')
    with tabs[1]:
        if report['problems']:
            st.dataframe(pd.DataFrame(report['problems'])[['id','priority','object','parameter','status']].rename(columns={
                'id':'ID','priority':'Приоритет','object':'Объект','parameter':'Показатель','status':'Результат'}), hide_index=True, width='stretch')
        else:
            empty('Проблемные межраздельные результаты не выявлены.')
    with tabs[2]:
        rows = [r for r in checklist if str(r.get('status') or r.get('result') or '').lower() in {'нет','частично','требует проверки','нет данных','не соответствует'}]
        if rows:
            st.dataframe(pd.DataFrame([{
                'Пункт': f"{r.get('item_no') or ''} — {r.get('question') or ''}".strip(' —'),
                'Результат': r.get('status') or r.get('result'),
            } for r in rows]), hide_index=True, width='stretch')
        else:
            empty('Проблемные результаты чек-листов отсутствуют или чек-лист ещё не запускался.')
    with tabs[3]:
        for idx, text in enumerate(report['recommendations'] or ['Дополнительные действия не сформированы.'], 1):
            st.write(f'{idx}. {text}')

    if st.session_state.get('expert_mode'):
        with st.expander('Техническая диагностика отчёта'):
            st.json(summary)
