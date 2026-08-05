from __future__ import annotations

import pandas as pd
import streamlit as st

from studio.components import card, empty, section


def _first_present(row: pd.Series, names: list[str], default="—"):
    for name in names:
        if name in row and pd.notna(row.get(name)) and str(row.get(name)).strip():
            return row.get(name)
    return default


def render(ctx):
    docs = ctx.data[0]
    section('Документы проекта', 'Навигация по разделам, состав комплекта и сведения о результатах обработки.')
    if docs.empty:
        return empty('Сначала загрузите комплект на странице «Обзор».')

    work = docs.copy()
    file_col = next((c for c in ['Файл', 'file_name', 'filename', 'name'] if c in work.columns), None)
    section_col = next((c for c in ['Раздел', 'document_type', 'section', 'doc_type'] if c in work.columns), None)
    if not file_col:
        work['_display_file'] = [f'Документ {i + 1}' for i in range(len(work))]
        file_col = '_display_file'
    if not section_col:
        work['_display_section'] = 'Не определён'
        section_col = '_display_section'

    families = sorted(work[section_col].fillna('Не определён').astype(str).unique())
    left, right = st.columns([0.78, 2.15], gap='large')

    with left:
        st.markdown('#### Разделы проекта')
        selected_family = st.selectbox('Раздел', ['Все разделы'] + families, label_visibility='collapsed')
        filtered = work if selected_family == 'Все разделы' else work[work[section_col].astype(str) == selected_family]
        labels = [f"{r.get(section_col, '—')} · {r.get(file_col, '—')}" for _, r in filtered.iterrows()]
        if not labels:
            return empty('В выбранном разделе документы отсутствуют.')
        selected_label = st.radio('Документы', labels, label_visibility='collapsed')
        selected = filtered.iloc[labels.index(selected_label)]
        st.caption(f'Показано документов: {len(filtered)} из {len(work)}')

    with right:
        st.markdown('#### Карточка документа')
        c1, c2, c3 = st.columns(3)
        with c1:
            card('Раздел', _first_present(selected, [section_col]), 'Определённый тип документа')
        with c2:
            card('Страниц', _first_present(selected, ['Страниц', 'pages', 'page_count']), 'Объём документа')
        with c3:
            card('Статус', _first_present(selected, ['Статус', 'status'], 'Проанализирован'), 'Результат обработки', 'ok')

        st.markdown(f"### {_first_present(selected, [file_col])}")
        details = []
        for label, candidates in [
            ('Размер', ['Размер', 'Размер, МБ', 'size_mb', 'file_size']),
            ('XML-схема', ['XML-схема', 'xml_schema', 'schema_version']),
            ('Таблицы', ['Распознано страниц с таблицами', 'table_pages', 'tables_count']),
            ('Найдено объектов', ['objects_count', 'object_count']),
            ('Найдено характеристик', ['findings_count', 'characteristics_count']),
        ]:
            value = _first_present(selected, candidates, None)
            if value is not None:
                details.append({'Показатель': label, 'Значение': value})
        if details:
            st.dataframe(pd.DataFrame(details), width='stretch', hide_index=True)
        else:
            st.info('Для документа доступны только основные сведения о составе комплекта.')

        if st.session_state.expert_mode:
            with st.expander('Диагностика документа'):
                diagnostic = pd.DataFrame({'Поле': selected.index.astype(str), 'Значение': selected.astype(str).values})
                st.dataframe(diagnostic, width='stretch', hide_index=True)
