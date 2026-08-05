from __future__ import annotations

import pandas as pd
import streamlit as st

from studio.components import card, empty, section


def _assembly_editor() -> None:
    section('Мастер формирования состава проекта','Проверьте кандидатов, исключите файлы, служебные строки, существующие и перспективные объекты. Межраздельная сверка запускается только после подтверждения этого перечня.')
    rows=st.session_state.get('object_assembly_rows') or []
    if not rows:
        st.info('Кандидаты объектов не извлечены.')
        return
    df=pd.DataFrame(rows)
    edited=st.data_editor(
        df,
        hide_index=True,
        width='stretch',
        height=480,
        disabled=[c for c in df.columns if c not in {'Включить'}],
        column_config={'Включить':st.column_config.CheckboxColumn('Включить в состав проекта')},
        key='object_assembly_editor',
    )
    chosen=int(edited['Включить'].fillna(False).sum())
    excluded=len(edited)-chosen
    c1,c2,c3=st.columns(3)
    with c1: card('Кандидатов',len(edited),'Все найденные сущности')
    with c2: card('Будет включено',chosen,'После подтверждения','ok' if chosen else 'warn')
    with c3: card('Исключено',excluded,'Не участвуют в сверке','info')
    changed=edited.to_dict('records') != rows
    if changed and st.session_state.get('object_registry_confirmed'):
        st.warning('Перечень изменён. Подтвердите его повторно, чтобы обновить межраздельную сверку.')
        st.session_state.object_registry_confirmed=False
    b1,b2=st.columns([1,2])
    if b1.button('Сохранить и подтвердить состав',type='primary',width='stretch'):
        st.session_state.object_assembly_rows=edited.to_dict('records')
        st.session_state.object_registry_confirmed=True
        st.success('Состав проекта подтверждён. Межраздельная сверка выполняется только по выбранным объектам.')
        st.rerun()
    if b2.button('Сбросить ручные решения',width='content'):
        for row in st.session_state.object_assembly_rows:
            row['Включить']=row.get('Автоматическое решение')=='Предложено включить'
        st.session_state.object_registry_confirmed=False
        st.rerun()


def render(ctx):
    _assembly_editor()
    if not st.session_state.get('object_registry_confirmed'):
        st.info('Подтвердите состав проекта выше. До этого реестр, паспорта и сверки скрыты, чтобы система не формировала выводы по ложным объектам.')
        return

    registry, passports = ctx.data[3], ctx.data[4]
    section('Подтверждённый реестр объектов', 'В реестре остаются только позиции, выбранные пользователем в мастере состава проекта.')
    if registry.empty:
        return empty('После ручной проверки в состав проекта не включено ни одного объекта.')

    position_col = next((c for c in ['Позиция по ГП', 'position', 'Позиция'] if c in registry.columns), None)
    name_col = next((c for c in ['Наименование объекта', 'name', 'Объект'] if c in registry.columns), None)
    quantity_col = next((c for c in ['Количество', 'quantity'] if c in registry.columns), None)
    f1,f2=st.columns([1,2]); query=f2.text_input('Поиск по позиции или наименованию')
    view=registry.copy()
    if query:view=view[view.astype(str).apply(lambda c:c.str.contains(query,case=False,na=False)).any(axis=1)]
    total_physical=int(pd.to_numeric(registry[quantity_col],errors='coerce').fillna(1).sum()) if quantity_col else len(registry)
    m1,m2=st.columns(2)
    with m1: card('Реестровые позиции',len(registry),'Подтверждены пользователем','ok')
    with m2: card('Физические объекты',total_physical,'С учётом количества экземпляров','info')
    main=['Позиция по ГП','Наименование объекта','Тип объекта','Количество','Количество источников','Статус проектирования','Доверие к объекту']
    st.dataframe(view[[c for c in main if c in view]],width='stretch',hide_index=True,height=400)

    if not passports:return
    section('Цифровой паспорт объекта','Характеристики и источники выбранного подтверждённого объекта.')
    labels=[f"{p.get('position','') or '—'} · {p.get('name','') or 'Объект без наименования'}" for p in passports]
    selected=st.selectbox('Объект',labels); passport=passports[labels.index(selected)]
    cols=st.columns(4)
    with cols[0]:card('Позиция',passport.get('position') or '—',passport.get('object_type_name') or 'Тип не определён')
    with cols[1]:card('Количество',passport.get('quantity',1),'Физических экземпляров')
    with cols[2]:card('Характеристики',len(passport.get('characteristics',[])),'Связанные инженерные параметры','ok')
    with cols[3]:card('Полнота',f"{float(passport.get('passport_completeness',0)):.0f}%",'Наполнение цифрового паспорта','warn')
    ch=pd.DataFrame(passport.get('characteristics',[]))
    if ch.empty:return st.info('Для выбранного объекта характеристики пока не извлечены.')
    ch=ch.rename(columns={'parameter_name':'Характеристика','unit':'Ед. изм.','values_by_section':'Значения по разделам','status':'Статус','source_count':'Источников','confidence':'Уверенность'})
    visible=['Характеристика','Ед. изм.','Значения по разделам','Статус','Источников']
    if st.session_state.expert_mode:visible+=['Уверенность','pages_by_section','evidence_count']
    st.dataframe(ch[[c for c in visible if c in ch]],width='stretch',hide_index=True)
