from __future__ import annotations
import pandas as pd
import streamlit as st
from studio.components import hero,card,empty,section
from core.global_finding_gate import apply_finding_gate
from core.expert_review_engine import build_expert_risks
from core.verification_core import annotate_rows
from core.review_queue import build_review_clusters
from core.project_review_planner import build_review_plan


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
    comparison_rows=comparisons.to_dict('records') if not comparisons.empty else []
    gated=apply_finding_gate(comparison_rows)

    plan=build_review_plan(
        assignment_rows=list(first.get('assignment_compliance') or []),
        normative_rows=list(first.get('normative_compliance_audit') or []),
        checklist_review={'results': checklist},
        comparisons=comparison_rows,
    )
    plan_items=list(plan.get('items') or [])

    project=[{
        'object':item.get('entity') or item.get('domain') or '—',
        'parameter_name':item.get('title') or '—',
        'status':item.get('verification_state') or 'Несоответствие',
        'explanation':item.get('coverage_reason') or item.get('recommendation') or '',
    } for item in plan_items if item.get('verification_kind')=='PROJECT_FINDING']

    review_rows=[]
    for item in plan_items:
        if item.get('verification_kind')!='REVIEW_QUESTION':
            continue
        review_rows.append({
            'ID':item.get('plan_id'),
            'Контур':item.get('domain') or 'Не определён',
            'Объект':item.get('entity') or '—',
            'Проверка':item.get('title') or '—',
            'Причина':item.get('coverage_reason') or 'Требуется предметное решение специалиста.',
            'Код причины':item.get('coverage_reason_code') or 'SPECIALIST_JUDGEMENT',
            'Семейство проверки':item.get('checker_family') or '—',
            'Ожидаемые разделы':item.get('expected_evidence_route') or item.get('expected_sections') or '—',
            'Уровень доказательства':item.get('evidence_level') or 'L0',
        })
    # Keep comparison findings produced by the global gate if they are not
    # represented in the plan. This mirrors the technical-report queue.
    for row in gated:
        if row.get('finding_type')!='REVIEW_QUESTION':
            continue
        review_rows.append({
            'ID':row.get('id') or row.get('check_code') or row.get('comparison_id'),
            'Контур':'Межраздельная сверка',
            'Объект':row.get('object') or '—',
            'Проверка':row.get('parameter_name') or row.get('parameter') or '—',
            'Причина':row.get('global_finding_reason') or row.get('explanation') or 'Требуется предметное решение специалиста.',
            'Код причины':row.get('coverage_reason_code') or 'CROSS_SECTION_REVIEW',
            'Семейство проверки':row.get('checker_family') or 'Детерминированная межраздельная сверка',
            'Ожидаемые разделы':row.get('expected_sections') or row.get('sources') or '—',
            'Уровень доказательства':row.get('evidence_level') or 'L0',
        })
    review=[]; seen=set()
    for row in review_rows:
        key=(str(row.get('Контур') or ''),str(row.get('ID') or ''),str(row.get('Проверка') or ''))
        if key in seen:
            continue
        seen.add(key); review.append(row)

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
