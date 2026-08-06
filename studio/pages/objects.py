from __future__ import annotations

import pandas as pd
import streamlit as st

from studio.components import card, empty, section
from core.ai_gateway import analyze_object_fragment, diagnostic_message, provider_for_role

VISIBLE_EDITOR_COLS = [
    'Включить','Позиция по ГП','Наименование объекта','Статус проектирования','Доверие',
    'Количество доказательств','Независимых документов','Официальных источников','Решение Object Intelligence','Доверие Object Intelligence','Канонический источник','Обоснование Object Intelligence','Основание включения','Блокировка','Решение пользователя','Комментарий пользователя'
]


def _render_evidence(rows: list[dict]) -> None:
    section('Доказательства происхождения','Каждый объект должен иметь проверяемую ссылку на документ, страницу, раздел или таблицу.')
    labels=[]; mapping={}
    for row in rows:
        label=f"{row.get('Позиция по ГП') or '—'} · {row.get('Наименование объекта') or 'Без наименования'}"
        labels.append(label); mapping[label]=row
    selected=st.selectbox('Объект или кандидат',labels,key='evidence_object_selector')
    row=mapping[selected]
    evidence=row.get('_evidence') or []
    if not evidence:
        st.warning('Для позиции не сохранено структурированное доказательство. Рекомендуется не включать её автоматически.')
        return
    for idx,ev in enumerate(evidence,1):
        status='Отклонённый источник' if ev.get('forbidden') else 'Допустимое доказательство'
        title=f"{idx}. {ev.get('document_type') or 'Документ'} · стр. {ev.get('page') or '—'} · {status}"
        with st.expander(title,expanded=idx==1):
            st.write({
                'Файл':ev.get('document') or '—',
                'Раздел/пункт':ev.get('section') or '—',
                'Таблица':ev.get('table') or '—',
                'Строка таблицы':ev.get('row') or '—',
                'Тип источника':ev.get('source_type_label') or '—',
                'Статус проектирования':ev.get('lifecycle') or '—',
                'Уверенность':ev.get('confidence') if ev.get('confidence')!='' else '—',
                'Фрагмент':ev.get('quote') or '—',
            })
            if ev.get('forbidden'):
                st.error(f"Источник запрещён для создания объекта: {ev.get('forbidden_reason')}")



def _render_ai_review(rows: list[dict]) -> None:
    if not st.session_state.get('ai_assisted_extraction'):
        return
    provider=provider_for_role('extraction', st.session_state, st.secrets)
    if provider is None:
        st.warning('AI-проверка включена, но внешний провайдер не настроен.')
        return
    candidates=[r for r in rows if str(r.get('Решение Object Intelligence') or '').lower() in {'review','blocked','context'} or not r.get('Включить')]
    if not candidates:
        return
    section('AI-проверка спорных кандидатов','OpenRouter/Groq анализирует только выбранный кандидат и его доказательства. Решение пользователя остаётся обязательным.')
    labels=[f"{r.get('Позиция по ГП') or '—'} · {r.get('Наименование объекта') or 'Без наименования'}" for r in candidates]
    label=st.selectbox('Кандидат для AI-анализа',labels,key='ai_object_candidate')
    row=candidates[labels.index(label)]
    if st.button('Проанализировать кандидата внешним AI',key='ai_review_object_btn'):
        fragment={
            'position':row.get('Позиция по ГП'), 'name':row.get('Наименование объекта'),
            'design_status':row.get('Статус проектирования'), 'core_decision':row.get('Решение Object Intelligence'),
            'core_reason':row.get('Обоснование Object Intelligence') or row.get('Блокировка'),
            'canonical_source':row.get('Канонический источник'), 'evidence':row.get('_evidence') or [],
        }
        with st.spinner('AI анализирует доказательства кандидата...'):
            result,data=analyze_object_fragment(provider,fragment)
        if result.ok and data:
            st.session_state.ai_object_reviews[label]=data
        elif result.ok:
            st.warning('AI вернул ответ, который не удалось преобразовать в структурированное решение.')
            st.code(result.text)
        else:
            st.error(diagnostic_message(result))
    review=st.session_state.get('ai_object_reviews',{}).get(label)
    if review:
        st.write({
            'Классификация AI':review.get('entity_type'), 'Статус проектирования':review.get('design_status'),
            'Самостоятельный объект':review.get('independent_object'), 'Уверенность':review.get('confidence'),
            'Рекомендация':review.get('recommended_action'), 'Обоснование':review.get('reason'),
        })
        st.caption('Результат AI является рекомендацией и не меняет состав проекта автоматически.')

