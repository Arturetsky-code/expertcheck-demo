from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.ai_gateway import provider_for_role
from core20.normative_foundation import NormativeKnowledgeFoundation20
from core20.expert_history import ExpertHistoryCorpus20
from core20.normative_semantic_proof import run_normative_semantic_proof
from core20.proof_labels import judge_label, proof_state_label, proof_type_label


def _foundation():
    root=Path(__file__).resolve().parents[2]/"knowledge"
    return NormativeKnowledgeFoundation20(root)


def _persist_normative_semantic_proof(value:dict) -> bool:
    """Persist normative proof beside the project result so workspace autosave keeps it."""
    result=st.session_state.get("result")
    if not isinstance(result,(list,tuple)) or not result:
        return False
    documents=result[0]
    if isinstance(documents,list) and documents and isinstance(documents[0],dict):
        documents[0]["normative_semantic_proof"]=dict(value or {})
        return True
    return False


def _semantic_trace(row:dict)->str:
    proof=dict(row.get("semantic_proof") or {})
    selected=list(proof.get("selected_evidence") or row.get("semantic_selected_evidence") or [])
    rendered=[]
    for item in selected:
        if not isinstance(item,dict):
            continue
        locator=str(item.get("source_locator") or "").strip()
        if not locator and item.get("document"):
            locator=f"{item.get('document')}, стр. {item.get('page')}"
        if locator and locator not in rendered:
            rendered.append(locator)
    return " | ".join(rendered)


def _provider_error_summary(errors:list[str]|None)->str:
    messages=[str(value or "") for value in (errors or []) if str(value or "").strip()]
    low=" ".join(messages).casefold()
    if "429" in low or "rate limit" in low or "лимит" in low:
        return "Лимит AI-провайдера временно исчерпан. Выполненные проверки сохранены; незавершённые пакеты можно продолжить позже."
    if "timeout" in low or "timed out" in low:
        return "AI-провайдер временно не ответил. Выполненные проверки сохранены; незавершённые пакеты остаются в очереди."
    return "Часть AI-запросов не была выполнена. Выполненные проверки сохранены; незавершённые пакеты остаются в очереди."


