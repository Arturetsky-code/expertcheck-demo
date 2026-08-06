from __future__ import annotations
from datetime import datetime
import pandas as pd
import streamlit as st
from studio.components import hero, card, section, empty, project_status_bar, timeline
from studio.data import excel_report
from core.project_upload import DOCUMENT_TYPE_OPTIONS, apply_document_type_overrides, prepare_uploads
from core.report_engine import build_decision_report
from core.ai_gateway import provider_for_role
from studio.pages.documents import render as render_documents
from studio.pages.completeness import render as render_completeness


def _upload(ctx):
    hero(
        'Новая проверка проекта',
        'Загрузите PDF, XML или ZIP. Сначала ExpertCheck проверит состав комплекта, затем запустит инженерный анализ.',
        '1 Загрузка · 2 Состав · 3 Анализ · 4 Результат',
    )
    with st.container(border=True):
        name = st.text_input('Наименование проекта', value=st.session_state.project_name)
        uploads = st.file_uploader('Комплект проекта', type=['pdf', 'xml', 'zip'], accept_multiple_files=True)
        prepared = []
        edited = pd.DataFrame()
        confirmed = False
        errors = []
        if uploads:
            upload_status = st.status('Подготовка комплекта', expanded=False)
            upload_status.write('Проверяем архивы, форматы и структуру файлов.')
            package = prepare_uploads(uploads)
            prepared = package.files
            errors = package.errors
            upload_status.update(label=f'Подготовлено файлов: {len(prepared)}', state='complete', expanded=False)
            for item in errors:
                st.error(item)
            for item in package.warnings:
                st.warning(item)
            if prepared:
                summary = package.package_summary
                c1, c2, c3 = st.columns(3)
                c1.metric('Файлов', int(summary.get('files', 0)))
                c2.metric('Общий объём', f"{float(summary.get('total_bytes', 0))/1048576:.1f} МБ")
                c3.metric('XML', ', '.join(summary.get('identity', {}).get('xml_schemas', [])) or 'нет')
                with st.expander('Проверить состав и типы документов', expanded=True):
                    edited = st.data_editor(
                        pd.DataFrame(package.inventory),
                        hide_index=True,
                        width='stretch',
                        disabled=['ID', 'Файл', 'Формат', 'Семейство', 'Размер, МБ', 'Источник', 'Статус'],
                        column_config={
                            'Предполагаемый раздел': st.column_config.SelectboxColumn(
                                'Раздел', options=DOCUMENT_TYPE_OPTIONS, required=True
                            )
                        },
                        key='studio3_upload_inventory',
                    )
                    comp = summary.get('completeness', {})
                    available = comp.get('available_checks', [])
                    limits = comp.get('limitations', [])
                    if available:
                        st.success('Доступно: ' + '; '.join(available))
                    if limits:
                        st.info('Ограничения: ' + '; '.join(limits))
                confirmed = st.checkbox('Состав загруженного комплекта проверен', key='studio3_package_confirmed')
        if st.button(
            'Запустить проверку',
            type='primary',
            width='stretch',
            disabled=not prepared or bool(errors) or not confirmed,
        ):
            files = apply_document_type_overrides(prepared, edited.to_dict('records'))
            progress_bar = st.progress(0, text='Подготовка комплекта')
            stage_text = st.empty()
            detail_text = st.empty()

            def update_progress(value, stage, detail=''):
                progress_bar.progress(value, text=f'{value}%')
                stage_text.markdown(f'**{stage}**')
                detail_text.caption(detail or 'Выполняется обработка проекта')

            ai_level = str(st.session_state.get('ai_pipeline_level') or 'Отключён')
            ai_provider = None
            if ai_level != 'Отключён':
                ai_provider = provider_for_role('extraction', st.session_state, st.secrets)
            ai_options = {'level': {
                'Отключён': 'off', 'Умный автоматический': 'extended', 'Помощник': 'helper',
                'Расширенный': 'extended', 'Максимальный': 'maximum',
            }.get(ai_level, 'helper'), 'provider': ai_provider}
            try:
                st.session_state.result = ctx.analyze(files, ctx.config_dir, progress_callback=update_progress, ai_options=ai_options)
            except TypeError:
                update_progress(15, 'Подготовка комплекта', 'Запускаем обработку документов')
                st.session_state.result = ctx.analyze(files, ctx.config_dir)
            st.session_state.project_name = name.strip() or 'Новый проект'
            st.session_state.analysis_time = datetime.now().isoformat(timespec='minutes')
            st.session_state.completeness_user_confirmed = False
            st.session_state.completeness_decisions = {}
            st.session_state.object_registry_confirmed = False
            st.session_state.object_assembly_rows = []
            st.session_state.checklist_run = None
            st.session_state.checklist_user_results = {}
            update_progress(100, 'Проверка завершена', 'Переходим к подтверждению состава объектов')
            st.session_state.page = 'Состав объектов'
            st.rerun()


