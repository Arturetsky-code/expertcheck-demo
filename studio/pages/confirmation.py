from __future__ import annotations
import streamlit as st
from studio.components import hero, card
from studio.pages.completeness import render as render_completeness
from studio.pages.objects import _assembly_editor


def render(ctx):
    docs = ctx.data[0]
    hero('Подтверждение проекта','Проверьте то, что ExpertCheck распознал автоматически. Подтверждённые решения пользователя становятся доверенным контекстом последующей проверки.','Комплектность → объекты → проверка')
    if docs.empty:
        st.info('Сначала загрузите и проанализируйте комплект на странице «Проект».')
        return
    c1,c2,c3=st.columns(3)
    with c1: card('Документы',len(docs),'Распознано в комплекте','ok')
    with c2: card('Комплектность','Подтверждена' if st.session_state.get('completeness_user_confirmed') else 'Требует подтверждения','Решение пользователя','ok' if st.session_state.get('completeness_user_confirmed') else 'warn')
    with c3: card('Состав объектов','Подтверждён' if st.session_state.get('object_registry_confirmed') else 'Требует подтверждения','Trusted Object Registry','ok' if st.session_state.get('object_registry_confirmed') else 'warn')
    tab1,tab2=st.tabs(['1. Комплектность','2. Найденные объекты'])
    with tab1:
        render_completeness(ctx)
    with tab2:
        _assembly_editor(ctx)
