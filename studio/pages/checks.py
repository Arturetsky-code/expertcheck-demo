from __future__ import annotations

import pandas as pd
import streamlit as st

from studio.components import card, empty, section


def render(ctx):
    df=ctx.data[2]
    section('Межраздельная сверка','Сравнение характеристик выполняется только по подтверждённому пользователем составу объектов.')
    if not st.session_state.get('object_registry_confirmed'):
        st.warning('Quality Gate не пройден. Откройте раздел «Объекты», исключите лишние позиции и подтвердите состав проекта.')
        a,b,c=st.columns(3)
        with a: card('Шаг 1','Завершён','Документация загружена','ok')
        with b: card('Шаг 2','Требуется','Подтвердить перечень объектов','warn')
        with c: card('Шаг 3','Заблокирован','Сверка ТЭП')
        return
    if df.empty:return empty('После подтверждения состава сопоставимые сведения не найдены.')
    statuses=sorted(df.get('status',pd.Series(dtype=str)).dropna().astype(str).unique())
    c1,c2=st.columns([1,2]); selected=c1.multiselect('Статус',statuses,default=statuses,key='cross_status'); q=c2.text_input('Поиск',key='cross_search'); view=df.copy()
    if selected and 'status' in view:view=view[view.status.isin(selected)]
    if q:view=view[view.astype(str).apply(lambda c:c.str.contains(q,case=False,na=False)).any(axis=1)]
    cols=['object','parameter_name','status','documents','document_values','explanation']
    if st.session_state.expert_mode:cols+=['check_code','priority','evidence_count','sources','engineering_risk_level']
    labels={'object':'Объект','parameter_name':'Характеристика','status':'Результат','documents':'Разделы','document_values':'Значения','explanation':'Объяснение','check_code':'Код','priority':'Приоритет','evidence_count':'Подтверждений','sources':'Источники','engineering_risk_level':'Риск'}
    st.dataframe(view[[c for c in cols if c in view]].rename(columns=labels),width='stretch',hide_index=True)
