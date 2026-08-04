import pandas as pd
import streamlit as st
from studio.components import section,empty,card

def render(ctx):
    registry,passports=ctx.data[3],ctx.data[4];section('Реестр объектов','Консолидированный перечень по ПЗ, генплану, XML и профильным разделам.')
    if registry.empty:return empty('Реестр объектов ещё не сформирован.')
    q=st.text_input('Поиск по позиции или наименованию');view=registry.copy()
    if q:view=view[view.astype(str).apply(lambda c:c.str.contains(q,case=False,na=False)).any(axis=1)]
    main=['Позиция по ГП','Наименование объекта','Количество','Количество источников','Статус консолидации','Конфликты'];st.dataframe(view[[c for c in main if c in view]],use_container_width=True,hide_index=True)
    if passports:
        section('Цифровой паспорт объекта','Выберите объект для просмотра характеристик.')
        labels=[f"{p.get('position','')} · {p.get('name','')}" for p in passports];sel=st.selectbox('Объект',labels);p=passports[labels.index(sel)];cols=st.columns(4)
        with cols[0]:card('Позиция',p.get('position') or '—','По генеральному плану')
        with cols[1]:card('Количество',p.get('quantity',1),'Физических экземпляров')
        with cols[2]:card('Характеристики',len(p.get('characteristics',[])),'Связанные параметры','ok')
        with cols[3]:card('Полнота',f"{float(p.get('passport_completeness',0)):.0f}%",'Наполнение паспорта','warn')
        ch=pd.DataFrame(p.get('characteristics',[]))
        if not ch.empty:
            ch=ch.rename(columns={'parameter_name':'Характеристика','unit':'Ед. изм.','values_by_section':'Значения по разделам','status':'Статус','source_count':'Источников','confidence':'Уверенность'});visible=['Характеристика','Ед. изм.','Значения по разделам','Статус','Источников']
            if st.session_state.expert_mode:visible+=['Уверенность','pages_by_section','evidence_count']
            st.dataframe(ch[[c for c in visible if c in ch]],use_container_width=True,hide_index=True)
