from __future__ import annotations

import pandas as pd
import streamlit as st

from studio.components import card, empty, section


def _present(value) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    if isinstance(value, str) and value.strip().casefold() in {'', 'nan', 'none', 'null', 'nat'}:
        return False
    return value not in ([], {}, ())


def _as_list(value) -> list[str]:
    if not _present(value):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(x).strip() for x in value if _present(x) and str(x).strip()]
    return [str(value).strip()]


def _render_gate(row) -> None:
    raw_gate = row.get('cross_section_gate')
    if not _present(raw_gate):
        return
    if not isinstance(raw_gate, dict):
        st.warning(
            'Статус строгого доказательного gate сохранён в устаревшем формате. '
            'Для этой строки требуется повторная межраздельная проверка.'
        )
        if st.session_state.get('expert_mode'):
            st.caption(f'Техническое значение legacy gate: {raw_gate!r}')
        return

    gate = raw_gate
    passed = bool(gate.get('passed'))
    route = str(gate.get('proof_route') or '').strip().upper()
    owner_present = _as_list(gate.get('owner_present'))
    control_present = _as_list(gate.get('control_present'))
    trusted_sections = _as_list(gate.get('trusted_sections'))
    reasons = _as_list(gate.get('reasons'))

    st.markdown('**Строгий доказательный gate:** ' + ('пройден' if passed else 'не пройден'))
    route_labels = {
        'OWNER_CONTROL': 'владелец → независимый контроль',
        'INDEPENDENT_AGREEMENT': 'два независимых источника подтверждают совпадение',
        'INDEPENDENT_CONFLICT': 'два независимых источника подтверждают конфликт',
    }
    if route:
        st.write('Маршрут доказательства: ' + route_labels.get(route, route))
    st.write('Фактически найден владелец: ' + (', '.join(owner_present) or '—'))
    st.write('Фактически найден контроль: ' + (', '.join(control_present) or '—'))
    if trusted_sections:
        st.write('Доверенные независимые разделы: ' + ', '.join(trusted_sections))

    if passed and route == 'INDEPENDENT_CONFLICT' and not owner_present:
        st.info(
            'Конфликт значений доказан двумя независимыми адресными источниками, '
            'но правильное значение ещё не подтверждено профильным разделом-владельцем.'
        )
    elif passed and route == 'INDEPENDENT_AGREEMENT' and not owner_present:
        st.info(
            'Совпадение закрыто по двум независимым доверенным источникам. '
            'Отсутствие owner-раздела не используется как доказательство отдельного несоответствия.'
        )
    if reasons:
        st.caption('Причины: ' + ' | '.join(reasons))


def render(ctx):
    df=ctx.data[2]
    section('Межраздельная сверка','Сначала показаны только результаты, требующие внимания. Совпадения доступны отдельной вкладкой.')
    if not st.session_state.get('object_registry_confirmed'):
        st.warning('Сначала подтвердите состав объектов.')
        return
    if df.empty:
        return empty('Для подтверждённых объектов сопоставимые характеристики не найдены.')

    status=df.get('status',pd.Series('',index=df.index,dtype=str)).fillna('').astype(str)
    final_kind=df.get('final_verification_kind',pd.Series('',index=df.index,dtype=str)).fillna('').astype(str).str.upper()
    has_final=final_kind.ne('')
    bad_mask=final_kind.eq('PROJECT_FINDING') | (~has_final & status.str.contains('РАСХОЖД|КОНФЛИКТ',case=False,regex=True))
    warn_mask=final_kind.isin({'REVIEW_QUESTION','SYSTEM_LIMITATION'}) | (~has_final & status.str.contains('НЕДОСТАТОЧ|УТОЧ|НЕ ПРОВЕР',case=False,regex=True))
    ok_mask=final_kind.eq('VERIFIED_OK') | (~has_final & status.str.contains('СОВПАД',case=False,regex=True))
    a,b,c,d=st.columns(4)
    with a: card('Проверок',len(df),'Всего сопоставленных характеристик')
    with b: card('Завершено L5',int(ok_mask.sum()),'Строгая сверка пройдена','ok')
    with c: card('Не завершено',int(warn_mask.sum()),'Не пройден контракт доказательств','warn')
    with d: card('Несоответствия L5',int(bad_mask.sum()),'Адресные расхождения','bad')

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
            compact=['object','parameter_name','verification_state','evidence_level','status','document_values']
            labels={'object':'Объект','parameter_name':'Характеристика','verification_state':'Итог ExpertCheck','evidence_level':'Уровень','status':'Диагностический статус','document_values':'Значения по разделам'}
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
                owners=_as_list(row.get('data_owner_sections'))
                dependents=_as_list(row.get('dependent_sections'))
                if owners or dependents:
                    st.markdown('**Логика межраздельной проверки**')
                    if owners: st.write('Профильный источник данных: ' + ', '.join(owners))
                    if dependents: st.write('Разделы для контрольной сверки: ' + ', '.join(dependents))
                    if _present(row.get('dependency_rationale')): st.caption(str(row.get('dependency_rationale')))
                _render_gate(row)
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
                if _present(row.get('sources')):
                    with st.expander('Показать источники'):
                        st.write(row.get('sources'))
                if st.session_state.get('expert_mode'):
                    with st.expander('Техническая диагностика'):
                        fields=['check_code','priority','evidence_count','independent_section_count','independent_trusted_sources','trusted_section_families','engineering_risk_level','tolerance']
                        st.write({f:row.get(f) for f in fields if f in row})