def _retrieval_trace(row:dict)->str:
    document=str(row.get("retrieval_evidence_document") or "").strip()
    page=row.get("retrieval_evidence_page")
    if document and page not in (None,""):
        return f"{document}, стр. {page}"
    return "—"


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
        "Категорический вывод разрешается только при подтверждённом источнике, верифицированном пункте и доказательстве в проекте."
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
        b.metric("Маршрутов по верифицированным пунктам",knowledge.get("project_verified_clause_routes",0))
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
            st.subheader("Исполнение верифицированных пунктов")
            retrieval=dict(execution.get("retrieval") or {})
            p1,p2,p3,p4,p5=st.columns(5)
            p1.metric("Исполняемых контрактов",execution.get("contracts",0))
            p2.metric("Кандидатов доказательства",retrieval.get("candidate_evidence",0))
            p3.metric("Доказано",execution.get("verified_ok",0))
            p4.metric(
                "Удержано сейчас",
                execution.get("demoted_keyword_only_remaining",execution.get("demoted_keyword_only",0)),
            )
            p5.metric("Очередь смысловой проверки",execution.get("semantic_queue_total",0))

            e1,e2,e3,e4=st.columns(4)
            e1.metric("Смысл подтверждён",execution.get("semantic_proof_applied",0))
            e2.metric("Вопросов специалисту",execution.get("review_questions",0))
            e3.metric("Не проверено системой",execution.get("system_limitations",0))
            e4.metric("Адресное доказательство",f"{execution.get('evidence_coverage_pct',0)}%")
            st.caption(
                "ExpertCheck разделяет поиск кандидата и доказательство. Совпадение терминов — это только поиск, а не нормативное подтверждение. "
                "Для смыслового требования система сохраняет до четырёх адресных кандидатов, а проверяющая модель должна выбрать конкретные доказательства. "
                "После независимого контроля выбранное доказательство становится каноническим proof trace; исходный retrieval сохраняется отдельно для аудита."
            )

            initial_held=int(execution.get("demoted_keyword_only_initial") or execution.get("demoted_keyword_only") or 0)
            remaining_held=int(
                execution.get("demoted_keyword_only_remaining")
                if execution.get("demoted_keyword_only_remaining") is not None
                else execution.get("demoted_keyword_only") or 0
            )
            if initial_held != remaining_held:
                st.caption(
                    f"Доказательный контроль исходно удержал {initial_held} контрактов; "
                    f"после накопленных смысловых решений в текущем остатке {remaining_held}."
                )

            frontier=dict(execution.get("proof_frontier") or {})
            blocker_counts=dict(frontier.get("blocker_counts") or {})
            if blocker_counts:
                blocker_labels={
                    "SEMANTIC_PENDING":"Смысловая очередь — ожидает Judge/Critic",
                    "SEMANTIC_REVIEWED_NO_PROMOTION":"Смысловая проверка завершена, но доказательство не принято",
                    "SET_COMPLETENESS_REQUIRED":"Нужен контракт полноты обязательного набора",
                    "STRUCTURED_PROOF_REQUIRED":"Нужен структурированный числовой/межраздельный контракт",
                    "VISUAL_PROOF_REQUIRED":"Нужна визуальная проверка графической части",
                    "PRESENCE_NOT_ADDRESSABLE":"Нет адресного доказательства наличия",
                    "RETAINED_FAIL_CLOSED":"Сохранено исходное неопределённое состояние",
                    "OTHER_UNRESOLVED":"Прочий незавершённый доказательный контракт",
                }
                with st.expander("Диагностика текущего остатка",expanded=True):
                    st.dataframe([
                        {
                            "Причина остатка":blocker_labels.get(code,code),
                            "Контрактов":count,
                        }
                        for code,count in sorted(
                            blocker_counts.items(),
                            key=lambda item:(-int(item[1] or 0),item[0]),
                        )
                        if int(count or 0)>0
                    ],hide_index=True,width="stretch")
                    st.caption(
                        "Это диагностическая раскладка текущего состояния. Она не меняет нормативные вердикты "
                        "и не вызывает AI; нужна для выбора следующего узкого улучшения."
                    )

                    semantic_diag=dict(frontier.get("semantic_pending") or {})
                    if semantic_diag.get("total"):
                        semantic_total=int(semantic_diag.get("total") or 0)
                        st.markdown(f"**Смысловая очередь — где сосредоточены {semantic_total} пакетов**")
                        semantic_sources=dict(semantic_diag.get("by_source") or {})
                        semantic_sections=dict(semantic_diag.get("by_section") or {})
                        semantic_evidence=dict(semantic_diag.get("by_evidence_candidates") or {})
                        semantic_admission=dict(semantic_diag.get("by_retrieval_admission") or {})
                        d1,d2,d3=st.columns(3)
                        with d1:
                            st.caption("По НТД")
                            st.dataframe([
                                {"НТД":key,"Пакетов":value}
                                for key,value in sorted(
                                    semantic_sources.items(),
                                    key=lambda item:(-int(item[1] or 0),item[0]),
                                )
                            ],hide_index=True,width="stretch")
                        with d2:
                            st.caption("По разделам проекта")
                            st.dataframe([
                                {"Разделы":key,"Пакетов":value}
                                for key,value in sorted(
                                    semantic_sections.items(),
                                    key=lambda item:(-int(item[1] or 0),item[0]),
                                )
                            ],hide_index=True,width="stretch")
                        with d3:
                            st.caption("По числу evidence-кандидатов")
                            st.dataframe([
                                {"Кандидатов evidence":key,"Пакетов":value}
                                for key,value in sorted(
                                    semantic_evidence.items(),
                                    key=lambda item:item[0],
                                )
                            ],hide_index=True,width="stretch")
                        if semantic_admission:
                            admission_labels={
                                "STRICT_RETRIEVAL":"Обычный retrieval-кандидат",
                                "WEAK_RETRIEVAL":"Слабый phrase-level retrieval → semantic",
                                "STRONG_NEAR_MISS":"Сильный token-level near-miss → semantic",
                                "OTHER":"Прочее происхождение",
                            }
                            st.caption("По происхождению evidence-кандидата")
                            st.dataframe([
                                {
                                    "Маршрут admission":admission_labels.get(code,code),
                                    "Пакетов":count,
                                }
                                for code,count in sorted(
                                    semantic_admission.items(),
                                    key=lambda item:(-int(item[1] or 0),item[0]),
                                )
                            ],hide_index=True,width="stretch")
                        with st.expander("Показать пакеты смысловой очереди",expanded=False):
                            route_labels={
                                "STRICT_RETRIEVAL":"обычный retrieval",
                                "WEAK_RETRIEVAL":"weak → semantic",
                                "STRONG_NEAR_MISS":"near-miss → semantic",
                                "OTHER":"прочее",
                            }
                            st.dataframe([
                                {
                                    "ID":row.get("requirement_id") or "",
                                    "НТД":row.get("source") or "",
                                    "Пункт":row.get("paragraph") or "",
                                    "Разделы":row.get("sections") or "",
                                    "Кандидатов evidence":row.get("retrieval_candidate_count") or 0,
                                    "Маршрут":route_labels.get(
                                        row.get("retrieval_admission") or "OTHER",
                                        "прочее",
                                    ),
                                    "Тема":row.get("topic") or "",
                                }
                                for row in semantic_diag.get("rows") or []
                            ],hide_index=True,width="stretch")

                    retained_diag=dict(frontier.get("retained_fail_closed") or {})
                    if retained_diag.get("total"):
                        retained_reason_labels={
                            "NORMATIVE_APPLICABILITY_NOT_PROVEN":"Условная применимость требования не доказана",
                            "NORMATIVE_STRUCTURE_PART_NOT_PROVEN":"Состав текстовой/графической частей не подтверждён",
                            "NORMATIVE_IOS_SUBSECTION_APPLICABILITY_PENDING":"Применимость подразделов ИОС требует проектной проверки",
                            "NORMATIVE_SECTION_EVIDENCE_MISSING":"В цифровом корпусе нет страниц ожидаемого раздела",
                            "NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND":"Адресное положительное evidence не найдено",
                            "NORMATIVE_EVIDENCE_WEAK":"Evidence найдено, но retrieval недостаточно сильный",
                            "UNSPECIFIED":"Причина не классифицирована",
                        }
                        st.markdown("**Исходно неопределённые — почему retrieval не дошёл до proof**")
                        retained_reasons=dict(retained_diag.get("by_reason") or {})
                        st.dataframe([
                            {
                                "Причина retrieval":retained_reason_labels.get(code,code),
                                "Контрактов":count,
                            }
                            for code,count in sorted(
                                retained_reasons.items(),
                                key=lambda item:(-int(item[1] or 0),item[0]),
                            )
                        ],hide_index=True,width="stretch")
                        with st.expander("Показать исходно неопределённые контракты",expanded=False):
                            st.dataframe([
                                {
                                    "ID":row.get("requirement_id") or "",
                                    "Причина":retained_reason_labels.get(
                                        row.get("reason_code") or "UNSPECIFIED",
                                        row.get("reason_code") or "UNSPECIFIED",
                                    ),
                                    "НТД":row.get("source") or "",
                                    "Пункт":row.get("paragraph") or "",
                                    "Разделы":row.get("sections") or "",
                                    "Кандидатов evidence":row.get("retrieval_candidate_count") or 0,
                                    "Тема":row.get("topic") or "",
                                }
                                for row in retained_diag.get("rows") or []
                            ],hide_index=True,width="stretch")

                        near_miss_rows=[]
                        for row in retained_diag.get("rows") or []:
                            if row.get("reason_code") not in {
                                "NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
                                "NORMATIVE_EVIDENCE_WEAK",
                            }:
                                continue
                            for rank,candidate in enumerate(row.get("near_misses") or [],1):
                                near_miss_rows.append({
                                    "ID":row.get("requirement_id") or "",
                                    "Ранг":rank,
                                    "Документ":candidate.get("document") or "",
                                    "Страница":candidate.get("page"),
                                    "Раздел":candidate.get("section") or "",
                                    "Совпавшие термины":", ".join(candidate.get("matched_terms") or []),
                                    "Пересечение":(
                                        f"{candidate.get('overlap_count') or 0}/"
                                        f"{candidate.get('query_term_count') or 0}"
                                    ),
                                    "Фрагмент":candidate.get("fragment") or "",
                                })
                        if near_miss_rows:
                            with st.expander("Ближайшие страницы для retrieval · диагностика",expanded=True):
                                st.caption(
                                    "Near-miss показывает страницы с частичным лексическим пересечением. "
                                    "Они не считаются доказательством и не меняют результат проверки."
                                )
                                st.dataframe(
                                    near_miss_rows,
                                    hide_index=True,
                                    width="stretch",
                                )

            semantic_queue=list(execution.get("semantic_queue") or [])
            semantic_summary=dict(execution.get("semantic_proof_summary") or {})
            provider_errors=[str(value) for value in semantic_summary.get("provider_errors") or [] if str(value).strip()]
            if execution.get("semantic_proof_applied"):
                st.success(
                    f"Независимая смысловая проверка подтвердила требований: {execution.get('semantic_proof_applied',0)}. "
                    "Эти строки прошли адресное доказательство → проверяющая модель → независимая контрольная модель → программный контроль."
                )
            if execution.get("semantic_proof_stale"):
                st.warning("Сохранённая смысловая проверка относится к другой версии набора доказательств и не применена.")
            if provider_errors and semantic_queue:
                st.warning(_provider_error_summary(provider_errors))
            if provider_errors and st.session_state.get("expert_mode"):
                with st.expander("Технические сообщения AI-провайдеров",expanded=False):
                    for message in provider_errors:
                        st.code(message)

            if semantic_queue:
                st.info(
                    f"В очереди смыслового доказательства: {len(semantic_queue)}; "
                    f"адресных кандидатов: {sum(len(packet.get('evidence') or []) for packet in semantic_queue)}. "
                    "Запуск передаёт только ограниченные адресные фрагменты настроенным проверяющей и контрольной моделям; полные PDF не передаются."
                )
                if st.button(
                    "Проверить смысловые требования двумя моделями",
                    type="primary",
                    key="normative_semantic_proof",
                ):
                    judge=provider_for_role("judge",st.session_state,st.secrets)
                    critic=provider_for_role("critic",st.session_state,st.secrets)
                    if judge is None or critic is None:
                        st.error("Для смысловой проверки настройте независимые проверяющую и контрольную модели в разделе «Настройки → AI-модули».")
                    else:
                        with st.spinner("Проверяем нормативные доказательства двумя независимыми моделями..."):
                            proof=run_normative_semantic_proof(
                                semantic_queue,
                                judge_provider=judge,
                                critic_provider=critic,
                                limit=24,
                            )
                        if not _persist_normative_semantic_proof(proof):
                            st.error("Не удалось сохранить результат смысловой проверки в цифровой снимок проекта.")
                        else:
                            if proof.get("provider_errors"):
                                st.warning(_provider_error_summary(proof.get("provider_errors") or []))
                            else:
                                st.success(
                                    f"Смысловая проверка завершена: подтверждено {proof.get('verified_ok',0)} из {proof.get('selected',0)} выбранных пакетов."
                                )
                            st.rerun()

            st.dataframe([{
                "Результат":x.get("state") or "",
                "Тип доказательства":proof_type_label(x.get("proof_type")),
                "Состояние доказательства":proof_state_label(x.get("proof_state")),
                "Кандидатов доказательства":x.get("retrieval_candidate_count") or 0,
                "НТД":x.get("source") or x.get("document_id") or "",
                "Пункт":x.get("paragraph") or "",
                "Требование":x.get("requirement") or "",
                "Каноническое доказательство":(
                    f"{x.get('evidence_document')}, стр. {x.get('evidence_page')}"
                    if x.get("evidence_document") and x.get("evidence_page") not in (None,"")
                    else ""
                ),
                "Исходный retrieval-кандидат":_retrieval_trace(x),
                "Выбранные доказательства":_semantic_trace(x) or "—",
                "Решение проверяющей модели":judge_label((x.get("semantic_proof") or {}).get("judge_verdict")) if x.get("semantic_proof") else "—",
                "Провайдер проверяющей модели":(x.get("semantic_proof") or {}).get("judge_provider") or "—",
                "Контрольная модель":("Приняла" if (x.get("semantic_proof") or {}).get("critic_accept") is True else "Не приняла") if x.get("semantic_proof") else "—",
                "Провайдер контрольной модели":(x.get("semantic_proof") or {}).get("critic_provider") or "—",
                "Независимость моделей":("Да" if (x.get("semantic_proof") or {}).get("independent") is True else "Нет") if x.get("semantic_proof") else "—",
                "Фрагмент канонического доказательства":x.get("evidence_fragment") or "",
                "Причина":x.get("reason") or "",
            } for x in execution_rows],hide_index=True,width="stretch")

            proof_counts=dict(execution.get("proof_type_counts") or {})
            if proof_counts:
                with st.expander("Профиль доказательных контрактов",expanded=False):
                    st.dataframe([
                        {"Тип доказательства":proof_type_label(key),"Контрактов":value}
                        for key,value in proof_counts.items() if value
                    ],hide_index=True,width="stretch")
                    st.caption(
                        "Наличие сведений и структура допускают детерминированное подтверждение при выполненном контракте. "
                        "Смысловое требование требует независимого смыслового доказательства; содержание графической части — отдельной визуальной проверки; "
                        "полнота набора — верифицированного перечня обязательных элементов."
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

    with st.expander("Состояние базы и очередь верификации",expanded=False):
        st.write({
            "Документы с подтверждённым статусом":summary.get("verified_document_statuses",0),
            "Пунктов с верифицированным содержанием":summary.get("verified_clauses",0),
            "Контрактов, готовых к автоматическому выводу":summary.get("automatic_contract_ready",0),
            "Пунктов в очереди на верификацию":summary.get("clause_verification_backlog",0),
            "Нормативных записей, связанных с историей экспертизы":summary.get("history_linked_normative_records",0),
            "Всего исторических упоминаний":summary.get("history_expert_occurrences",0),
        })
        st.caption(
            "Цель доказательного контура ExpertCheck — отделить релевантный поиск от доказательства нормативного требования. "
            "Наличие документа или совпадение ключевых слов само по себе не означает подтверждённое соответствие."
        )
