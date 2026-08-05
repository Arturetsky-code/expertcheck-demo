from __future__ import annotations

import pandas as pd
import streamlit as st

from core.checklist_engine import ChecklistEngine
from studio.components import card, empty, section


def _document_options(docs: pd.DataFrame) -> list[str]:
    if docs.empty:
        return []
    preferred=['Файл','Имя файла','name','filename']
    section_cols=['Раздел','Тип документа','document_type','family']
    labels=[]
    for _,row in docs.iterrows():
        file_name=next((str(row.get(c)) for c in preferred if c in docs.columns and str(row.get(c) or '').strip()),'Документ')
        section_name=next((str(row.get(c)) for c in section_cols if c in docs.columns and str(row.get(c) or '').strip()),'Не определён')
        labels.append(f'{section_name} · {file_name}')
    return labels


def render(ctx):
    docs,findings,comparisons=ctx.data[:3]
    section('Проверка ПД по чек-листам','Независимая проверка выбранного раздела по выбранному корпоративному чек-листу. Она не зависит от подтверждения объектного реестра.')
    if docs.empty:
        return empty('Сначала загрузите комплект проектной документации.')
    engine=ChecklistEngine(ctx.config_dir/'knowledge'/'checklist_catalog.json')
    if not engine.items:return empty('Каталог чек-листов не загружен.')

    left,right=st.columns(2,gap='large')
    sections=engine.sections()
    with left:
        st.markdown('### Чек-лист')
        checklist_files=engine.checklist_files()
        checklist=st.selectbox('Выберите чек-лист',checklist_files,key='workspace_checklist_file')
        recommended=engine.primary_section(checklist)
        st.caption(f'Рекомендуемый раздел: {recommended}')
    with right:
        st.markdown('### Документация')
        selected_section=st.selectbox('Выберите раздел ПД',sections,index=sections.index(recommended) if recommended in sections else 0,key='workspace_checklist_section')
        document_labels=_document_options(docs)
        matching=[x for x in document_labels if x.startswith(selected_section+' ·')]
        selected_docs=st.multiselect('Документы для проверки',document_labels,default=matching,key='workspace_checklist_documents')
        if not selected_docs:
            st.warning('Выберите хотя бы один документ. Проверка не будет запущена без явного выбора.')

    mode=st.radio('Режим проверки',['Быстрая','Полная','Экспертная'],horizontal=True,key='workspace_checklist_mode',help='Быстрая — пункты A; Полная — A и B; Экспертная — A, B и C.')
    if st.button('Проверить выбранный раздел',type='primary',width='stretch',disabled=not selected_docs):
        st.session_state.checklist_run={'section':selected_section,'source_file':checklist,'mode':mode,'documents':selected_docs}
        st.session_state.checklist_user_results={}
        st.rerun()

    run=st.session_state.get('checklist_run')
    if not run:
        st.info('Выберите чек-лист и документы, затем запустите проверку.')
        return
    if run.get('source_file')!=checklist or run.get('section')!=selected_section or run.get('mode')!=mode:
        st.info('Параметры изменены. Нажмите «Проверить выбранный раздел», чтобы получить новый результат.')
        return

    selected_set=set(run.get('documents') or [])
    doc_records=[]
    labels=_document_options(docs)
    for label,(_,row) in zip(labels,docs.iterrows()):
        if label in selected_set: doc_records.append(row.to_dict())
    results=engine.evaluate(doc_records,comparisons.to_dict('records'),findings.to_dict('records'),source_file=checklist,section=selected_section)
    levels={'Быстрая':{'A'},'Полная':{'A','B'},'Экспертная':{'A','B','C'}}[mode]
    results=[r for r in results if r.get('automation_level') in levels]
    if not results:return empty('Для выбранного сочетания раздела, чек-листа и режима нет пунктов.')

    summary=engine.summary(results)
    a,b,c,d=st.columns(4)
    with a:card('Пунктов',summary['total'],'В выбранном режиме')
    with b:card('Автоматически',summary['automatic'],'Есть структурированные доказательства','ok')
    with c:card('К подтверждению',summary['prepared'],'Нужна оценка специалиста','warn')
    with d:card('Ручных',summary['manual'],'Инженерное решение','info')

    df=pd.DataFrame(results)
    df['Решение пользователя']='Не рассмотрено'; df['Комментарий']=''
    show=df.rename(columns={'item_no':'№','sheet':'Вкладка','question':'Контрольный вопрос','automation_level':'Тип','status':'Результат системы','evidence':'Основание','priority':'Приоритет','where_to_check':'Где сверить','risk':'Риск / замечание'})
    cols=[c for c in ['№','Вкладка','Контрольный вопрос','Тип','Результат системы','Основание','Где сверить','Решение пользователя','Комментарий'] if c in show]
    edited=st.data_editor(show[cols],hide_index=True,width='stretch',height=600,disabled=[c for c in cols if c not in {'Решение пользователя','Комментарий'}],column_config={'Решение пользователя':st.column_config.SelectboxColumn(options=['Не рассмотрено','Соответствует','Не соответствует','Не применимо','Требуется уточнение'])},key=f'checklist_workspace_editor_{checklist}_{selected_section}_{mode}')
    if st.button('Сохранить результаты чек-листа',width='content'):
        key=f'{selected_section}|{checklist}|{mode}'
        st.session_state.checklist_user_results[key]=edited.to_dict('records')
        st.success('Результаты сохранены в текущей сессии.')
    st.caption('Ручные пункты не считаются выполненными без решения специалиста. Автоматический статус формируется только при наличии структурированных доказательств.')
