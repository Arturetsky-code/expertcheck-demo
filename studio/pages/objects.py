from __future__ import annotations

import pandas as pd
import streamlit as st

from studio.components import card, empty, section


def _status_text(row: pd.Series) -> str:
    for key in ['Статус консолидации', 'status', 'Статус']:
        if key in row and pd.notna(row.get(key)):
            return str(row.get(key))
    return ''


def render(ctx):
    registry, passports = ctx.data[3], ctx.data[4]
    section('Подтвержденный реестр объектов', 'В основной перечень включаются только проектируемые и реконструируемые объекты с сильными структурными доказательствами.')
    if registry.empty:
        return empty('Реестр объектов ещё не сформирован.')

    position_col = next((c for c in ['Позиция по ГП', 'position', 'Позиция'] if c in registry.columns), None)
    name_col = next((c for c in ['Наименование объекта', 'name', 'Объект'] if c in registry.columns), None)
    quantity_col = next((c for c in ['Количество', 'quantity'] if c in registry.columns), None)
    status_col = next((c for c in ['Статус консолидации', 'status', 'Статус'] if c in registry.columns), None)

    statuses = sorted(registry[status_col].dropna().astype(str).unique()) if status_col else []
    f1, f2 = st.columns([1.25, 2])
    selected_statuses = f1.multiselect('Статус', statuses, default=statuses)
    query = f2.text_input('Поиск по позиции или наименованию')

    view = registry.copy()
    if selected_statuses and status_col:
        view = view[view[status_col].astype(str).isin(selected_statuses)]
    if query:
        view = view[view.astype(str).apply(lambda c: c.str.contains(query, case=False, na=False)).any(axis=1)]

    total_physical = int(pd.to_numeric(registry[quantity_col], errors='coerce').fillna(1).sum()) if quantity_col else len(registry)
    conflicts = int(registry.apply(lambda r: 'КОНФЛИКТ' in _status_text(r).upper() or 'ТРЕБУЕТ' in _status_text(r).upper(), axis=1).sum())
    m1, m2, m3 = st.columns(3)
    with m1:
        card('Реестровые позиции', len(registry), 'Уникальные строки консолидированного реестра')
    with m2:
        card('Физические объекты', total_physical, 'С учётом количества экземпляров', 'info')
    with m3:
        card('Требуют проверки', conflicts, 'Конфликты и неподтверждённые позиции', 'warn' if conflicts else 'ok')

    main = ['Позиция по ГП', 'Наименование объекта', 'Тип объекта', 'Количество', 'Количество источников', 'Статус консолидации', 'Конфликты']
    extra=['Статус проектирования','Доверие к объекту']
    st.dataframe(view[[c for c in main+extra if c in view]], width='stretch', hide_index=True, height=420)

    if not ctx.data[0].empty and 'consolidated_candidates' in ctx.data[0].columns:
        candidates=pd.DataFrame(ctx.data[0].iloc[0].get('consolidated_candidates') or [])
        if not candidates.empty:
            with st.expander(f'Кандидаты, не включенные в основной реестр ({len(candidates)})'):
                st.caption('Эти записи не участвуют в подсчете объектов, сверке ТЭП и формировании замечаний до подтверждения.')
                ccols=['Позиция по ГП','Наименование объекта','Статус проектирования','Доверие к объекту','Статус консолидации','Источники']
                st.dataframe(candidates[[c for c in ccols if c in candidates]],width='stretch',hide_index=True)

    if not passports:
        return

    section('Цифровой паспорт объекта', 'Выберите объект и проверьте его характеристики, источники и подтверждение по разделам.')
    labels = [f"{p.get('position', '') or '—'} · {p.get('name', '') or 'Объект без наименования'}" for p in passports]
    selected_label = st.selectbox('Объект', labels)
    passport = passports[labels.index(selected_label)]

    cols = st.columns(4)
    with cols[0]:
        card('Позиция', passport.get('position') or '—', passport.get('object_type_name') or 'Тип не определён')
    with cols[1]:
        card('Количество', passport.get('quantity', 1), 'Физических экземпляров')
    with cols[2]:
        card('Характеристики', len(passport.get('characteristics', [])), 'Связанные инженерные параметры', 'ok')
    with cols[3]:
        card('Полнота', f"{float(passport.get('passport_completeness', 0)):.0f}%", 'Наполнение цифрового паспорта', 'warn')

    sources = passport.get('sections') or passport.get('source_sections') or passport.get('confirmation_matrix') or {}
    if sources:
        section('Подтверждение по разделам', 'В каких источниках объект был обнаружен.')
        if isinstance(sources, dict):
            source_rows = [{'Раздел': k, 'Статус': v if not isinstance(v, bool) else ('Подтвержден' if v else 'Не найден')} for k, v in sources.items()]
        elif isinstance(sources, list):
            source_rows = [{'Раздел': x, 'Статус': 'Подтвержден'} for x in sources]
        else:
            source_rows = [{'Раздел': str(sources), 'Статус': 'Подтвержден'}]
        st.dataframe(pd.DataFrame(source_rows), width='stretch', hide_index=True)


    expected = passport.get('expected_parameter_codes') or []
    missing = passport.get('missing_expected_parameter_codes') or []
    if expected:
        section('Ожидаемые характеристики', 'Набор параметров выбран по распознанному типу объекта.')
        e1, e2 = st.columns(2)
        with e1:
            st.caption('Ожидаются')
            st.write(', '.join(expected))
        with e2:
            st.caption('Пока не найдены')
            st.write(', '.join(missing) if missing else 'Все ожидаемые характеристики найдены')

    ch = pd.DataFrame(passport.get('characteristics', []))
    if ch.empty:
        st.info('Для выбранного объекта характеристики пока не извлечены.')
        return

    ch = ch.rename(columns={
        'parameter_name': 'Характеристика', 'unit': 'Ед. изм.',
        'values_by_section': 'Значения по разделам', 'status': 'Статус',
        'source_count': 'Источников', 'confidence': 'Уверенность'
    })
    visible = ['Характеристика', 'Ед. изм.', 'Значения по разделам', 'Статус', 'Источников']
    if st.session_state.expert_mode:
        visible += ['Уверенность', 'pages_by_section', 'evidence_count']
    st.dataframe(ch[[c for c in visible if c in ch]], width='stretch', hide_index=True)

    aliases = passport.get('name_variants') or passport.get('aliases') or []
    if aliases and st.session_state.expert_mode:
        with st.expander('Варианты наименования объекта'):
            st.write(aliases)
