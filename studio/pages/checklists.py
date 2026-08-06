from __future__ import annotations

import pandas as pd
import streamlit as st

from core.checklist_engine import ChecklistEngine
from studio.components import card, empty, section


def _document_options(docs: pd.DataFrame) -> list[str]:
    if docs.empty: return []
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
    section('Проверка ПД по чек-листам','Выберите корпоративный чек-лист и конкретный раздел документации. Результаты проверки по чек-листу не смешиваются с межраздельной сверкой ТЭП.')
    if docs.empty: return empty('Сначала загрузите комплект проектной документации.')
    engine=ChecklistEngine(ctx.config_dir/'knowledge'/'checklist_catalog.json')
    if not engine.items:return empty('Каталог чек-листов не загружен.')

    left,right=st.columns(2,gap='large')
    with left:
        st.markdown('### Чек-лист')
        checklist_files=engine.checklist_files()
        checklist=st.selectbox('Выберите чек-лист',checklist_files,key='workspace_checklist_file')
        recommended=engine.primary_section(checklist)
        st.caption(f'Рекомендуемый раздел: {recommended}')
    with right:
        st.markdown('### Документация')
        sections=engine.sections()
        selected_section=st.selectbox('Выберите раздел ПД',sections,index=sections.index(recommended) if recommended in sections else 0,key='workspace_checklist_section')
        document_labels=_document_options(docs)
        matching=[x for x in document_labels if x.startswith(selected_section+' ·')]
        selected_docs=st.multiselect('Документы для проверки',document_labels,default=matching,key='workspace_checklist_documents')
        if not selected_docs: st.warning('Выберите хотя бы один документ.')

    mode=st.radio('Режим проверки',['Быстрая','Полная','Экспертная'],horizontal=True,key='workspace_checklist_mode')
    if st.button('Проверить выбранный раздел',type='primary',width='stretch',disabled=not selected_docs):
        st.session_state.checklist_run={'section':selected_section,'source_file':checklist,'mode':mode,'documents':selected_docs}
        st.rerun()

    run=st.session_state.get('checklist_run')
    if not run:
        st.info('Выберите чек-лист и документы, затем запустите проверку.')
        return
    if run.get('source_file')!=checklist or run.get('section')!=selected_section or run.get('mode')!=mode:
        st.info('Параметры изменены. Запустите проверку повторно.')
        return

    selected_set=set(run.get('documents') or [])
    labels=_document_options(docs); doc_records=[]
    for label,(_,row) in zip(labels,docs.iterrows()):
        if label in selected_set: doc_records.append(row.to_dict())
    results=engine.evaluate(doc_records,comparisons.to_dict('records'),findings.to_dict('records'),source_file=checklist,section=selected_section)
    levels={'Быстрая':{'A'},'Полная':{'A','B'},'Экспертная':{'A','B','C'}}[mode]
    results=[r for r in results if r.get('is_heading') or r.get('automation_level') in levels]
    if not results:return empty('Для выбранного сочетания нет пунктов.')

    summary=engine.summary(results)
    a,b,c,d=st.columns(4)
    with a:card('Пунктов',summary['total'],'Без группирующих заголовков')
    with b:card('Да',summary['yes'],'Соответствие подтверждено','ok')
    with c:card('Нет',summary['no'],'Выявлено несоответствие','bad')
    with d:card('К проверке',summary['review']+summary['no_data'],'Недостаточно автоматических доказательств','warn')

    rows=[]
    details={}
    for r in results:
        no=str(r.get('item_no') or '').strip()
        question=str(r.get('question') or '').strip()
        position=(f'{no} — {question}' if no else question)
        value=('—' if r.get('status')=='Раздел' else r.get('status'))
        rows.append({'Позиция по чек-листу':position,'Соответствие':value})
        details[position]=r
    show=pd.DataFrame(rows)
    st.dataframe(show,hide_index=True,width='stretch',height=620,column_config={
        'Позиция по чек-листу':st.column_config.TextColumn(width='large'),
        'Соответствие':st.column_config.TextColumn(width='small'),
    })

    st.markdown('#### Пояснение по выбранной позиции')
    selectable=[x for x in show['Позиция по чек-листу'].tolist() if details[x].get('status')!='Раздел']
    if selectable:
        selected=st.selectbox('Позиция',selectable,key=f'checklist_detail_{checklist}_{selected_section}_{mode}')
        detail=details[selected]
        st.write(detail.get('evidence') or 'Пояснение отсутствует.')
        st.caption('Автоматический ответ «Да/Нет» формируется только при наличии структурированных доказательств. В остальных случаях система честно оставляет пункт на проверку специалисту.')
