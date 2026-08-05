from __future__ import annotations

import streamlit as st

from core.engineering_advisor import answer_local_question, summarize_object_registry
from studio.components import card, section


def render(ctx):
    section('Локальный инженерный советник','Объясняет решения Core по объектам и сверкам. Не использует внешний API и не изменяет данные проекта.')
    rows = st.session_state.get('object_assembly_rows') or []
    comparisons = ctx.data[2].to_dict('records') if hasattr(ctx.data[2], 'to_dict') else []
    summary = summarize_object_registry(rows)
    cols = st.columns(4)
    with cols[0]: card('Кандидатов', summary['total'], 'Все найденные сущности')
    with cols[1]: card('Предложено включить', summary['included'], 'До ручного подтверждения', 'ok')
    with cols[2]: card('Требуют решения', summary['review'], 'Недостаточно доказательств', 'warn')
    with cols[3]: card('Заблокировано', summary['blocked'], 'Служебные источники', 'bad')
    question = st.text_area('Вопрос к локальному советнику', placeholder='Например: покажи подозрительные позиции в перечне объектов')
    if st.button('Проанализировать', type='primary'):
        st.markdown(answer_local_question(question, rows, comparisons))
    st.caption('Советник работает только по структурированной модели ExpertCheck и не является языковой моделью.')
