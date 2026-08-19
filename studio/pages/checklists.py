from __future__ import annotations

import pandas as pd
import streamlit as st

from core.checklist_engine import ChecklistEngine
from core.automatic_review import AutomaticProjectReview
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

    first_doc=docs.iloc[0].to_dict() if not docs.empty else {}
    pipeline_auto=first_doc.get('automatic_checklist_review') or {}
    st.markdown('### Проверка всего комплекта')
    st.caption('ExpertCheck сам распознаёт разделы, сопоставляет их с доступными корпоративными чек-листами и запускает проверку. Разделы без корпоративного чек-листа показываются отдельно, а не пропускаются молча.')
    if st.button('Проверить весь комплект по чек-листам',type='primary',width='stretch',key='run_all_checklists'):
        reviewer=AutomaticProjectReview(ctx.config_dir/'knowledge')
        project_context={
            'project_type':str((first_doc.get('pp87_project_profile') or {}).get('project_type') or ''),
            'name':str(st.session_state.get('project_name') or ''),
            'description':' '.join(str(x) for x in docs.get('Тип документа',pd.Series(dtype=str)).tolist())
        }
        with st.spinner('Определяем разделы и выполняем все доступные проверки по чек-листам...'):
            st.session_state['all_checklists_review']=reviewer.execute(
                docs.to_dict('records'),
                comparisons.to_dict('records'),
                findings.to_dict('records'),
                project_context=project_context
            )
        # Store for reports/risk engine as the latest project-wide checklist run.
        st.session_state.checklist_run={
            'section':'Все распознанные разделы',
            'source_file':'Все доступные чек-листы',
            'mode':'Автоматическая',
            'results':list(st.session_state['all_checklists_review'].get('results') or [])
        }
        st.rerun()
    auto=st.session_state.get('all_checklists_review') or pipeline_auto
    auto_summary=auto.get('summary') or {}
    if auto_summary and not auto_summary.get('error'):
        st.markdown('### Автоматическая проверка')
        c1,c2,c3,c4=st.columns(4)
        c1.metric('Чек-листов',auto_summary.get('checklists_run',0))
        c2.metric('Проверок',auto_summary.get('checks',0))
        c3.metric('Требуют внимания',int(auto_summary.get('no',0))+int(auto_summary.get('review',0)))
        c4.metric('AI/специалист',auto_summary.get('semantic_pending_ai',0))
        programme=auto.get('runs') or []
        routing=auto.get('routing') or {}
        if programme:
            with st.expander('Программа автоматической проверки',expanded=False):
                st.dataframe(pd.DataFrame(programme),hide_index=True,width='stretch')
        covered=routing.get('covered_sections') or []
        uncovered=routing.get('uncovered_sections') or []
        if covered:
            st.success('Чек-листы автоматически сопоставлены с разделами: '+', '.join(covered))
        if uncovered:
            st.warning('Распознаны разделы без корпоративного чек-листа: '+', '.join(uncovered)+'. Они не считаются проверенными по корпоративному чек-листу; для них сохраняется нормативная/межраздельная проверка.')
        if routing.get('unknown_document_count'):
            st.info(f"Не удалось однозначно классифицировать документов: {routing.get('unknown_document_count')}.")
        auto_results=[r for r in (auto.get('results') or []) if not r.get('is_heading')]
        # Automatic semantic AI review: no checklist/section selection is required.
        ai_level=str(st.session_state.get('ai_pipeline_level') or 'Отключён')
        auto_ai_store=st.session_state.setdefault('automatic_checklist_ai_reviews',{})
        auto_ai_signature=str(first_doc.get('analysis_time') or '')+'|'+str(auto_summary.get('checks') or 0)
        if ai_level in {'Умный автоматический','Расширенный','Максимальный'} and auto_ai_signature not in auto_ai_store:
            provider=provider_for_role('extraction',st.session_state,st.secrets)
            if provider:
                batch=[]
                for idx,r in enumerate(auto_results):
                    if r.get('execution_class') not in {'SEMANTIC','EXPERT'} or r.get('status') not in {'Нет','Требует проверки','Нет данных','Не проверено системой'}:
                        continue
                    compiled=r.get('compiled_rule') or {}
                    terms=compiled.get('evidence_terms') or []
                    evidence_rows=[]
                    for row in findings.to_dict('records'):
                        blob=' '.join(str(row.get(k) or '') for k in ('context','section_title','structural_zone','table_title','table_evidence','value_text'))
                        if not terms or any(str(t).lower() in blob.lower() for t in terms):
                            evidence_rows.append({k:row.get(k) for k in ('document','document_type','page','section_title','table_title','context','value_text','parameter_code','object_hint')})
                        if len(evidence_rows)>=7: break
                    key=f'auto-{idx}'
                    r['_auto_ai_key']=key
                    batch.append({'key':key,'checklist_position':r.get('item_no'),'question':r.get('question'),'core_status':r.get('status'),'compiled_rule':compiled,'evidence':evidence_rows})
                    if len(batch)>=18: break
                if batch:
                    with st.spinner('AI автоматически проверяет смысловые пункты программы проверки...'):
                        ai_result,reviews=analyze_checklist_batch(provider,batch)
                    auto_ai_store[auto_ai_signature]=reviews if ai_result.ok else {'__error__':diagnostic_message(ai_result)}
                else:
                    auto_ai_store[auto_ai_signature]={}
        auto_reviews=auto_ai_store.get(auto_ai_signature,{})
        if auto_results:
            for r in auto_results:
                review=auto_reviews.get(r.get('_auto_ai_key')) if isinstance(auto_reviews,dict) else None
                if review:
                    r['_auto_ai_result']=review
            result_df=pd.DataFrame([{
              'Раздел':r.get('automatic_section'),
              'Чек-лист':r.get('automatic_checklist'),
              'Позиция':r.get('item_no'),
              'Проверка':r.get('question'),
              'Результат':r.get('status'),
              'AI': ({'yes':'Да','no':'Нет','partial':'Частично','requires_review':'Требует проверки','insufficient_data':'Недостаточно данных'}.get(str((r.get('_auto_ai_result') or {}).get('result') or ''),'') if r.get('_auto_ai_result') else ''),
              'Тип':r.get('execution_class')
            } for r in auto_results])
            attention=result_df[result_df['Результат'].isin(['Нет','Требует проверки','Нет данных','Не проверено системой'])]
            if not attention.empty:
                st.dataframe(attention,hide_index=True,width='stretch')
            else:
                st.success('Автоматическая проверка не выявила пунктов, требующих внимания.')
    elif auto_summary.get('error'):
        st.warning('Автоматическая проверка чек-листов не завершена: '+str(auto_summary.get('error')))

    with st.expander('Выборочная ручная проверка',expanded=not bool(auto_summary)):
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
                    if r.get('is_heading') or r.get('status') not in {'Нет','Требует проверки','Нет данных','Не проверено системой'}:
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
        with d:card('К проверке',summary['review']+summary['no_data']+summary.get('unsupported',0)+sum(1 for x in results if x.get('status')=='Частично'),'Недостаточно автоматических доказательств','warn')

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
            compiled=detail.get('compiled_rule') or {}
            automation=compiled.get('automation_class')
            if automation:
                labels={'AUTO':'Автоматическая проверка','CALC':'Расчётная / межраздельная проверка','SEMANTIC':'Смысловой AI-анализ','EXPERT':'Контроль специалиста'}
                st.caption('Тип проверки: ' + labels.get(automation,str(automation)))
            normative=detail.get('normative_context') or []
            if normative:
                with st.expander('Нормативный контекст пункта'):
                    for norm in normative[:4]:
                        st.markdown(f"**{norm.get('source','')} · {norm.get('topic','')}**")
                        st.write(norm.get('requirement') or '')
                        st.caption(norm.get('status') or 'Предварительная проверка')
                    st.caption('Нормативный контекст используется как база предварительного контроля и не заменяет проверку актуальной редакции НТД специалистом.')
            if st.session_state.get('expert_mode') and detail.get('compiled_rule'):
                with st.expander('Скомпилированное правило'):
                    st.json(detail.get('compiled_rule'))
            if st.session_state.get('ai_assisted_extraction') and detail.get('status') in {'Нет','Требует проверки','Нет данных','Не проверено системой'}:
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
