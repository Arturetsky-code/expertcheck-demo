from __future__ import annotations
import pandas as pd
import streamlit as st
from studio.components import hero,card,empty,section
from core.global_finding_gate import apply_finding_gate
from core.expert_review_engine import build_expert_risks
from core.verification_core import annotate_rows


def _first(docs):return docs.iloc[0].to_dict() if not docs.empty else {}

def _checklist(first):
    run=st.session_state.get('checklist_run') or {}
    if isinstance(run,dict) and isinstance(run.get('results'),list):return run['results']
    return list((first.get('automatic_checklist_review') or {}).get('results') or [])


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero('Результаты','Только квалифицированные результаты проверки проекта.','Несоответствия · вопросы специалисту · подтверждённое соответствие')
    if docs.empty:return empty('Сначала выполните проверку проекта.')
    first=_first(docs); checklist=_checklist(first)
    assignment=annotate_rows(list(first.get('assignment_compliance') or []),'assignment')
    normative=annotate_rows(list(first.get('normative_compliance_audit') or []),'normative')
    checklist=annotate_rows(checklist,'checklist')
    gated=apply_finding_gate(comparisons.to_dict('records') if not comparisons.empty else [])

    project=[r for r in gated if r.get('finding_type')=='PROJECT_FINDING']
    review=[r for r in gated if r.get('finding_type')=='REVIEW_QUESTION']
    for domain,rows in [('Задание',assignment),('НТД',normative),('Чек-листы',checklist)]:
        for r in rows:
            if r.get('verification_kind')=='PROJECT_FINDING':project.append({'object':domain,'parameter_name':r.get('requirement_text') or r.get('requirement') or r.get('question'),'status':r.get('verification_state'),'explanation':r.get('decision_basis') or r.get('evidence') or ''})
            elif r.get('verification_kind')=='REVIEW_QUESTION':review.append({'object':domain,'parameter_name':r.get('requirement_text') or r.get('requirement') or r.get('question'),'global_finding_reason':r.get('decision_basis') or r.get('evidence') or ''})
    verified=sum(1 for rows in (assignment,normative,checklist) for r in rows if r.get('verification_kind')=='VERIFIED_OK')
    limits=sum(1 for rows in (assignment,normative,checklist) for r in rows if r.get('verification_kind')=='SYSTEM_LIMITATION')
    c1,c2,c3,c4=st.columns(4)
    with c1:card('Несоответствия',len(project),'Доказанные проблемы','bad' if project else 'ok')
    with c2:card('Вопросы специалисту',len(review),'Есть конкретное основание','warn' if review else 'ok')
    with c3:card('Подтверждено',verified,'Проверки с доказательством','ok')
    with c4:card('Не проверено',limits,'Ограничения покрытия','info')

    tabs=st.tabs(['Несоответствия','Вопросы специалисту','Подтверждено'])
    with tabs[0]:
        if not project:empty('Доказанные несоответствия не сформированы.')
        else:st.dataframe(pd.DataFrame([{'Контур / объект':r.get('object') or '—','Проверка':r.get('parameter_name') or r.get('parameter') or '—','Результат':r.get('status') or r.get('result') or 'Несоответствие','Обоснование':r.get('explanation') or ''} for r in project]).head(80),hide_index=True,width='stretch')
    with tabs[1]:
        if not review:empty('Обоснованные вопросы специалисту не сформированы.')
        else:st.dataframe(pd.DataFrame([{'Контур / объект':r.get('object') or '—','Вопрос':r.get('parameter_name') or r.get('parameter') or '—','Почему требуется проверка':r.get('global_finding_reason') or r.get('explanation') or ''} for r in review]).head(80),hide_index=True,width='stretch')
    with tabs[2]:
        rows=[]
        for domain,data in [('Задание',assignment),('НТД',normative),('Чек-листы',checklist)]:
            for r in data:
                if r.get('verification_kind')=='VERIFIED_OK':rows.append({'Контур':domain,'Проверка':r.get('requirement_text') or r.get('requirement') or r.get('question') or '—','Результат':'Соответствует'})
        if not rows:empty('Автоматически подтверждённые проверки пока отсутствуют.')
        else:st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')

    if st.session_state.get('expert_mode'):
        section('Диагностика покрытия','Ограничения системы не являются замечаниями к проекту.')
        st.caption(f'Не завершено автоматически: {limits}.')