def _dashboard(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    report = build_decision_report(docs.to_dict('records'), comparisons.to_dict('records'))
    summary = report['summary']
    confirmed = bool(st.session_state.get('completeness_user_confirmed'))
    project_status_bar(
        st.session_state.project_name,
        'Проверка завершена',
        f"Комплектность: {'подтверждена' if confirmed else 'не подтверждена'}",
        f"Объекты: {summary['objects']}",
        f"ТЭП: {summary['checks']}",
    )
    object_gate=bool(st.session_state.get('object_registry_confirmed'))
    cols = st.columns(4)
    with cols[0]:
        card('Комплектность', 'Подтверждена' if confirmed else 'Требует решения', 'Состав проектной документации', 'ok' if confirmed else 'warn')
    with cols[1]:
        card('Состав объектов', 'Подтверждён' if object_gate else 'Требует проверки', 'Quality Gate перед сверкой', 'ok' if object_gate else 'warn')
    with cols[2]:
        card('Межраздельная сверка', summary['checks'] if object_gate else 'Заблокирована', f"Совпадает: {summary['confirmed']}" if object_gate else 'Сначала подтвердите объекты', 'ok' if object_gate else 'info')
    with cols[3]:
        card('Требует внимания', summary['requires_attention'] if object_gate else '—', f"Высокий риск: {summary['high_priority']}" if object_gate else 'Выводы ещё не формируются', 'bad' if object_gate and summary['high_priority'] else 'warn')
    section('Quality Gate','ExpertCheck формирует выводы только после подтверждения состава проектируемых объектов.')
    q1,q2,q3=st.columns(3)
    with q1: card('1. Документы','Готово',f'Загружено: {len(docs)}','ok')
    with q2: card('2. Объекты','Готово' if object_gate else 'Требуется', 'Пользовательское подтверждение', 'ok' if object_gate else 'warn')
    with q3: card('3. Сверка ТЭП','Доступна' if object_gate else 'Заблокирована','Только по Trusted Object Registry','ok' if object_gate else 'info')

    tab_summary, tab_documents, tab_completeness = st.tabs(['Сводка', 'Документы', 'Комплектность'])
    with tab_summary:
        section('Что требует внимания', 'Показаны только результаты, по которым требуется инженерное решение.')
        problems = report['problems']
        if not problems:
            st.success('Существенные расхождения не выявлены либо пока недостаточно сопоставимых данных.')
        else:
            for idx, item in enumerate(problems[:8], 1):
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"**{idx}. {item['object']} · {item['parameter']}**")
                        st.caption(f"{item['status']} · {item['priority']} приоритет")
                        if item['values']:
                            st.write(item['values'])
                        st.write(item['explanation'])
                    with c2:
                        st.metric('Приоритет', item['priority'])
        section('История проекта', 'Последние действия в текущей сессии.')
        events = [('Создано рабочее пространство', 'готово')]
        if not docs.empty:
            events.append((f'Загружено документов: {len(docs)}', 'готово'))
        if st.session_state.analysis_time:
            events.append((f'Проверка выполнена: {st.session_state.analysis_time}', 'готово'))
        if confirmed:
            events.append(('Состав проекта подтверждён пользователем', 'готово'))
        timeline(events)
    with tab_documents:
        render_documents(ctx)
    with tab_completeness:
        render_completeness(ctx)


def render(ctx):
    docs = ctx.data[0]
    if docs.empty:
        _upload(ctx)
    else:
        _dashboard(ctx)
