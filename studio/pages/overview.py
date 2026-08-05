from __future__ import annotations
from datetime import datetime
import pandas as pd
import streamlit as st
from studio.components import hero,card,section
from studio.data import status_group,excel_report
from core.project_upload import DOCUMENT_TYPE_OPTIONS,apply_document_type_overrides,prepare_uploads

def render(ctx):
    docs,findings,comparisons,registry,passports,metrics,eng=ctx.data
    if docs.empty:
        hero('Новая проверка проекта','Загрузите PDF, XML или ZIP-комплект. Перед запуском можно проверить состав и исправить типы документов.','01 · Загрузка → 02 · Проверка состава → 03 · Анализ → 04 · Результат')
        with st.container(border=True):
            name=st.text_input('Наименование проекта',value=st.session_state.project_name)
            uploads=st.file_uploader('Комплект проекта',type=['pdf','xml','zip'],accept_multiple_files=True)
            prepared=[];edited=pd.DataFrame();confirmed=False;errors=[]
            if uploads:
                upload_status=st.status('Подготавливаем загруженный комплект…',expanded=False)
                upload_status.write('Проверяем архивы, форматы и внутреннюю структуру файлов.')
                package=prepare_uploads(uploads);prepared=package.files;errors=package.errors
                upload_status.update(label=f'Комплект подготовлен: {len(prepared)} файлов',state='complete',expanded=False)
                for x in errors:st.error(x)
                for x in package.warnings:st.warning(x)
                if prepared:
                    s=package.package_summary;c1,c2,c3=st.columns(3);c1.metric('Файлов',int(s.get('files',0)));c2.metric('Общий объём',f"{float(s.get('total_bytes',0))/1048576:.1f} МБ");c3.metric('XML',', '.join(s.get('identity',{}).get('xml_schemas',[])) or 'нет')
                    section('Состав комплекта','Проверьте классификацию документов до запуска анализа.')
                    edited=st.data_editor(pd.DataFrame(package.inventory),hide_index=True,use_container_width=True,disabled=['ID','Файл','Формат','Семейство','Размер, МБ','Источник','Статус'],column_config={'Предполагаемый раздел':st.column_config.SelectboxColumn('Раздел',options=DOCUMENT_TYPE_OPTIONS,required=True)},key='studio_upload_inventory')
                    comp=s.get('completeness',{});available=comp.get('available_checks',[]);limits=comp.get('limitations',[])
                    if available:st.success('Доступно: '+'; '.join(available))
                    if limits:st.info('Ограничения: '+'; '.join(limits))
                    confirmed=st.checkbox('Состав комплекта проверен',key='studio_package_confirmed')
            if st.button('Запустить проверку проекта',type='primary',use_container_width=True,disabled=not prepared or bool(errors) or not confirmed):
                files=apply_document_type_overrides(prepared,edited.to_dict('records'))
                progress_box=st.container()
                with progress_box:
                    st.markdown('<div class="ec-progress-panel"><div class="ec-progress-title">Анализ проектной документации</div><div class="ec-progress-detail">Не закрывайте страницу до завершения обработки.</div></div>',unsafe_allow_html=True)
                    progress_bar=st.progress(0,text='Подготовка комплекта')
                    stage_text=st.empty()
                    detail_text=st.empty()
                    file_text=st.caption(f'Документов в обработке: {len(files)}')
                def update_progress(value,stage,detail=''):
                    progress_bar.progress(value,text=f'{value}%')
                    stage_text.markdown(f'**{stage}**')
                    detail_text.caption(detail or 'Выполняется обработка проекта')
                try:
                    st.session_state.result=ctx.analyze(files,ctx.config_dir,progress_callback=update_progress)
                    st.session_state.project_name=name.strip() or 'Новый проект'
                    st.session_state.analysis_time=datetime.now().isoformat(timespec='minutes')
                    st.session_state.completeness_user_confirmed=False
                    st.session_state.completeness_decisions={}
                    st.session_state.completeness_user_confirmed=False
                    st.session_state.completeness_decisions={}
                    progress_bar.progress(100,text='100%')
                    stage_text.markdown('**Проверка завершена**')
                    detail_text.caption('Результаты подготовлены. Открываем рабочее пространство проекта.')
                except TypeError:
                    # Совместимость с более ранним Core без callback.
                    update_progress(15,'Подготовка комплекта','Запускаем обработку документов')
                    st.session_state.result=ctx.analyze(files,ctx.config_dir)
                    st.session_state.project_name=name.strip() or 'Новый проект'
                    st.session_state.analysis_time=datetime.now().isoformat(timespec='minutes')
                    update_progress(100,'Проверка завершена','Результаты подготовлены')
                st.rerun()
        return
    quality_data=docs.iloc[0].get('dem_model_quality') if 'dem_model_quality' in docs else {};quality=int(round(float((quality_data or {}).get('model_quality_index',0))*100))
    hero(st.session_state.project_name,'Проверка завершена. Ниже показаны результаты, влияющие на инженерное решение.',f'Индекс цифровой модели: {quality}% · Последняя проверка: {st.session_state.analysis_time or "—"}')
    cols=st.columns(5)
    with cols[0]:card('Документы',len(docs),'PDF и XML в комплекте')
    with cols[1]:card('Объекты',len(registry),'Позиции консолидированного реестра')
    with cols[2]:card('Требуют внимания',metrics['bad']+metrics['warn'],'Расхождения и неподтверждённые сведения','bad' if metrics['bad'] else 'warn')
    with cols[3]:card('Подтверждено',metrics['ok'],'Согласованные проверки','ok')
    with cols[4]:card('Комплектность','Подтверждена' if st.session_state.get('completeness_user_confirmed') else 'Не подтверждена','Откройте раздел «Комплектность»','ok' if st.session_state.get('completeness_user_confirmed') else 'warn')
    section('Состояние проекта','Краткая сводка без служебных полей.')
    left,right=st.columns([1.45,1])
    with left:
        p=comparisons.copy()
        if not p.empty and 'status' in p:p['_group']=p['status'].map(status_group);p=p[p['_group'].isin(['bad','warn'])]
        if p.empty:st.success('Существенные расхождения не выявлены либо недостаточно сопоставимых данных.')
        else:
            for _,r in p.head(8).iterrows():
                st.markdown(f"**{r.get('object') or 'Объект не определён'} · {r.get('parameter_name') or r.get('rule_name') or 'Проверка'}**  \n{r.get('document_values') or r.get('documents') or ''}  \n`{r.get('status') or 'Требует проверки'}`")
    with right:
        st.info(f"Инженерных характеристик: **{len(eng)}**\n\nМежраздельных проверок: **{metrics['total']}**\n\nРеестровых позиций: **{len(registry)}**")
        if st.button('Новая проверка',use_container_width=True):st.session_state.result=None;st.session_state.analysis_time=None;st.rerun()
        st.download_button('Скачать отчёт Excel',data=excel_report(st.session_state.project_name,ctx.version,docs,findings,comparisons),file_name='ExpertCheck_report.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True)
