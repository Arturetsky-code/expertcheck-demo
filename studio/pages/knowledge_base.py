from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.ai_gateway import provider_for_role
from core20.normative_foundation import NormativeKnowledgeFoundation20
from core20.expert_history import ExpertHistoryCorpus20
from core20.normative_semantic_proof import run_normative_semantic_proof


def _foundation():
    root=Path(__file__).resolve().parents[2]/"knowledge"
    return NormativeKnowledgeFoundation20(root)


def _persist_normative_semantic_proof(value:dict) -> bool:
    """Persist Alpha 9 proof beside the project result so normal workspace save keeps it."""
    result=st.session_state.get("result")
    if not isinstance(result,(list,tuple)) or not result:
        return False
    documents=result[0]
    if isinstance(documents,list) and documents and isinstance(documents[0],dict):
        documents[0]["normative_semantic_proof"]=dict(value or {})
        return True
    return False


def render(ctx):
    st.title("НТД и экспертная практика")
    st.caption(
        "Фундамент нормативной базы ExpertCheck: каталог документов, верифицированные атомарные пункты, "
        "маршрутизация требований, доказательная проверка и историческая практика экспертизы."
    )

    foundation=_foundation()
    summary=foundation.summary()
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Документов в каталоге",summary.get("document_catalog_total",0))
    c2.metric("Статусов в реестре",summary.get("validity_registry_total",0))
    c3.metric("Атомарных требований",summary.get("atomic_requirements_total",0))
    c4.metric("Верифицированных пунктов",summary.get("verified_clauses",0))
    c5.metric("Проектов, связанных с НТД",summary.get("history_projects",0))

    st.info(
        "История замечаний экспертизы используется только для приоритизации и поиска аналогов. "
        "Она не превращает повторяющееся замечание в автоматический нормативный вердикт. "
        "Категорический вывод разрешается только при подтверждённом источнике, verified-clause и доказательстве в проекте."
    )

    history=ExpertHistoryCorpus20(Path(__file__).resolve().parents[2]/"knowledge")
    hs=history.summary()
    h1,h2,h3,h4=st.columns(4)
    h1.metric("Исторических проектов",hs.get("projects",0))
    h2.metric("Замечаний в корпусе",hs.get("records",0))
    h3.metric("С ответом",hs.get("records_with_response",0))
    h4.metric("Повторных/уточняющих",hs.get("repeat_records",0))
    st.caption(
        "«Проектов, связанных с НТД» — уникальные проекты, упомянутые в реестре нормативной практики; "
        "«Исторических проектов» — фактически загруженные проектные корпуса замечаний и ответов."
    )

    manifest=st.session_state.get("canonical_core_20_manifest") or {}
    knowledge=manifest.get("knowledge_foundation") or {}
    if knowledge:
        st.subheader("Маршрут текущего проекта")
        a,b,c,d=st.columns(4)
        a.metric("Маршрутов по распознанным разделам",knowledge.get("project_relevant",0))
        b.metric("Маршрутов по verified-clause",knowledge.get("project_verified_clause_routes",0))
        c.metric("Готовых контрактов",knowledge.get("project_automatic_contract_ready",0))
        d.metric("Приоритет по истории",knowledge.get("project_history_prioritized",0))
        sections=knowledge.get("project_sections") or []
        if sections:
            st.caption("Распознанные разделы проекта: "+", ".join(sections))
        st.caption(
            "Маршрут по разделу означает релевантность для проверки, но сам по себе не доказывает юридическую применимость "
            "условного требования и не является результатом проверки."
        )

        rows=list(knowledge.get("priority_routes") or [])
        execution=dict(manifest.get("normative_execution") or {})
        execution_rows=list(execution.get("rows") or [])
        if execution_rows:
            st.subheader("Исполнение verified-clause")
            retrieval=dict(execution.get("retrieval") or {})
            p1,p2,p3,p4,p5=st.columns(5)
            p1.metric("Исполняемых контрактов",execution.get("contracts",0))
            p2.metric("Retrieval-кандидатов",retrieval.get("verified_ok",execution.get("verified_ok",0)))
            p3.metric("Доказано proof-gate",execution.get("verified_ok",0))
            p4.metric("Удержано proof-gate",execution.get("demoted_keyword_only",0))
            p5.metric("Semantic proof очередь",execution.get("semantic_queue_total",0))

            e1,e2,e3=st.columns(3)
            e1.metric("Вопросов специалисту",execution.get("review_questions",0))
            e2.metric("Не проверено системой",execution.get("system_limitations",0))
            e3.metric("Адресное evidence",f"{execution.get('evidence_coverage_pct',0)}%")
            st.caption(
                "Alpha 9 разделяет поиск кандидата и доказательство. Совпадение терминов — это retrieval, а не нормативное подтверждение. "
                "Ненайденный текст и недоказанный смысл не превращаются в несоответствие."
            )

            semantic_queue=list(execution.get("semantic_queue") or [])
            semantic_summary=dict(execution.get("semantic_proof_summary") or {})
            if execution.get("semantic_proof_applied"):
                st.success(
                    f"Независимый semantic proof подтвердил требований: {execution.get('semantic_proof_applied',0)}. "
                    "Эти строки прошли адресное evidence → Judge → независимый Critic → программный gate."
                )
            if execution.get("semantic_proof_stale"):
                st.warning("Сохранённый semantic proof относится к другой версии evidence-очереди и не применён.")
            if semantic_summary.get("provider_errors"):
                st.warning("Последний semantic proof завершён с ограничениями: "+" | ".join(semantic_summary.get("provider_errors") or []))

            if semantic_queue:
                st.info(
                    f"В очереди смыслового доказательства: {len(semantic_queue)}. "
                    "Запуск отправляет только ограниченные адресные evidence packets настроенным Judge и Critic; полные PDF не передаются."
                )
                if st.button(
                    "Проверить смысловые требования: Judge → Critic",
                    type="primary",
                    key="alpha9_normative_semantic_proof",
                ):
                    judge=provider_for_role("judge",st.session_state,st.secrets)
                    critic=provider_for_role("critic",st.session_state,st.secrets)
                    if judge is None or critic is None:
                        st.error("Для semantic proof настройте независимые провайдеры Judge и Critic в разделе «Настройки → AI-модули».")
                    else:
                        with st.spinner("Проверяем нормативные evidence packets независимыми Judge и Critic..."):
                            proof=run_normative_semantic_proof(
                                semantic_queue,
                                judge_provider=judge,
                                critic_provider=critic,
                                limit=24,
                            )
                        if not _persist_normative_semantic_proof(proof):
                            st.error("Не удалось сохранить normative proof в цифровой снимок проекта.")
                        else:
                            if proof.get("provider_errors"):
                                st.warning("Semantic proof сохранён fail-closed: "+" | ".join(proof.get("provider_errors") or []))
                            else:
                                st.success(
                                    f"Semantic proof завершён: подтверждено {proof.get('verified_ok',0)} из {proof.get('selected',0)} выбранных пакетов."
                                )
                            st.rerun()

            st.dataframe([{
                "Результат":x.get("state") or "",
                "Тип proof":x.get("proof_type") or "",
                "Proof state":x.get("proof_state") or "",
                "НТД":x.get("source") or x.get("document_id") or "",
                "Пункт":x.get("paragraph") or "",
                "Требование":x.get("requirement") or "",
                "Evidence":(
                    f"{x.get('evidence_document')}, стр. {x.get('evidence_page')}"
                    if x.get("evidence_document") and x.get("evidence_page") not in (None,"")
                    else ""
                ),
                "Фрагмент":x.get("evidence_fragment") or "",
                "Причина":x.get("reason") or "",
            } for x in execution_rows],hide_index=True,width="stretch")

            proof_counts=dict(execution.get("proof_type_counts") or {})
            if proof_counts:
                with st.expander("Профиль доказательных контрактов",expanded=False):
                    st.dataframe([
                        {"Тип proof":key,"Контрактов":value}
                        for key,value in proof_counts.items() if value
                    ],hide_index=True,width="stretch")
                    st.caption(
                        "PRESENCE/STRUCTURE допускают детерминированное подтверждение при выполненном контракте. "
                        "SEMANTIC_REQUIREMENT требует смыслового доказательства; GRAPHIC_CONTENT — отдельного визуального proof; "
                        "SET_COMPLETENESS — проверки полного обязательного набора."
                    )
    else:
        docs,_,_,_,_,_,_=ctx.data
        rows=foundation.project_routes(docs.to_dict("records") if hasattr(docs,"to_dict") else []).get("rows") or []

    st.subheader("Приоритетный нормативный маршрут")
    display=[]
    for row in rows:
        display.append({
            "Применимость":row.get("project_applicability_state") or "",
            "Доверие":row.get("trust_state") or "",
            "Документ":row.get("document_id") or "",
            "Статус источника":row.get("source_status") or "",
            "Пункт":row.get("paragraph") or "",
            "Тема":row.get("topic") or "",
            "Требование":row.get("requirement") or "",
            "Разделы":", ".join(row.get("sections") or []),
            "Тип проверки":row.get("check_kind") or "",
            "Автоконтракт":"Да" if row.get("automatic_contract_ready") else "Нет",
            "История замечаний":row.get("expert_occurrences") or 0,
            "Проектов в истории":row.get("expert_project_count") or 0,
            "Приоритет":row.get("verification_priority") or "",
        })
    if display:
        st.dataframe(display,hide_index=True,width="stretch")
    else:
        st.caption("Маршруты пока не сформированы.")

    with st.expander("Повторяющиеся паттерны экспертной практики",expanded=False):
        patterns=history.top_patterns(limit=20)
        if patterns:
            st.dataframe([
                {
                    "Раздел":x.get("section") or "",
                    "Паттерн":x.get("pattern") or "",
                    "Случаев":x.get("occurrences") or 0,
                    "Устранено":x.get("resolved") or 0,
                    "Повтор":x.get("repeated") or 0,
                    "Параметры":", ".join(x.get("parameter_codes") or []),
                    "Пример":x.get("example") or "",
                }
                for x in patterns
            ],hide_index=True,width="stretch")
        st.caption(
            "Эти данные — экспертная практика и обучающий корпус. Они повышают приоритет проверки и помогают искать аналоги, "
            "но сами по себе не являются нормативным основанием."
        )

    with st.expander("Состояние базы и backlog верификации",expanded=False):
        st.write({
            "Документы с подтверждённым статусом":summary.get("verified_document_statuses",0),
            "Пунктов с verified-clause":summary.get("verified_clauses",0),
            "Контрактов, готовых к автоматическому выводу":summary.get("automatic_contract_ready",0),
            "Пунктов в очереди на верификацию":summary.get("clause_verification_backlog",0),
            "Нормативных записей, связанных с историей экспертизы":summary.get("history_linked_normative_records",0),
            "Всего исторических упоминаний":summary.get("history_expert_occurrences",0),
        })
        st.caption(
            "Цель Alpha 9 — отделить релевантный retrieval от доказательства нормативного требования. "
            "Наличие документа или совпадение ключевых слов само по себе не означает VERIFIED_OK."
        )
