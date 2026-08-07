from __future__ import annotations

import pandas as pd
import streamlit as st

from core.checklist_engine import ChecklistEngine
from core.ai_gateway import analyze_checklist_evidence, analyze_checklist_batch, diagnostic_message, provider_for_role
from studio.components import card, empty, section
from studio.ai_presenter import render_ai_result, render_unstructured_ai_text


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
    section('Проверка раздела','ExpertCheck сопоставляет выбранный раздел одновременно с корпоративным чек-листом и базовой контрольной матрицей ПП №87. AI автоматически подключается к неоднозначным смысловым пунктам.')
    if docs.empty: return empty('Сначала загрузите комплект проектной документации.')
    engine=ChecklistEngine(ctx.config_dir/'knowledge'/'checklist_catalog.json')
    if not engine.items:return empty('Каталог чек-листов не загружен.')

    with st.container(border=True):
        left,right=st.columns(2,gap='large')
        with left:
            checklist_files=engine.checklist_files()
            checklist=st.selectbox('Чек-лист',checklist_files,key='workspace_checklist_file')
            recommended=engine.primary_section(checklist)
            st.caption(f'Рекомендуемый раздел: {recommended}')
        with right:
            sections=engine.sections()
            selected_section=st.selectbox('Раздел ПД',sections,index=sections.index(recommended) if recommended in sections else 0,key='workspace_checklist_section')
            document_labels=_document_options(docs)
            matching=[x for x in document_labels if x.startswith(selected_section+' ·')]
            selected_docs=st.multiselect('Документы',document_labels,default=matching,key='workspace_checklist_documents')
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
    results=engine.evaluate_with_pp87(doc_records,comparisons.to_dict('records'),findings.to_dict('records'),source_file=checklist,section=selected_section)
    levels={'Быстрая':{'A'},'Полная':{'A','B'},'Экспертная':{'A','B','C'}}[mode]
    results=[r for r in results if r.get('is_heading') or r.get('automation_level') in levels]
    if not results:return empty('Для выбранного сочетания нет пунктов.')

    # In extended AI mode semantic and uncertain checklist items are reviewed automatically
    # in one compact batch. Core evidence remains visible and AI cannot hide missing data.
    ai_level = str(st.session_state.get('ai_pipeline_level') or 'Отключён')
    batch_signature = f"{checklist}|{selected_section}|{mode}|{','.join(sorted(selected_set))}"
    batch_store = st.session_state.setdefault('ai_checklist_batch_reviews', {})
    if ai_level in {'Умный автоматический','Расширенный','Максимальный'} and batch_signature not in batch_store:
        provider = provider_for_role('extraction', st.session_state, st.secrets)
        if provider:
            batch_items=[]
            for idx,r in enumerate(results):
                if r.get('is_heading') or r.get('status') not in {'Нет','Требует проверки','Нет данных'}:
                    continue
                terms=(r.get('compiled_rule') or {}).get('evidence_terms') or []
                evidence_rows=[]
                for row in findings.to_dict('records'):
                    blob=' '.join(str(row.get(k) or '') for k in ('context','section_title','structural_zone','table_title','table_evidence','value_text'))
                    if not terms or any(str(t).lower() in blob.lower() for t in terms):
                        evidence_rows.append({k:row.get(k) for k in ('document','document_type','page','section_title','table_title','context','value_text','parameter_code','object_hint')})
                    if len(evidence_rows)>=8: break
                key=f"item-{idx}"
                r['_ai_batch_key']=key
                batch_items.append({'key':key,'checklist_position':r.get('item_no'),'question':r.get('question'),'core_status':r.get('status'),'compiled_rule':r.get('compiled_rule'),'evidence':evidence_rows})
                if len(batch_items)>=12: break
            if batch_items:
                with st.spinner('AI выполняет смысловую проверку неоднозначных пунктов чек-листа...'):
                    batch_result,batch_reviews=analyze_checklist_batch(provider,batch_items)
                if batch_result.ok:
                    batch_store[batch_signature]=batch_reviews
                else:
                    batch_store[batch_signature]={'__error__':diagnostic_message(batch_result)}
    batch_reviews=batch_store.get(batch_signature,{})
    for r in results:
        review=batch_reviews.get(r.get('_ai_batch_key')) if isinstance(batch_reviews,dict) else None
        if not review: continue
        r['ai_review']=review
        result_code=str(review.get('result') or '')
        confidence=float(review.get('confidence') or 0)
        if confidence>=0.78:
            mapped={'yes':'Да','no':'Нет','partial':'Частично','requires_review':'Требует проверки','insufficient_data':'Нет данных'}.get(result_code)
            if mapped:
                r['status_before_ai']=r.get('status')
                r['status']=mapped
                r['evidence']=(r.get('evidence') or '')+' AI-анализ: '+str(review.get('reason') or '')

    # Persist final checklist results for the Expert Review Engine and reports.
    if isinstance(st.session_state.get('checklist_run'), dict):
        st.session_state.checklist_run['results'] = [dict(row) for row in results]
    summary=engine.summary(results)
    a,b,c,d=st.columns(4)
    with a:card('Пунктов',summary['total'],'Без группирующих заголовков')
    with b:card('Да',summary['yes'],'Соответствие подтверждено','ok')
    with c:card('Нет',summary['no'],'Выявлено несоответствие','bad')
    with d:card('К проверке',summary['review']+summary['no_data']+sum(1 for x in results if x.get('status')=='Частично'),'Недостаточно автоматических доказательств','warn')

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
    st.dataframe(show,hide_index=True,width='stretch',height=480,column_config={
        'Позиция по чек-листу':st.column_config.TextColumn(width='large'),
        'Соответствие':st.column_config.TextColumn(width='small'),
    })

    st.markdown('#### Детали выбранного пункта')
    selectable=[x for x in show['Позиция по чек-листу'].tolist() if details[x].get('status')!='Раздел']
    if selectable:
        selected=st.selectbox('Позиция',selectable,key=f'checklist_detail_{checklist}_{selected_section}_{mode}')
        detail=details[selected]
        st.write(detail.get('evidence') or 'Пояснение отсутствует.')
        if st.session_state.get('expert_mode') and detail.get('compiled_rule'):
            with st.expander('Скомпилированное правило'):
                st.json(detail.get('compiled_rule'))
        if st.session_state.get('ai_assisted_extraction') and detail.get('status') in {'Нет','Требует проверки','Нет данных'}:
            provider=provider_for_role('extraction', st.session_state, st.secrets)
            if provider and st.button('Провести смысловой AI-анализ пункта',key='ai_checklist_item_btn'):
                evidence_rows=[]
                terms=(detail.get('compiled_rule') or {}).get('evidence_terms') or []
                for row in findings.to_dict('records'):
                    blob=' '.join(str(row.get(k) or '') for k in ('context','section_title','structural_zone','table_title','table_evidence','value_text'))
                    if not terms or any(str(t).lower() in blob.lower() for t in terms):
                        evidence_rows.append({k:row.get(k) for k in ('document','document_type','page','section_title','table_title','context','value_text','parameter_code','object_hint')})
                    if len(evidence_rows)>=16: break
                with st.spinner('AI сопоставляет пункт чек-листа с найденными фрагментами...'):
                    result,data=analyze_checklist_evidence(provider,detail,evidence_rows)
                if result.ok and data:
                    st.session_state.ai_checklist_reviews[selected]=data
                elif result.ok:
                    st.warning('AI вернул ответ без ожидаемой структуры.'); render_unstructured_ai_text(result.text)
                else:
                    st.error(diagnostic_message(result))
            ai_review=st.session_state.get('ai_checklist_reviews',{}).get(selected)
            if ai_review:
                render_ai_result(ai_review, title='AI-анализ пункта чек-листа')
                st.caption('AI-оценка не заменяет решение специалиста и не меняет результат автоматически.')
        st.caption('Автоматический ответ «Да/Нет» формируется только при наличии структурированных доказательств. В остальных случаях система честно оставляет пункт на проверку специалисту.')
