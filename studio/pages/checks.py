from __future__ import annotations

import pandas as pd
import streamlit as st

from core.checklist_engine import ChecklistEngine
from studio.components import card, empty, section


def _cross_checks(ctx, df: pd.DataFrame):
    section('Межраздельные сверки','Сопоставление выполняется только после ручного подтверждения состава проекта.')
    if not st.session_state.get('object_registry_confirmed'):
        st.warning('Сначала откройте раздел «Объекты», исключите лишние позиции и подтвердите состав проекта.')
        return
    if df.empty:return empty('После подтверждения состава сопоставимые сведения не найдены.')
    statuses=sorted(df.get('status',pd.Series(dtype=str)).dropna().astype(str).unique())
    c1,c2=st.columns([1,2]); selected=c1.multiselect('Статус',statuses,default=statuses,key='cross_status'); q=c2.text_input('Поиск',key='cross_search'); view=df.copy()
    if selected and 'status' in view:view=view[view.status.isin(selected)]
    if q:view=view[view.astype(str).apply(lambda c:c.str.contains(q,case=False,na=False)).any(axis=1)]
    cols=['object','parameter_name','status','documents','document_values','explanation']
    if st.session_state.expert_mode:cols+=['check_code','priority','evidence_count','sources','engineering_risk_level']
    labels={'object':'Объект','parameter_name':'Характеристика','status':'Результат','documents':'Разделы','document_values':'Значения','explanation':'Объяснение','check_code':'Код','priority':'Приоритет','evidence_count':'Подтверждений','sources':'Источники','engineering_risk_level':'Риск'}
    st.dataframe(view[[c for c in cols if c in view]].rename(columns=labels),width='stretch',hide_index=True)


def _checklists(ctx, docs, findings, comparisons):
    section('Проверка по чек-листу','Выберите раздел, соответствующий корпоративный чек-лист и запустите отдельную проверку.')
    engine=ChecklistEngine(ctx.config_dir/'knowledge'/'checklist_catalog.json')
    if not engine.items:return empty('Каталог чек-листов не загружен.')
    sections=engine.sections()
    c1,c2=st.columns(2)
    section_name=c1.selectbox('Раздел проектной документации',sections,key='checklist_section')
    files=engine.checklist_files(section_name)
    if not files:return st.info('Для выбранного раздела чек-лист не найден.')
    checklist=c2.selectbox('Чек-лист',files,key='checklist_file')
    mode=st.radio('Режим проверки',['Быстрая','Полная','Экспертная'],horizontal=True,key='checklist_mode',help='Быстрая — автоматизируемые пункты; Полная — A и B; Экспертная — все пункты, включая ручные.')
    if st.button('Запустить проверку по чек-листу',type='primary',width='content'):
        st.session_state.checklist_run={'section':section_name,'source_file':checklist,'mode':mode}
        st.session_state.checklist_user_results={}
        st.rerun()
    run=st.session_state.get('checklist_run')
    if not run or run.get('source_file')!=checklist or run.get('section')!=section_name:
        st.info('Выберите параметры и нажмите «Запустить проверку по чек-листу».')
        return
    results=engine.evaluate(docs.to_dict('records'),comparisons.to_dict('records'),findings.to_dict('records'),source_file=checklist,section=section_name)
    levels={'Быстрая':{'A'},'Полная':{'A','B'},'Экспертная':{'A','B','C'}}[mode]
    results=[r for r in results if r.get('automation_level') in levels]
    if not results:return empty('Для выбранного режима в чек-листе нет пунктов.')
    summary=engine.summary(results)
    a,b,c,d=st.columns(4)
    with a:card('Пунктов',summary['total'],'В выбранном режиме')
    with b:card('Автоматически',summary['automatic'],'Есть связанные доказательства','ok')
    with c:card('К подтверждению',summary['prepared'],'Нужна оценка специалиста','warn')
    with d:card('Ручных',summary['manual'],'Инженерное решение','info')
    df=pd.DataFrame(results)
    df['Решение пользователя']='Не рассмотрено'; df['Комментарий']=''
    show=df.rename(columns={'item_no':'№','sheet':'Вкладка','question':'Контрольный вопрос','automation_level':'Тип','status':'Результат системы','evidence':'Основание','priority':'Приоритет','where_to_check':'Где сверить','risk':'Риск / замечание'})
    cols=[c for c in ['№','Вкладка','Контрольный вопрос','Тип','Результат системы','Основание','Где сверить','Решение пользователя','Комментарий'] if c in show]
    edited=st.data_editor(show[cols],hide_index=True,width='stretch',height=560,disabled=[c for c in cols if c not in {'Решение пользователя','Комментарий'}],column_config={'Решение пользователя':st.column_config.SelectboxColumn(options=['Не рассмотрено','Соответствует','Не соответствует','Не применимо','Требуется уточнение'])},key=f"checklist_editor_{checklist}_{section_name}_{mode}")
    if st.button('Сохранить результаты чек-листа',width='content'):
        st.session_state.checklist_user_results[f'{section_name}|{checklist}|{mode}']=edited.to_dict('records')
        st.success('Результаты проверки по чек-листу сохранены в текущей сессии.')
    st.caption('Система не считает ручной пункт выполненным без решения пользователя. Автоматические результаты являются предварительными и должны иметь структурированное доказательство.')


def render(ctx):
    docs,findings,comparisons=ctx.data[:3]
    tabs=st.tabs(['Межраздельные сверки','Чек-листы'])
    with tabs[0]:_cross_checks(ctx,comparisons)
    with tabs[1]:_checklists(ctx,docs,findings,comparisons)
