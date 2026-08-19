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
            st.caption(f'Выбрано файлов для загрузки: {len(uploads)}')
            upload_status = st.status('Подготовка комплекта', expanded=True)
            upload_status.write('Проверяем архивы, форматы и структуру файлов.')
            try:
                package = prepare_uploads(uploads)
            except Exception as exc:
                upload_status.update(label='Не удалось подготовить комплект', state='error', expanded=True)
                st.error(f'Ошибка подготовки загруженных файлов: {type(exc).__name__}: {exc}')
                package = None
            if package is not None:
                prepared = package.files
                errors = package.errors
                upload_status.update(
                    label=f'Подготовлено файлов: {len(prepared)} из {len(uploads)} загруженных элементов',
                    state='complete' if prepared else 'error',
                    expanded=not bool(prepared),
                )
                for item in errors:
                    st.error(item)
                for item in package.warnings:
                    st.warning(item)
                if not prepared:
                    st.error('Ни один PDF/XML не был подготовлен. Проверьте размер файлов, формат ZIP и журналы выше.')
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
            }.get(ai_level, 'helper'), 'provider': ai_provider, 'learning_examples': st.session_state.get('object_learning_examples', [])}
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
            # The sidebar radio with key 'page' already exists in this run.
            # Defer navigation until the next rerun to comply with Streamlit state rules.
            st.session_state['_navigate_to'] = 'Состав объектов'
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

    tab_summary, tab_documents, tab_completeness, tab_ird = st.tabs(['Сводка', 'Документы', 'Комплектность', 'Исходные документы'])
    with tab_summary:
        first_doc = docs.iloc[0].to_dict() if not docs.empty else {}
        pp87_profile = first_doc.get('pp87_project_profile') or {}
        if pp87_profile:
            with st.container(border=True):
                st.markdown('**Профиль проверки по ПП №87**')
                st.write(pp87_profile.get('profile') or 'Тип требует подтверждения')
                appendices=pp87_profile.get('appendices') or []
                if appendices:
                    st.caption('Применимые специальные приложения: ' + '; '.join(x.get('title','') for x in appendices if x.get('title')))
                else:
                    st.caption('Специальные приложения автоматически не определены.')
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

    with tab_ird:
        section('Исходные и подтверждающие документы', 'Автоматический контроль наличия ключевых исходных материалов. Статус «Требует проверки» означает, что применимость и актуальность необходимо подтвердить специалисту.')
        first_doc = docs.iloc[0].to_dict() if not docs.empty else {}
        audit = first_doc.get('mandatory_document_audit') or []
        if audit:
            show = pd.DataFrame([{'Документ / сведения':x.get('title'),'Статус':x.get('status'),'Применимость':x.get('applicability'),'Что проверить':x.get('recommendation')} for x in audit])
            st.dataframe(show, hide_index=True, width='stretch')
        else:
            st.info('Автоматический аудит исходных документов пока не сформирован.')
        validity = first_doc.get('normative_validity_audit') or []
        validity_summary = first_doc.get('normative_validity_summary') or {}
        if validity:
            statuses=validity_summary.get('statuses') or {}
            st.markdown('#### Проверка актуальности НТД')
            c1,c2,c3,c4=st.columns(4)
            c1.metric('Найдено ссылок',validity_summary.get('references',len(validity)))
            c2.metric('Действует',statuses.get('Действует',0)+statuses.get('Действует с изменениями',0))
            c3.metric('Требуют верификации',statuses.get('Требует верификации',0)+statuses.get('Возможна устаревшая редакция',0))
            c4.metric('Устаревшие редакции',validity_summary.get('outdated_editions',0))
            show=pd.DataFrame([{
                'НТД':x.get('reference'),'Статус':x.get('status'),
                'Редакция':(x.get('edition_assessment') or {}).get('edition_status',''),
                'Актуальная замена':(x.get('edition_assessment') or {}).get('current_reference',''),
                'Файл':x.get('document'),'Стр.':x.get('page'),
                'Риск влияния':x.get('impact_risk'),
                'Приоритет базы':x.get('verification_priority'),
                'Замечаний экспертизы':x.get('expert_occurrences',0),
                'Проверять по':x.get('official_source')
            } for x in validity])
            st.dataframe(show,hide_index=True,width='stretch')
            try:
                from core.normative_verification import NormativeVerificationEngine
                verification_engine=NormativeVerificationEngine(ctx.config_dir/'knowledge')
                qsum=verification_engine.queue_summary()
                with st.expander('Очередь верификации нормативной базы',expanded=False):
                    q1,q2,q3=st.columns(3)
                    q1.metric('Всего в реестре',qsum.get('total',0))
                    q2.metric('Проверено',qsum.get('verified',0))
                    q3.metric('P1 ожидают проверки',qsum.get('p1_pending',0))
                    queue_rows=verification_engine.queue(pending_only=True,limit=30)
                    if queue_rows:
                        st.dataframe(pd.DataFrame(queue_rows),hide_index=True,width='stretch')
            except Exception:
                pass
        else:
            refs = first_doc.get('normative_reference_audit') or []
            if refs:
                with st.expander(f'Нормативные ссылки, требующие контроля актуальности ({len(refs)})'):
                    st.dataframe(pd.DataFrame(refs), hide_index=True, width='stretch')


def render(ctx):
    if not st.session_state.get('active_project_id'):
        user=st.session_state.get('auth_user') or {}
        if not user.get('id'):
            st.error('Сессия пользователя не определена.')
            return
        st.info('Сначала создайте или откройте проект в разделе «Мои проекты».')
        if st.button('Перейти в Мои проекты', type='primary', key='go_workspace_from_project'):
            st.session_state['_navigate_to']='Мои проекты'
            st.rerun()
        return
    docs = ctx.data[0]
    if docs.empty:
        _upload(ctx)
    else:
        _dashboard(ctx)
