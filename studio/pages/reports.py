from __future__ import annotations
import streamlit as st
from studio.components import section, empty, card
from studio.data import excel_report
from core.report_engine import build_decision_report


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    section('Центр отчётов', 'Выберите уровень детализации. Основной отчёт содержит только результаты, требующие решения.')
    if docs.empty:
        return empty('Сначала выполните проверку проекта.')
    report = build_decision_report(docs.to_dict('records'), comparisons.to_dict('records'))
    summary = report['summary']
    cols = st.columns(3)
    with cols[0]: card('Отчёт ГИПа', summary['requires_attention'], 'Проблемы и рекомендации', 'warn')
    with cols[1]: card('Реестр объектов', summary['objects'], 'Объекты и цифровые паспорта')
    with cols[2]: card('Полная диагностика', summary['checks'], 'Все сверки и доказательства')
    st.download_button(
        'Скачать отчёт Excel',
        data=excel_report(st.session_state.project_name, ctx.version, docs, findings, comparisons),
        file_name='ExpertCheck_report.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        width='stretch',
    )
    with st.expander('Рекомендации'):
        for text in report['recommendations'] or ['Дополнительные действия не сформированы.']:
            st.write('• ' + text)
    if st.session_state.expert_mode:
        with st.expander('Техническая диагностика'):
            st.dataframe(comparisons, width='stretch', hide_index=True)
