import streamlit as st
from studio.components import section,empty

def render(ctx):
    docs=ctx.data[0];section('Документы проекта','Состав комплекта, типы разделов и результаты обработки.')
    if docs.empty:return empty('Сначала загрузите комплект на странице «Обзор».')
    preferred=['Файл','Раздел','Страниц','Размер','XML-схема','Распознано страниц с таблицами'];view=docs[[c for c in preferred if c in docs]].copy()
    if view.empty:view=docs[[c for c in docs.columns if not c.endswith('summary') and not c.startswith('dem_')]].copy()
    st.dataframe(view,use_container_width=True,hide_index=True)
    if st.session_state.expert_mode:
        with st.expander('Диагностика документов'):st.dataframe(docs,use_container_width=True,hide_index=True)
