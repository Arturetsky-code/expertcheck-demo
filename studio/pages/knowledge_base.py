from __future__ import annotations

from pathlib import Path

import streamlit as st

from core20.normative_foundation import NormativeKnowledgeFoundation20
from core20.expert_history import ExpertHistoryCorpus20


def _foundation():
    root=Path(__file__).resolve().parents[2]/"knowledge"
    return NormativeKnowledgeFoundation20(root)


def render(ctx):
    st.title("НТД и экспертная практика")
    st.caption(
        "Фундамент нормативной базы ExpertCheck: каталог документов, верифицированные атомарные пункты, "
        "маршрутизация применимых требований и историческая практика экспертизы."
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
        a.metric("Применимых маршрутов",knowledge.get("project_relevant",0))
        b.metric("Маршрутов по verified-clause",knowledge.get("project_verified_clause_routes",0))
        c.metric("Готовых контрактов",knowledge.get("project_automatic_contract_ready",0))
        d.metric("Приоритет по истории",knowledge.get("project_history_prioritized",0))
        sections=knowledge.get("project_sections") or []
        if sections:
            st.caption("Распознанные разделы проекта: "+", ".join(sections))

        rows=list(knowledge.get("priority_routes") or [])
        execution=dict(manifest.get("normative_execution") or {})
        execution_rows=list(execution.get("rows") or [])
        if execution_rows:
            st.subheader("Исполнение verified-clause")
            e1,e2,e3,e4=st.columns(4)
            e1.metric("Исполняемых контрактов",execution.get("contracts",0))
            e2.metric("Подтверждено",execution.get("verified_ok",0))
            e3.metric("Вопросов специалисту",execution.get("review_questions",0))
            e4.metric("Не проверено системой",execution.get("system_limitations",0))
            st.caption(
                f"Адресное покрытие evidence: {execution.get('evidence_coverage_pct',0)}%. "
                "Ненайденный текст не превращается в нормативное несоответствие."
            )
            st.dataframe([{
                "Результат":x.get("state") or "",
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
            "Цель Alpha 8 — отделить размер корпуса НТД от реально исполняемого доказательного покрытия. "
            "Наличие документа в базе само по себе не означает, что его требования уже исполняются автоматически."
        )
