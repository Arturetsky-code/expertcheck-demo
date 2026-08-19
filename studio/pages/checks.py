from __future__ import annotations

import pandas as pd
import streamlit as st

from studio.components import card, empty, section


def render(ctx):
    df=ctx.data[2]
    section('Межраздельная сверка','Сначала показаны только результаты, требующие внимания. Совпадения доступны отдельной вкладкой.')
    if not st.session_state.get('object_registry_confirmed'):
        st.warning('Сначала подтвердите состав объектов.')
        return
    if df.empty:
        return empty('Для подтверждённых объектов сопоставимые характеристики не найдены.')

    status=df.get('status',pd.Series(dtype=str)).fillna('').astype(str)
    bad_mask=status.str.contains('РАСХОЖД|КОНФЛИКТ',case=False,regex=True)
    warn_mask=status.str.contains('НЕДОСТАТОЧ|УТОЧ|НЕ ПРОВЕР',case=False,regex=True)
    ok_mask=status.str.contains('СОВПАД',case=False,regex=True)
    a,b,c,d=st.columns(4)
    with a: card('Проверок',len(df),'Всего сопоставленных характеристик')
    with b: card('Совпадает',int(ok_mask.sum()),'Подтверждено разделами','ok')
    with c: card('Требует проверки',int(warn_mask.sum()),'Недостаточно доказательств','warn')
    with d: card('Расхождения',int(bad_mask.sum()),'Приоритетная проверка','bad')

    tab_attention,tab_all=st.tabs(['Требует внимания','Все результаты'])
    for tab,base_view in ((tab_attention,df[bad_mask|warn_mask].copy()),(tab_all,df.copy())):
        with tab:
            q=st.text_input('Поиск по объекту или характеристике',key=f'cross_search_{"attention" if tab is tab_attention else "all"}')
            view=base_view
            if q:
                view=view[view.astype(str).apply(lambda c:c.str.contains(q,case=False,na=False)).any(axis=1)]
            if view.empty:
                st.success('Результатов, требующих внимания, нет.')
                continue
            compact=['object','parameter_name','status','preliminary_compliance','document_values']
            labels={'object':'Объект','parameter_name':'Характеристика','status':'Результат','preliminary_compliance':'Предварительная оценка','document_values':'Значения по разделам'}
            st.dataframe(view[[c for c in compact if c in view]].rename(columns=labels),width='stretch',hide_index=True,height=430)
            choices=[]; mapping={}
            for idx,row in view.iterrows():
                label=f"{row.get('object') or 'Объект'} · {row.get('parameter_name') or 'Показатель'} · {row.get('status') or ''}"
                choices.append(label); mapping[label]=row
            selected=st.selectbox('Открыть подробности',choices,key=f'cross_detail_{"attention" if tab is tab_attention else "all"}')
            row=mapping[selected]
            with st.container(border=True):
                st.markdown(f"**{row.get('object') or 'Объект'} — {row.get('parameter_name') or 'Показатель'}**")
                st.write(row.get('explanation') or 'Пояснение отсутствует.')
                st.markdown(f"**Значения:** {row.get('document_values') or '—'}")
                owners=row.get('data_owner_sections') or []
                dependents=row.get('dependent_sections') or []
                if owners or dependents:
                    st.markdown('**Логика межраздельной проверки**')
                    if owners: st.write('Профильный источник данных: ' + ', '.join(str(x) for x in owners))
                    if dependents: st.write('Разделы для контрольной сверки: ' + ', '.join(str(x) for x in dependents))
                    if row.get('dependency_rationale'): st.caption(str(row.get('dependency_rationale')))
                norms=row.get('normative_requirements') or []
                if norms:
                    with st.expander('Нормативный контекст · предварительная оценка'):
                        for norm in norms[:5]:
                            st.markdown(f"**{norm.get('source','')} · {norm.get('topic','')}**")
                            st.write(norm.get('requirement') or '')
                            q=norm.get('normative_quality') or {}
                            mode=q.get('conclusion_mode') or ''
                            debt='; '.join(q.get('verification_debt') or [])
                            st.caption((norm.get('status') or 'Требует проверки актуальности') + (f" · {mode}" if mode else ''))
                            if debt: st.caption('Долг верификации: ' + debt)
                        st.caption('ExpertCheck использует этот контекст для предварительной предподачной проверки. Итоговое нормативное заключение должен подтвердить специалист.')
                if row.get('sources'):
                    with st.expander('Показать источники'):
                        st.write(row.get('sources'))
                if st.session_state.get('expert_mode'):
                    with st.expander('Техническая диагностика'):
                        fields=['check_code','priority','evidence_count','independent_section_count','independent_trusted_sources','trusted_section_families','engineering_risk_level','tolerance']
                        st.write({f:row.get(f) for f in fields if f in row})
