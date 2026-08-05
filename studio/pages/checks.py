from __future__ import annotations

import pandas as pd
import streamlit as st

from core.checklist_engine import ChecklistEngine
from studio.components import card, empty, section


def _cross_checks(ctx, df: pd.DataFrame):
    section('Межраздельные сверки','Сопоставление инженерных характеристик выполняется только по подтвержденным объектам.')
    if df.empty:
        return empty('Сопоставимые сведения не найдены.')
    statuses=sorted(df.get('status',pd.Series(dtype=str)).dropna().astype(str).unique())
    c1,c2=st.columns([1,2]); selected=c1.multiselect('Статус',statuses,default=statuses,key='cross_status'); q=c2.text_input('Поиск',key='cross_search'); view=df.copy()
    if selected and 'status' in view:view=view[view.status.isin(selected)]
    if q:view=view[view.astype(str).apply(lambda c:c.str.contains(q,case=False,na=False)).any(axis=1)]
    cols=['object','parameter_name','status','documents','document_values','explanation']
    if st.session_state.expert_mode:cols+=['check_code','priority','evidence_count','sources','engineering_risk_level']
    labels={'object':'Объект','parameter_name':'Характеристика','status':'Результат','documents':'Разделы','document_values':'Значения','explanation':'Объяснение','check_code':'Код','priority':'Приоритет','evidence_count':'Подтверждений','sources':'Источники','engineering_risk_level':'Риск'}
    st.dataframe(view[[c for c in cols if c in view]].rename(columns=labels),width='stretch',hide_index=True)


def _checklists(ctx, docs, findings, comparisons):
    section('Проверка по корпоративным чек-листам','Пункты разделены на автоматические, частично автоматические и ручные. Ручные пункты не выдаются за выполненные системой.')
    engine=ChecklistEngine(ctx.config_dir/'knowledge'/'checklist_catalog.json')
    results=engine.evaluate(docs.to_dict('records'),comparisons.to_dict('records'),findings.to_dict('records'))
    if not results:return empty('Каталог чек-листов не загружен.')
    summary=engine.summary(results)
    c1,c2,c3,c4=st.columns(4)
    with c1: card('Всего пунктов',summary['total'],'Интегрировано из 15 чек-листов')
    with c2: card('Автоматически',summary['automatic'],'Есть структурированные доказательства','ok')
    with c3: card('Подготовлено',summary['prepared'],'Нужна оценка специалиста','warn')
    with c4: card('Ручная проверка',summary['manual'],'Инженерное решение обязательно','info')
    df=pd.DataFrame(results)
    source_options=sorted(df['source_file'].unique())
    f1,f2,f3=st.columns([1.5,1,1])
    source=f1.selectbox('Чек-лист',source_options)
    levels=f2.multiselect('Уровень автоматизации',['A','B','C'],default=['A','B','C'])
    statuses=sorted(df['status'].unique())
    selected=f3.multiselect('Результат',statuses,default=statuses)
    view=df[(df.source_file==source)&df.automation_level.isin(levels)&df.status.isin(selected)]
    show=['item_no','sheet','question','automation_level','status','evidence','priority','where_to_check','risk']
    labels={'item_no':'№','sheet':'Вкладка','question':'Контрольный вопрос','automation_level':'Тип','status':'Результат','evidence':'Основание','priority':'Приоритет','where_to_check':'Где сверить','risk':'Риск / замечание'}
    st.dataframe(view[[c for c in show if c in view]].rename(columns=labels),width='stretch',hide_index=True,height=520)
    st.caption('A — автоматизируемый пункт; B — система подготавливает доказательства; C — обязательная ручная инженерная проверка.')


def render(ctx):
    docs,findings,comparisons=ctx.data[:3]
    tabs=st.tabs(['Межраздельные сверки','Чек-листы'])
    with tabs[0]: _cross_checks(ctx,comparisons)
    with tabs[1]: _checklists(ctx,docs,findings,comparisons)
