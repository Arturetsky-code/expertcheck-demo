from __future__ import annotations
import pandas as pd
import streamlit as st
from studio.components import hero,card,empty,section
from core.global_finding_gate import apply_finding_gate
from core.expert_review_engine import build_expert_risks


def _checklist_results():
    run=st.session_state.get('checklist_run') or {}
    rows=run.get('results') if isinstance(run,dict) else None
    return rows if isinstance(rows,list) else []


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero('Результаты проверки','Здесь собраны только пользовательские выводы. Ограничения автоматической проверки не смешиваются с проблемами проекта.','Проблема проекта → вопрос специалисту → техническое ограничение')
    if docs.empty:return empty('Сначала выполните проверку проекта.')
    rows=apply_finding_gate(comparisons.to_dict('records') if not comparisons.empty else [])
    project=[r for r in rows if r.get('finding_type')=='PROJECT_FINDING']
    review=[r for r in rows if r.get('finding_type')=='REVIEW_QUESTION']
    limits=[r for r in rows if r.get('finding_type')=='SYSTEM_LIMITATION']
    risks=build_expert_risks(comparisons.to_dict('records') if not comparisons.empty else [],st.session_state.get('object_assembly_rows') or [],_checklist_results(),documents=docs.to_dict('records'))
    c1,c2,c3=st.columns(3)
    with c1: card('Проблемы проекта',len(project),'Доказанные несоответствия','bad' if project else 'ok')
    with c2: card('Вопросы специалисту',len(review),'Есть основание для инженерной проверки','warn' if review else 'ok')
    with c3: card('Ограничения системы',len(limits),'Не являются замечаниями к ПД','info')
    tabs=st.tabs(['Проблемы проекта','Вопросы специалисту','Риски экспертизы'] + (['Ограничения системы'] if st.session_state.get('expert_mode') else []))
    with tabs[0]:
        if not project: empty('Доказанные проблемы проекта не сформированы.')
        else: st.dataframe(pd.DataFrame([{'Объект':r.get('object') or r.get('object_name') or '—','Показатель':r.get('parameter_name') or r.get('parameter') or 'Проверка','Результат':r.get('status') or r.get('result'),'Пояснение':r.get('explanation') or ''} for r in project]),hide_index=True,width='stretch')
    with tabs[1]:
        if not review: empty('Обоснованные вопросы специалисту не сформированы.')
        else: st.dataframe(pd.DataFrame([{'Объект':r.get('object') or r.get('object_name') or '—','Вопрос':r.get('parameter_name') or r.get('parameter') or 'Проверка','Почему требуется специалист':r.get('global_finding_reason') or r.get('explanation') or ''} for r in review]),hide_index=True,width='stretch')
    with tabs[2]:
        if not risks: empty('Риски экспертизы не сформированы.')
        else: st.dataframe(pd.DataFrame([{'Уровень':r.get('level'),'Категория':r.get('category'),'Объект / раздел':r.get('object') or '—','Вопрос':r.get('parameter'),'Рекомендация':r.get('recommendation')} for r in risks]),hide_index=True,width='stretch')
    if st.session_state.get('expert_mode'):
        with tabs[3]:
            section('Ограничения автоматической проверки','Эти записи помогают развивать ExpertCheck, но не должны попадать в замечания или план действий ГИПа.')
            if not limits: empty('Ограничения не зафиксированы.')
            else: st.dataframe(pd.DataFrame([{'Проверка':r.get('parameter_name') or r.get('parameter') or '—','Объект':r.get('object') or '—','Причина':r.get('global_finding_reason') or r.get('explanation') or ''} for r in limits]),hide_index=True,width='stretch')