def _assembly_editor() -> None:
    section('Мастер формирования состава проекта','Система формирует кандидатов и показывает доказательства. Пользователь исключает лишнее; только затем разрешается межраздельная сверка.')
    rows=st.session_state.get('object_assembly_rows') or []
    if not rows:
        st.info('Кандидаты объектов не извлечены.')
        return
    df=pd.DataFrame(rows)
    display_cols=[c for c in VISIBLE_EDITOR_COLS if c in df.columns]
    edited=st.data_editor(
        df[display_cols], hide_index=True, width='stretch', height=500,
        disabled=[c for c in display_cols if c not in {'Включить','Решение пользователя','Комментарий пользователя'}],
        column_config={
            'Включить':st.column_config.CheckboxColumn('Включить в состав проекта'),
            'Решение пользователя':st.column_config.SelectboxColumn('Причина решения',options=[
                'Не задано','Подтверждённый объект','Имя файла или документ','Существующий объект',
                'Перспективный объект','Оборудование внутри объекта','Дублирующая запись',
                'Ошибочно распознанный текст','Другое'
            ]),
        }, key='object_assembly_editor',
    )
    updated=[]
    for original,edit in zip(rows,edited.to_dict('records')):
        merged=dict(original); merged.update(edit); updated.append(merged)
    chosen=int(edited['Включить'].fillna(False).sum()); excluded=len(edited)-chosen
    c1,c2,c3=st.columns(3)
    with c1: card('Кандидатов',len(edited),'Все найденные сущности')
    with c2: card('Будет включено',chosen,'После подтверждения','ok' if chosen else 'warn')
    with c3: card('Исключено',excluded,'Не участвуют в сверке','info')
    if updated != rows and st.session_state.get('object_registry_confirmed'):
        st.warning('Перечень изменён. Подтвердите его повторно.')
        st.session_state.object_registry_confirmed=False
    b1,b2=st.columns([1,2])
    if b1.button('Сохранить и подтвердить состав',type='primary',width='stretch'):
        unresolved=[r for r in updated if r.get('Включить') and (not r.get('Количество доказательств') or r.get('Блокировка'))]
        if unresolved:
            st.error(f'Нельзя подтвердить состав: {len(unresolved)} включённых позиций не имеют допустимого доказательства либо основаны на запрещённом источнике.')
        else:
            st.session_state.object_assembly_rows=updated
            st.session_state.object_registry_confirmed=True
            st.success('Состав проекта подтверждён. Сверка будет выполнена только по выбранным объектам.')
            st.rerun()
    if b2.button('Сбросить ручные решения',width='content'):
        for row in st.session_state.object_assembly_rows:
            row['Включить']=row.get('Автоматическое решение')=='Предложено включить'
            row['Решение пользователя']='Не задано'; row['Комментарий пользователя']=''
        st.session_state.object_registry_confirmed=False; st.rerun()
    _render_evidence(updated)
    _render_ai_review(updated)


def render(ctx):
    _assembly_editor()
    if not st.session_state.get('object_registry_confirmed'):
        st.info('Подтвердите состав проекта выше. До этого паспорта и межраздельные сверки недоступны.')
        return
    registry, passports = ctx.data[3], ctx.data[4]
    section('Подтверждённый реестр объектов','Только позиции с допустимыми доказательствами, подтверждённые пользователем.')
    if registry.empty:return empty('В состав проекта не включено ни одного объекта.')
    quantity_col=next((c for c in ['Количество','quantity'] if c in registry.columns),None)
    query=st.text_input('Поиск по позиции или наименованию')
    view=registry.copy()
    if query:view=view[view.astype(str).apply(lambda c:c.str.contains(query,case=False,na=False)).any(axis=1)]
    total_physical=int(pd.to_numeric(registry[quantity_col],errors='coerce').fillna(1).sum()) if quantity_col else len(registry)
    m1,m2=st.columns(2)
    with m1:card('Реестровые позиции',len(registry),'Подтверждены пользователем','ok')
    with m2:card('Физические объекты',total_physical,'С учётом количества','info')
    main=['Позиция по ГП','Наименование объекта','Тип объекта','Количество','Количество источников','Статус проектирования','Доверие к объекту']
    st.dataframe(view[[c for c in main if c in view]],width='stretch',hide_index=True,height=400)
    if not passports:return
    section('Цифровой паспорт объекта','Характеристики и источники выбранного объекта.')
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
