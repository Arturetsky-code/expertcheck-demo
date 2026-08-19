from __future__ import annotations

import pandas as pd
from core.display_localization import parameter_label, localize_parameter_list, status_label
import streamlit as st

from studio.components import card, empty, section
from studio.ai_presenter import render_ai_result, render_unstructured_ai_text
from core.ai_gateway import analyze_object_fragment, diagnostic_message, provider_for_role
from core.learning_engine import object_learning_examples, merge_examples

VISIBLE_EDITOR_COLS = [
    'Включить','Позиция по ГП','Наименование объекта','Статус проектирования',
    'Доверие Object Intelligence','Канонический источник','Решение пользователя','Комментарий пользователя'
]
TECHNICAL_COLS = [
    'Количество доказательств','Независимых документов','Официальных источников',
    'Решение Object Intelligence','Обоснование Object Intelligence','Основание включения','Блокировка'
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
            left, right = st.columns(2)
            with left:
                st.markdown(f"**Файл:** {ev.get('document') or '—'}")
                st.markdown(f"**Раздел / пункт:** {ev.get('section') or '—'}")
                st.markdown(f"**Таблица:** {ev.get('table') or '—'}")
                st.markdown(f"**Строка таблицы:** {ev.get('row') or '—'}")
            with right:
                st.markdown(f"**Тип источника:** {ev.get('source_type_label') or '—'}")
                st.markdown(f"**Статус проектирования:** {ev.get('lifecycle') or '—'}")
                confidence = ev.get('confidence') if ev.get('confidence') not in ('', None) else '—'
                st.markdown(f"**Уверенность:** {confidence}")
            quote = str(ev.get('quote') or '').strip()
            if quote:
                st.markdown('**Фрагмент документа:**')
                st.info(quote)
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
            st.warning('AI вернул ответ без ожидаемой структуры.')
            render_unstructured_ai_text(result.text)
        else:
            st.error(diagnostic_message(result))
    review=st.session_state.get('ai_object_reviews',{}).get(label)
    if review:
        render_ai_result(review, title='Рекомендация AI по кандидату')
        st.caption('Результат AI является рекомендацией и не меняет состав проекта автоматически.')

def _assembly_editor(ctx=None) -> None:
    section('Состав объектов','Сначала используется экспликация генерального плана, затем ПЗ/XML и профильные разделы. Проверьте только спорные позиции.')
    if ctx is not None:
        try:
            docs = ctx.data[0]
            if docs is not None and not docs.empty and 'object_discovery_3_summary' in docs.columns:
                summary = docs.iloc[0].get('object_discovery_3_summary') or {}
                gp = int(summary.get('general_plan_explication_objects') or 0)
                if gp:
                    st.caption(f'General Plan First: в экспликациях найдено {gp} позиций. Они используются как опорный реестр и сверяются с ПЗ, XML и профильными разделами.')
        except Exception:
            pass
    rows=st.session_state.get('object_assembly_rows') or []
    if not rows:
        st.info('Кандидаты объектов не извлечены.')
        return
    df=pd.DataFrame(rows)
    display_cols=[c for c in VISIBLE_EDITOR_COLS if c in df.columns]
    edited=st.data_editor(
        df[display_cols], hide_index=True, width='stretch', height=430,
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

    if st.session_state.get('expert_mode'):
        tech_cols=[c for c in TECHNICAL_COLS if c in df.columns]
        if tech_cols:
            with st.expander('Техническая диагностика определения объектов'):
                st.dataframe(df[['Позиция по ГП','Наименование объекта']+tech_cols], hide_index=True, width='stretch')

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
            st.session_state.object_learning_examples=merge_examples(st.session_state.get('object_learning_examples',[]), object_learning_examples(updated))
            st.session_state.object_registry_confirmed=True
            st.success('Состав проекта подтверждён. Сверка будет выполнена только по выбранным объектам.')
            st.rerun()
    if b2.button('Сбросить ручные решения',width='content'):
        for row in st.session_state.object_assembly_rows:
            row['Включить']=row.get('Автоматическое решение')=='Предложено включить'
            row['Решение пользователя']='Не задано'; row['Комментарий пользователя']=''
        st.session_state.object_registry_confirmed=False; st.rerun()
    tab_sources,tab_ai=st.tabs(['Источники объектов','AI-анализ спорных позиций'])
    with tab_sources:
        _render_evidence(updated)
    with tab_ai:
        _render_ai_review(updated)


def render(ctx):
    _assembly_editor(ctx)
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
    section('Цифровой паспорт объекта','Единая карточка объекта: где он подтверждён, какие ТЭП найдены и что требует внимания.')
    labels=[f"{p.get('position','') or '—'} · {p.get('name','') or 'Объект без наименования'}" for p in passports]
    selected=st.selectbox('Объект',labels); passport=passports[labels.index(selected)]
    st.subheader(passport.get('name') or 'Объект без наименования')
    cols=st.columns(5)
    with cols[0]:card('Позиция',passport.get('position') or '—',passport.get('object_type_name') or 'Тип не определён')
    with cols[1]:card('Количество',passport.get('quantity',1),'Физических экземпляров')
    with cols[2]:card('Источники',len(passport.get('registry_sources') or []),'Разделов с подтверждениями','ok')
    with cols[3]:card('Характеристики',len(passport.get('characteristics',[])),'Извлечённых ТЭП','ok')
    with cols[4]:card('Полнота',f"{float(passport.get('passport_completeness',0)):.0f}%",'Наполнение паспорта','warn')

    tab_summary, tab_props, tab_sources, tab_risks = st.tabs(['Сводка','Характеристики','Где найден','Риски и замечания'])
    with tab_summary:
        matrix=passport.get('confirmation_matrix') or {}
        if matrix:
            st.markdown('**Подтверждение по разделам**')
            st.dataframe(pd.DataFrame([{'Раздел':k,'Статус':v} for k,v in matrix.items()]),hide_index=True,width='stretch',height=250)
        missing=passport.get('missing_expected_parameter_codes') or []
        if missing:
            st.warning('Не найдены ожидаемые для этого типа объекта характеристики: ' + ', '.join(localize_parameter_list(missing)))
        else:
            st.success('Ожидаемые типовые характеристики по доступной модели объекта найдены.')
        aliases=passport.get('aliases') or []
        if aliases:
            st.caption('Варианты наименования в документации: ' + '; '.join(aliases[:8]))

    with tab_props:
        ch=pd.DataFrame(passport.get('characteristics',[]))
        if ch.empty:
            st.info('Для выбранного объекта характеристики пока не извлечены.')
        else:
            rows=[]
            for item in passport.get('characteristics',[]):
                vals=item.get('values_by_section') or {}
                row={'Характеристика':item.get('parameter_name') or parameter_label(item.get('parameter_code')),'Ед. изм.':item.get('unit') or '—','Статус':status_label(item.get('status'))}
                for sec in ['ПЗ','ПЗУ','АР','ТХ','ИОС','ПОС','ООС']:
                    row[sec]=vals.get(sec,'—') if isinstance(vals,dict) else '—'
                rows.append(row)
            prop_df=pd.DataFrame(rows)
            st.dataframe(prop_df,width='stretch',hide_index=True,height=min(480,70+35*len(prop_df)))
            st.caption('Значения показываются по разделам; спорные и отсутствующие ТЭП дополнительно попадают в межраздельную сверку.')

    with tab_sources:
        matrix=passport.get('confirmation_matrix') or {}
        src_rows=[{'Раздел':k,'Наличие':v} for k,v in matrix.items()]
        st.dataframe(pd.DataFrame(src_rows),hide_index=True,width='stretch')
        evidence=passport.get('evidence_sources') or []
        if evidence:
            st.markdown('**Точные источники и страницы**')
            ev_df=pd.DataFrame([{
                'Документ':x.get('document') or '—','Раздел':x.get('section') or '—','Страница / лист':x.get('page') or '—',
                'Зона / таблица':x.get('table') or x.get('zone') or '—','Способ обнаружения':x.get('method') or '—'
            } for x in evidence])
            st.dataframe(ev_df,hide_index=True,width='stretch',height=min(420,70+35*len(ev_df)))
        if passport.get('registry_sources'):
            st.caption('Разделы с подтверждениями: ' + ', '.join(passport.get('registry_sources') or []))

    with tab_risks:
        comparisons_df=ctx.data[2]
        if comparisons_df is None or getattr(comparisons_df,'empty',True):
            st.info('Связанные межраздельные риски не сформированы.')
        else:
            name=str(passport.get('name') or '').lower()
            related=comparisons_df[comparisons_df.get('object',pd.Series(dtype=str)).fillna('').astype(str).str.lower().str.contains(name,regex=False)] if 'object' in comparisons_df.columns and name else pd.DataFrame()
            if related.empty:
                st.success('По выбранному объекту проблемные межраздельные проверки не найдены.')
            else:
                cols=[c for c in ['parameter_name','status','explanation','remark_best_scenario','remark_recurrence','remark_recommendation'] if c in related.columns]
                st.dataframe(related[cols].rename(columns={'parameter_name':'Показатель','status':'Результат','explanation':'Пояснение','remark_best_scenario':'Сценарий замечания','remark_recurrence':'Повторяемость','remark_recommendation':'Рекомендация'}),hide_index=True,width='stretch')
