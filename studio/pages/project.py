from __future__ import annotations
from datetime import datetime
import pandas as pd
from core.display_localization import parameter_label, status_label
import streamlit as st
from studio.components import hero, card, section, empty, project_status_bar, timeline
from studio.data import excel_report
from core.project_upload import DOCUMENT_TYPE_OPTIONS, apply_document_type_overrides, prepare_uploads
from core.review_profiles import filter_prepared_files, PROFILES
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
        mode_label=st.radio(
            'Режим проверки',
            ['Быстрая','Расширенная — рекомендуется','Полная'],
            index=1,horizontal=True,key='project_review_mode',
            help='Быстрая — основные разделы ПД; Расширенная — ПД + ИИ + ключевая ИРД; Полная — весь комплект.'
        )
        mode_code={'Быстрая':'quick','Расширенная — рекомендуется':'extended','Полная':'full'}[mode_label]
        st.caption({
            'quick':'Основные разделы ПД: быстрее, подходит для ранней предпроверки.',
            'extended':'Рекомендуемый режим перед экспертизой: ПД + ИИ + ключевая ИРД.',
            'full':'Максимальная глубина. Для больших комплектов обработка может занимать существенно больше времени.'
        }[mode_code])
        upload_mode = st.radio(
            'Способ загрузки комплекта',
            ['ZIP-архив — рекомендуется', 'Отдельные PDF/XML'],
            index=0, horizontal=True, key='project_upload_transport_mode',
            help='Для комплектов из нескольких томов ZIP надёжнее: браузер выполняет одну передачу вместо множества параллельных загрузок.'
        )
        if upload_mode.startswith('ZIP'):
            st.caption('Рекомендуемый режим для полного проекта: упакуйте PDF/XML в один ZIP без пароля. Структура папок внутри архива сохраняется.')
            zip_upload = st.file_uploader(
                'Комплект проекта — ZIP', type=['zip'], accept_multiple_files=False,
                key='project_zip_uploader',
            )
            uploads = [zip_upload] if zip_upload is not None else []
        else:
            st.caption('Резервный режим. При загрузке большого количества файлов Streamlit/облачный прокси может прервать параллельные передачи. Если появляются красные значки «!», используйте ZIP-режим.')
            uploads = st.file_uploader(
                'Комплект проекта — отдельные файлы', type=['pdf', 'xml'],
                accept_multiple_files=True, key='project_multi_uploader',
            ) or []
        prepared = []
        edited = pd.DataFrame()
        confirmed = False
        errors = []
        if uploads:
            total_upload_bytes=sum(int(getattr(x,'size',0) or 0) for x in uploads)
            st.caption(f'Получено браузером: {len(uploads)} файлов · {total_upload_bytes/1048576:.1f} МБ')
            st.progress(100,text=f'Загрузка в приложение: 100% · {len(uploads)} из {len(uploads)} файлов')
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
            files, skipped_by_mode = filter_prepared_files(files,mode_code)
            if skipped_by_mode:
                st.info(f'Режим «{mode_label}»: {len(skipped_by_mode)} файлов оставлены вне текущего анализа. Их можно проверить позднее без изменения исходного комплекта.')
            if not files:
                st.error('Для выбранного режима не найдено файлов для анализа.')
                st.stop()
            st.markdown('### Анализ проекта')
            progress_bar = st.progress(0, text=f'Анализ: 0% · файлов в программе: {len(files)}')
            stage_text = st.empty()
            detail_text = st.empty()

            def update_progress(value, stage, detail=''):
                progress_bar.progress(value, text=f'Анализ проекта: {value}%')
                stage_text.markdown(f'**Этап: {stage}**')
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
            st.session_state.review_mode = mode_code
            st.session_state.review_mode_label = mode_label
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

    tab_summary, tab_model, tab_documents, tab_completeness, tab_assignment, tab_ird = st.tabs(['Сводка', 'Модель проекта', 'Документы', 'Комплектность', 'Задание на проектирование', 'Исходные документы'])
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
    with tab_model:
        first_doc = docs.iloc[0].to_dict() if not docs.empty else {}
        model=first_doc.get('project_understanding') or {}
        quality=first_doc.get('project_understanding_quality') or {}
        section('Модель понимания проекта','Проверяем, насколько надёжно ExpertCheck связал объекты с их характеристиками и источниками. Неоднозначные сведения не используются как доказательство расхождения.')
        if not model.get('objects'):
            st.info('Модель проекта не сформирована.')
        else:
            c1,c2,c3,c4=st.columns(4)
            c1.metric('Объектов',quality.get('objects',0))
            c2.metric('С показателями',quality.get('objects_with_properties',0))
            c3.metric('Неразрешённых привязок',quality.get('unresolved_properties',0))
            c4.metric('Качество привязки',str(quality.get('binding_precision_proxy_pct',0))+'%')
            if quality.get('quality_status')=='Требует внимания':
                st.warning('Качество объектно-параметрической привязки требует проверки. ExpertCheck намеренно не формирует часть межраздельных выводов.')
            else:
                st.success('Модель проекта пригодна для дальнейшей межраздельной проверки с установленными ограничениями.')
            rows=[]
            for obj in model.get('objects') or []:
                for prop in obj.get('property_summary') or []:
                    rows.append({
                      'Объект':obj.get('name'),'Позиция по ГП':obj.get('position') or '—',
                      'Тип объекта':obj.get('object_type'),'Показатель':prop.get('parameter_name'),
                      'Код показателя':parameter_label(prop.get('parameter_code')),'Разделы':', '.join(prop.get('sections') or []),
                      'Доказательств':prop.get('evidence_count',0),
                      'Профильный источник':'Да' if prop.get('owner_evidence') else 'Нет',
                      'Конфликт значений':'Да' if prop.get('value_conflict') else 'Нет',
                    })
            if rows:
                st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
            with st.expander('Принцип формирования модели',expanded=False):
                st.write('Показатель не может создавать объект. Сначала объект должен попасть в подтверждённый реестр проекта; только после этого площадь, объём, высота, мощность, расход и другие характеристики могут быть привязаны к нему. Неоднозначная привязка остаётся нерешённой и не используется для автоматического замечания.')

            drawing=first_doc.get('drawing_intelligence_v2') or {}
            dsum=drawing.get('summary') or {}
            if dsum.get('documents'):
                st.markdown('#### Понимание чертежей')
                d1,d2,d3,d4=st.columns(4)
                d1.metric('Объектных комплектов',dsum.get('objects',0))
                d2.metric('Чертёжных листов',dsum.get('sheets',0))
                d3.metric('Экспликаций помещений',dsum.get('room_schedules',0))
                d4.metric('Помещений',dsum.get('rooms',0))
                st.caption('Площади помещений и итог экспликации хранятся как локальные показатели чертежа и не приравниваются автоматически к общей площади или площади застройки объекта.')
                with st.expander('Экспликации помещений и доказательства',expanded=False):
                    dr=[]
                    for sched in drawing.get('room_schedules') or []:
                        dr.append({
                            'Объект':sched.get('parent_object'),'Позиция':sched.get('position') or '—','Страница':sched.get('page'),
                            'Помещений':len(sched.get('rows') or []),'Итого по экспликации, м²':sched.get('reported_total'),
                            'Сумма строк, м²':sched.get('calculated_total'),'Проверка суммы':'Совпадает' if sched.get('total_matches_rows') else 'Требует проверки',
                            'Привязка владельца':'По основной надписи' if sched.get('owner_binding')=='TITLE_BLOCK_EXACT' else 'Требует проверки',
                        })
                    if dr:
                        st.dataframe(pd.DataFrame(dr),hide_index=True,width='stretch')
                    if dsum.get('withheld_bindings'):
                        st.info(f"Неоднозначных привязок листов удержано без догадки: {dsum.get('withheld_bindings')}")

    with tab_documents:
        render_documents(ctx)
    with tab_completeness:
        render_completeness(ctx)

    with tab_assignment:
        section('Соответствие Заданию на проектирование','Требования Задания извлекаются отдельно и сопоставляются с объектами, ТЭП и найденными проектными решениями.')
        first_doc = docs.iloc[0].to_dict() if not docs.empty else {}
        assignment_rows=first_doc.get('assignment_compliance') or []
        assignment_summary=first_doc.get('assignment_compliance_summary') or {}
        if not assignment_rows:
            st.info('Задание на проектирование не распознано в комплекте либо машинно-интерпретируемые требования не извлечены. При необходимости укажите тип документа «Задание на проектирование» на этапе загрузки.')
        else:
            a1,a2,a3,a4=st.columns(4)
            a1.metric('Требований',assignment_summary.get('total',len(assignment_rows)))
            a2.metric('Соответствуют',assignment_summary.get('compliant',0))
            a3.metric('Отклонения',assignment_summary.get('deviation',0))
            a4.metric('Требуют проверки / не проверены',assignment_summary.get('unconfirmed',0)+assignment_summary.get('semantic',0)+assignment_summary.get('not_checked',0))
            show=pd.DataFrame([{
                'Строка':x.get('source_row') or '—',
                'Раздел / вопрос':x.get('source_row_title') or '—',
                'Тип проверки':x.get('requirement_type') or '—',
                'Требование':x.get('requirement_text'),
                'Объект':x.get('object_name') or '—',
                'Показатель':parameter_label(x.get('parameter_code')) if x.get('parameter_code') else '—',
                'Требуемое значение':(str(x.get('required_value'))+' '+str(x.get('unit') or '')).strip() if x.get('required_value') is not None else '—',
                'Результат':x.get('status'),
                'Достоверность привязки':f"{float(x.get('match_confidence') or 0)*100:.0f}%",
                'Ожидаемое доказательство':x.get('expected_evidence') or '',
                'Основание вывода':x.get('decision_basis') or '',
                'Источник':f"{x.get('source_document')}, стр. {x.get('page')}",
                'Доказательства':' | '.join(x.get('evidence') or []),
                'Качество доказательства':x.get('evidence_quality_state') or '—',
                'Направленных кандидатов':len(x.get('directed_evidence_candidates') or []),
            } for x in assignment_rows])
            st.dataframe(show,hide_index=True,width='stretch')
            st.caption('Автоматическая проверка не подменяет инженерную интерпретацию Задания. Смысловые требования без структурированного параметра остаются на проверку специалисту.')

    with tab_ird:
        section('Исходные и подтверждающие документы', 'Автоматический контроль наличия ключевых исходных материалов. Статус «Требует проверки» означает, что применимость и актуальность необходимо подтвердить специалисту.')
        first_doc = docs.iloc[0].to_dict() if not docs.empty else {}
        audit = first_doc.get('mandatory_document_audit') or []
        if audit:
            show = pd.DataFrame([{'Документ / сведения':x.get('title'),'Статус':x.get('status'),'Применимость':x.get('applicability'),'Что проверить':x.get('recommendation')} for x in audit])
            st.dataframe(show, hide_index=True, width='stretch')
        else:
            st.info('Автоматический аудит исходных документов пока не сформирован.')
        validity_details = first_doc.get('normative_validity_audit') or []
        validity = first_doc.get('normative_reference_summary') or validity_details
        validity_summary = first_doc.get('normative_validity_summary') or {}
        if validity:
            statuses=validity_summary.get('statuses') or {}
            st.markdown('#### Проверка актуальности НТД')
            c1,c2,c3,c4=st.columns(4)
            c1.metric('Уникальных НТД',len(validity))
            c2.metric('Действует',statuses.get('Действует',0)+statuses.get('Действует с изменениями',0))
            c3.metric('Требуют верификации',statuses.get('Требует верификации',0)+statuses.get('Возможна устаревшая редакция',0))
            c4.metric('Устаревшие редакции',validity_summary.get('outdated_editions',0))
            show=pd.DataFrame([{
                'НТД':x.get('reference'),'Статус':x.get('status'),
                'Редакция':(x.get('edition_assessment') or {}).get('edition_status',''),
                'Актуальная замена':(x.get('edition_assessment') or {}).get('current_reference',''),
                'Упоминаний':x.get('mentions',1),'Документов':x.get('documents_count',1 if x.get('document') else 0),
                'Где встречается':'; '.join(x.get('pages') or []) if isinstance(x.get('pages'),list) else f"{x.get('document') or ''}, стр. {x.get('page') or ''}",
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
            try:
                from core.normative_intelligence import NormativeIntelligence
                nsum=NormativeIntelligence(ctx.config_dir/'knowledge').summary()
                with st.expander('Качество нормативной базы', expanded=False):
                    n1,n2,n3,n4=st.columns(4)
                    n1.metric('Документов в ядре',nsum.get('documents',0))
                    n2.metric('Требований',nsum.get('requirements',0))
                    n3.metric('Пунктов верифицировано',nsum.get('clause_verified_requirements',0))
                    n4.metric('Категоричные выводы разрешены',nsum.get('categorical_requirements',0))
                    st.caption('Неверифицированное требование используется для маршрутизации и предварительной проверки, но не должно формировать доказанное нормативное нарушение.')
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
