from __future__ import annotations
import pandas as pd
import streamlit as st
from studio.components import hero,card,empty,section
from core.global_finding_gate import apply_finding_gate
from core.expert_review_engine import build_expert_risks
from core.review_queue import build_review_clusters
from core.result_ledger import build_qualified_result_ledger
from core.report_engine import build_structured_report
from core.result_surface import build_project_surface_rows, build_review_surface_rows


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
    raw_comparisons=comparisons.to_dict('records') if not comparisons.empty else []
    ledger=build_qualified_result_ledger(
        assignment_rows=list(first.get('assignment_compliance') or []),
        normative_rows=list(first.get('normative_compliance_audit') or []),
        checklist_rows=checklist,
        comparisons=raw_comparisons,
    )
    assignment=ledger['assignment_rows']
    normative=ledger['normative_rows']
    checklist=ledger['checklist_rows']
    comparison_rows=ledger['comparisons']
    plan=ledger['review_plan']
    plan_items=list(plan.get('items') or [])
    report=build_structured_report(
        st.session_state.get('project_name') or 'Проект',
        docs.to_dict('records'),
        comparison_rows,
        checklist_results=checklist,
        assembly_rows=st.session_state.get('object_assembly_rows') or [],
    )
    project=build_project_surface_rows(report.get('problems') or [], plan)
    review=build_review_surface_rows(report.get('problems') or [], plan)
    verified=sum(1 for item in plan_items if item.get('verification_kind')=='VERIFIED_OK')
    limits=sum(1 for item in plan_items if item.get('verification_kind')=='SYSTEM_LIMITATION')
    review_clusters=build_review_clusters(review)
    compression_pct=round(100*(1-len(review_clusters)/max(1,len(review))),1) if review else 0.0
    c1,c2,c3,c4=st.columns(4)
    with c1:card('Несоответствия',len(project),'Доказанные проблемы','bad' if project else 'ok')
    with c2:card(
        'Вопросы специалисту',
        len(review),
        f'{len(review_clusters)} рабочих пакетов · сжатие {compression_pct:.0f}%',
        'warn' if review else 'ok'
    )
    with c3:card('Подтверждено',verified,'Проверки с доказательством','ok')
    with c4:card('Не проверено',limits,'Ограничения покрытия','info')

    tabs=st.tabs(['Несоответствия','Вопросы специалисту','Подтверждено'])
    with tabs[0]:
        if not project:empty('Доказанные несоответствия не сформированы.')
        else:st.dataframe(pd.DataFrame([{'Контур / объект':r.get('object') or '—','Проверка':r.get('parameter_name') or r.get('parameter') or '—','Результат':r.get('status') or r.get('result') or 'Несоответствие','Обоснование':r.get('explanation') or ''} for r in project]).head(80),hide_index=True,width='stretch')
    with tabs[1]:
        if not review:empty('Обоснованные вопросы специалисту не сформированы.')
        else:
            st.caption(
                'Сначала показаны рабочие пакеты по общей инженерной причине и маршруту доказательства. '
                'Один пакет может охватывать несколько объектов; все исходные вопросы сохранены ниже для трассировки.'
            )
            st.dataframe(pd.DataFrame(review_clusters).head(40),hide_index=True,width='stretch')
            with st.expander(f'Все адресные вопросы ({len(review)})'):
                st.dataframe(pd.DataFrame([{
                    'Контур':r.get('Контур') or '—',
                    'Объект':r.get('Объект') or '—',
                    'Вопрос':r.get('Проверка') or '—',
                    'Код причины':r.get('Код причины') or '—',
                    'Почему требуется проверка':r.get('Причина') or '',
                } for r in review]).head(500),hide_index=True,width='stretch')
    with tabs[2]:
        rows=[{
            'Контур':item.get('domain') or '—',
            'Объект':item.get('entity') or '—',
            'Проверка':item.get('title') or '—',
            'Уровень доказательства':item.get('evidence_level') or 'L0',
            'Результат':'Соответствует',
        } for item in plan_items if item.get('verification_kind')=='VERIFIED_OK']
        if not rows:empty('Автоматически подтверждённые проверки пока отсутствуют.')
        else:st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')

    if st.session_state.get('expert_mode'):
        section('Диагностика покрытия','Ограничения системы не являются замечаниями к проекту.')
        st.caption(f'Не завершено автоматически: {limits}.')
