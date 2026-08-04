import pandas as pd
import streamlit as st
from studio.components import section,empty

def render(ctx):
    df=ctx.data[2];section('Межраздельные сверки','Сопоставление инженерных характеристик без метаданных проекта.')
    if df.empty:return empty('Сопоставимые сведения не найдены.')
    statuses=sorted(df.get('status',pd.Series(dtype=str)).dropna().astype(str).unique());c1,c2=st.columns([1,2]);selected=c1.multiselect('Статус',statuses,default=statuses);q=c2.text_input('Поиск');view=df.copy()
    if selected and 'status' in view:view=view[view.status.isin(selected)]
    if q:view=view[view.astype(str).apply(lambda c:c.str.contains(q,case=False,na=False)).any(axis=1)]
    cols=['object','parameter_name','status','documents','document_values','explanation']
    if st.session_state.expert_mode:cols+=['check_code','priority','evidence_count','sources','engineering_risk_level']
    labels={'object':'Объект','parameter_name':'Характеристика','status':'Результат','documents':'Разделы','document_values':'Значения','explanation':'Объяснение','check_code':'Код','priority':'Приоритет','evidence_count':'Подтверждений','sources':'Источники','engineering_risk_level':'Риск'}
    st.dataframe(view[[c for c in cols if c in view]].rename(columns=labels),use_container_width=True,hide_index=True)
