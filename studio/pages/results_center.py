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
from core20.proof_labels import judge_label, proof_state_label, proof_type_label


def _first(docs):return docs.iloc[0].to_dict() if not docs.empty else {}

def _checklist(first):
    run=st.session_state.get('checklist_run') or {}
    if isinstance(run,dict) and isinstance(run.get('results'),list):return run['results']
    return list((first.get('automatic_checklist_review') or {}).get('results') or [])


def _semantic_trace(row):
    proof=dict(row.get('semantic_proof') or {})
    selected=list(proof.get('selected_evidence') or row.get('semantic_selected_evidence') or [])
    rendered=[]
    for item in selected:
        if not isinstance(item,dict):
            continue
        locator=item.get('source_locator')
        if not locator and item.get('document'):
            locator=f"{item.get('document')}, стр. {item.get('page')}"
        if locator and locator not in rendered:
            rendered.append(str(locator))
    return ' | '.join(rendered)


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero('Результаты','Только квалифицированные результаты проверки проекта.','Несоответствия · вопросы специалисту · подтверждённое соответствие')
    if docs.empty:return empty('Сначала выполните проверку проекта.')
    first=_first(docs); checklist=_checklist(first)
    canonical=dict(first.get('canonical_core_20_manifest') or st.session_state.get('canonical_core_20_manifest') or {})
    normative20=dict(canonical.get('normative_execution') or {})
    normative20_rows=list(normative20.get('rows') or [])
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

    if normative20_rows:
        section(
            'НТД 20.0 — доказательная проверка',
            'Верифицированный пункт проходит отдельный доказательный контроль: найденный текст ещё не означает выполненное нормативное требование.'
        )
        retrieval=dict(normative20.get('retrieval') or {})
        n1,n2,n3,n4,n5=st.columns(5)
        with n1:card('Контрактов',normative20.get('contracts',0),'Верифицированные пункты')
        with n2:card('Кандидатов доказательства',retrieval.get('candidate_evidence',0),'Адресные фрагменты по страницам','info')
        with n3:card('Доказано',normative20.get('verified_ok',0),'Прошло доказательный контроль','ok')
        with n4:card('Удержано',normative20.get('demoted_keyword_only',0),'Поиск ≠ доказательство','warn' if normative20.get('demoted_keyword_only') else 'ok')
        with n5:card('Очередь смысловой проверки',normative20.get('semantic_queue_total',0),'Нужна смысловая проверка','warn' if normative20.get('semantic_queue_total') else 'ok')
        m1,m2,m3,m4=st.columns(4)
        with m1:card('Смысл подтверждён',normative20.get('semantic_proof_applied',0),'Проверяющая + контрольная модель + программный контроль','ok' if normative20.get('semantic_proof_applied') else 'info')
        with m2:card('Вопросы',normative20.get('review_questions',0),'Нужна инженерная проверка','warn' if normative20.get('review_questions') else 'ok')
        with m3:card('Не проверено',normative20.get('system_limitations',0),'Нет подходящего доказательного механизма','info')
        with m4:card('Адресное доказательство',f"{normative20.get('evidence_coverage_pct',0)}%",'Документ + страница','info')
        st.caption(
            'Наличие сведений и структура могут подтверждаться детерминированно. Смысловое выполнение, содержание графической части, '
            'полнота обязательного набора, структурированное значение и межраздельная согласованность требуют своего доказательного контракта. '
            'Для смысловой проверки проверяющая модель получает до четырёх адресных кандидатов и обязана сослаться на конкретные ID доказательств. '
            'Недостаточность доказательства не является несоответствием.'
        )
        st.dataframe(pd.DataFrame([{
            'Результат':row.get('state') or '—',
            'Тип доказательства':proof_type_label(row.get('proof_type')),
            'Состояние доказательства':proof_state_label(row.get('proof_state')),
            'Кандидатов доказательства':row.get('retrieval_candidate_count') or 0,
            'НТД':row.get('source') or row.get('document_id') or '—',
            'Пункт':row.get('paragraph') or '—',
            'Требование':row.get('requirement') or '—',
            'Основное доказательство':(
                f"{row.get('evidence_document')}, стр. {row.get('evidence_page')}"
                if row.get('evidence_document') and row.get('evidence_page') not in (None,'')
                else 'Не сформировано'
            ),
            'Выбранные доказательства':_semantic_trace(row) or '—',
            'Решение проверяющей модели':judge_label((row.get('semantic_proof') or {}).get('judge_verdict')) if row.get('semantic_proof') else '—',
            'Достоверность проверяющей модели':(row.get('semantic_proof') or {}).get('judge_confidence') if row.get('semantic_proof') else '—',
            'Провайдер проверяющей модели':(row.get('semantic_proof') or {}).get('judge_provider') or '—',
            'Контрольная модель':('Приняла' if (row.get('semantic_proof') or {}).get('critic_accept') is True else 'Не приняла') if row.get('semantic_proof') else '—',
            'Достоверность контрольной модели':(row.get('semantic_proof') or {}).get('critic_confidence') if row.get('semantic_proof') else '—',
            'Провайдер контрольной модели':(row.get('semantic_proof') or {}).get('critic_provider') or '—',
            'Независимость моделей':('Да' if (row.get('semantic_proof') or {}).get('independent') is True else 'Нет') if row.get('semantic_proof') else '—',
            'Фрагмент':row.get('evidence_fragment') or '',
            'Обоснование':row.get('reason') or '',
        } for row in normative20_rows]).head(160),hide_index=True,width='stretch')

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
