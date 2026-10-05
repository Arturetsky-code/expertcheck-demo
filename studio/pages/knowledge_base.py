from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.ai_gateway import provider_for_role
from core20.normative_foundation import NormativeKnowledgeFoundation20
from core20.expert_history import ExpertHistoryCorpus20
from core20.normative_semantic_proof import run_normative_semantic_proof
from core20.normative_visual_proof import run_normative_visual_proof
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


def _current_semantic_checkpoint() -> dict:
    result=st.session_state.get("result")
    if not isinstance(result,(list,tuple)) or not result:
        return {}
    documents=result[0]
    if isinstance(documents,list) and documents and isinstance(documents[0],dict):
        return dict(documents[0].get("normative_semantic_proof") or {})
    return {}


def _persist_normative_visual_proof(value:dict) -> bool:
    """Persist resumable visual proof beside the project snapshot."""
    result=st.session_state.get("result")
    if not isinstance(result,(list,tuple)) or not result:
        return False
    documents=result[0]
    if isinstance(documents,list) and documents and isinstance(documents[0],dict):
        documents[0]["normative_visual_proof"]=dict(value or {})
        return True
    return False


def _current_visual_state()->tuple[dict,dict]:
    result=st.session_state.get("result")
    if not isinstance(result,(list,tuple)) or not result:
        return {},{}
    documents=result[0]
    if isinstance(documents,list) and documents and isinstance(documents[0],dict):
        return (
            dict(documents[0].get("visual_evidence_cache") or {}),
            dict(documents[0].get("normative_visual_proof") or {}),
        )
    return {},{}


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
                "Удержано proof-контролем",
                execution.get("demoted_keyword_only_remaining",execution.get("demoted_keyword_only",0)),
            )
            p5.metric("Очередь смысловой проверки",execution.get("semantic_queue_total",0))

            e1,e2,e3,e4=st.columns(4)
            e1.metric("Смысл подтверждён",execution.get("semantic_proof_applied",0))
            e2.metric("Вопросов специалисту",execution.get("review_questions",0))
            e3.metric("Не проверено системой",execution.get("system_limitations",0))
            e4.metric("Адресное доказательство",f"{execution.get('evidence_coverage_pct',0)}%")
            graphic_structural_count=int(execution.get("graphic_structural_proof_count") or 0)
            if graphic_structural_count:
                st.caption(
                    f"Графических требований закрыто структурным proof без AI: {graphic_structural_count}. "
                    "Они не потеряны: после подтверждения доверенной структурой листа они выходят из очереди Visual Proof."
                )
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
                    f"Доказательный контроль исходно удержал {initial_held} контрактов после admissible retrieval/inventory; "
                    f"после накопленных смысловых решений в этом контуре осталось {remaining_held}. "
                    "Recoverable weak/near-miss кандидаты учитываются отдельно в смысловой очереди."
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

                    visual_diag=dict(frontier.get("visual_pending") or {})
                    if visual_diag.get("total"):
                        with st.expander(
                            f"Visual Proof · {int(visual_diag.get('total') or 0)} графических контрактов",
                            expanded=True,
                        ):
                            st.caption(
                                "Для АР лист-кандидат должен быть подтверждён Drawing Intelligence по основной надписи и типу листа; "
                                "для ПЗУ используется General Plan Engine либо совместимый структурный preflight сохранённого проекта. "
                                "Ни один preflight сам по себе не подтверждает графическое содержание и не меняет нормативный вердикт."
                            )
                            visual_rows=list(visual_diag.get("rows") or [])
                            visual_kind_labels={
                                "PZU_SITE_LAYOUT":"ПЗУ · планировочная схема",
                                "PZU_RELIEF_EARTHWORKS":"ПЗУ · рельеф и земляные массы",
                                "PZU_UTILITY_NETWORKS":"ПЗУ · инженерные сети",
                                "PZU_SITUATION_PLAN":"ПЗУ · ситуационный план",
                                "AR_FACADES":"АР · фасады",
                                "AR_FLOOR_PLANS":"АР · поэтажные планы",
                                "AR_SECTIONS":"АР · разрезы",
                            }
                            st.dataframe([
                                {
                                    "ID":row.get("requirement_id") or "",
                                    "Тип visual-proof":visual_kind_labels.get(
                                        row.get("visual_kind") or "",
                                        row.get("visual_kind") or "",
                                    ),
                                    "Покрытие preflight":(
                                        f"{row.get('coverage_count') or 0}/"
                                        f"{row.get('total_count') or 0}"
                                    ),
                                    "Структурно подтверждено":(
                                        f"{row.get('structural_confirmed_count') or 0}/"
                                        f"{row.get('structural_target_count') or 0}"
                                    ),
                                    "Осталось структурно":row.get("structural_review_required_count") or 0,
                                    "Осталось визуально":row.get("visual_review_required_count") or 0,
                                    "Источник отбора":{
                                        "DRAWING_INTELLIGENCE_V2":"Drawing Intelligence 2.0",
                                        "GENERAL_PLAN_ENGINE":"General Plan Engine",
                                        "PZU_STRUCTURAL_PREFLIGHT":"ПЗУ structural preflight",
                                        "TEXT_LAYER":"Текстовый слой",
                                    }.get(
                                        row.get("selection_source") or "",
                                        row.get("selection_source") or "—",
                                    ),
                                    "Листов-кандидатов":row.get("candidate_page_count") or 0,
                                    "Не найдено в text-layer":"; ".join(
                                        row.get("missing_labels") or []
                                    ),
                                    "Тема":row.get("topic") or "",
                                }
                                for row in visual_rows
                            ],hide_index=True,width="stretch")

                            visual_item_queue=list(execution.get("visual_item_queue") or [])
                            if visual_item_queue:
                                st.markdown(
                                    f"**Очередь визуальной проверки · {len(visual_item_queue)} элементов**"
                                )
                                vq1,vq2,vq3=st.columns(3)
                                vq1.metric(
                                    "Адресно локализовано",
                                    int(execution.get("visual_item_queue_addressed") or 0),
                                )
                                vq2.metric(
                                    "Только на уровне листа",
                                    int(execution.get("visual_item_queue_sheet_fallback") or 0),
                                )
                                vq3.metric(
                                    "Без листа-кандидата",
                                    int(execution.get("visual_item_queue_unresolved") or 0),
                                )
                                st.caption(
                                    "Адресная локализация означает, что элемент уже привязан к конкретной странице. "
                                    "«Только на уровне листа» означает: нужный лист известен, но сам элемент ещё надо найти на графике. "
                                    "Эта очередь не меняет нормативный вердикт и не вызывает AI."
                                )
                                localization_labels={
                                    "ELEMENT_ADDRESS":"Адрес элемента",
                                    "CONTRACT_SHEET_FALLBACK":"Лист-кандидат",
                                    "UNRESOLVED":"Лист не локализован",
                                }
                                with st.expander(
                                    "Показать элементную очередь Visual Proof",
                                    expanded=True,
                                ):
                                    st.dataframe([
                                        {
                                            "ID":item.get("requirement_id") or "",
                                            "Элемент":item.get("label") or "",
                                            "Локализация":localization_labels.get(
                                                item.get("localization_source") or "",
                                                item.get("localization_source") or "—",
                                            ),
                                            "Листов":item.get("candidate_page_count") or 0,
                                            "Документ":(
                                                (item.get("candidate_pages") or [{}])[0].get("document") or ""
                                            ),
                                            "Страница":(
                                                (item.get("candidate_pages") or [{}])[0].get("page")
                                            ),
                                            "Тема":item.get("topic") or "",
                                        }
                                        for item in visual_item_queue
                                    ],hide_index=True,width="stretch")

                                cache_summary=dict(execution.get("visual_evidence_cache_summary") or {})
                                page_batches=list(execution.get("visual_page_batches") or [])
                                if cache_summary.get("version"):
                                    st.markdown("**Visual Evidence Cache**")
                                    vc1,vc2,vc3,vc4,vc5=st.columns(5)
                                    vc1.metric("Сохранено страниц",int(cache_summary.get("cached_pages") or 0))
                                    vc2.metric("Основных page-batches",int(execution.get("visual_page_batch_total") or 0))
                                    vc3.metric("Элементов покрыто",int(execution.get("visual_page_batch_items") or 0))
                                    vc4.metric("Резервных страниц",int(execution.get("visual_page_batch_fallback_total") or 0))
                                    vc5.metric("Без кэшированной страницы",int(execution.get("visual_page_batch_unresolved") or 0))
                                    st.caption(
                                        "Кэш сохраняет адресные страницы Visual Proof для повторного открытия проекта. "
                                        "Первый проход vision использует минимальное rank-aware покрытие: один основной лист может закрывать несколько элементов; "
                                        "остальные кэшированные листы остаются резервными и не создают AI-вызов до необходимости."
                                    )
                                    if page_batches:
                                        with st.expander(
                                            "Основной план страниц для Visual AI",
                                            expanded=True,
                                        ):
                                            st.dataframe([
                                                {
                                                    "Документ":batch.get("document") or "",
                                                    "Страница":batch.get("page"),
                                                    "Элементов":batch.get("item_count") or 0,
                                                    "Элементы":"; ".join(batch.get("labels") or []),
                                                    "Кэш":batch.get("cache_id") or "",
                                                    "Размер, КБ":round(int(batch.get("image_bytes") or 0)/1024,1),
                                                }
                                                for batch in page_batches
                                            ],hide_index=True,width="stretch")
                                    fallback_pages=list(execution.get("visual_page_fallbacks") or [])
                                    if fallback_pages:
                                        with st.expander(
                                            f"Резервные страницы · {len(fallback_pages)}",
                                            expanded=False,
                                        ):
                                            st.dataframe([
                                                {
                                                    "Документ":row.get("document") or "",
                                                    "Страница":row.get("page"),
                                                    "Может помочь элементам":row.get("item_count") or 0,
                                                    "Элементы":"; ".join(row.get("labels") or []),
                                                    "Лучший ранг":row.get("best_rank") or "",
                                                    "Кэш":row.get("cache_id") or "",
                                                }
                                                for row in fallback_pages
                                            ],hide_index=True,width="stretch")
                                else:
                                    st.caption(
                                        "Visual Evidence Cache для этого сохранённого проекта ещё не сформирован. "
                                        "После обновления достаточно один раз повторно проанализировать исходные PDF; "
                                        "после этого адресные страницы будут сохраняться вместе с проектом."
                                    )

                            visual_proof_summary=dict(execution.get("visual_proof_summary") or {})
                            if execution.get("visual_proof_applied"):
                                st.success(
                                    f"Независимый Visual Proof подтвердил элементов: {execution.get('visual_proof_applied',0)}; "
                                    f"полностью закрыто графических контрактов: {execution.get('visual_contracts_confirmed',0)}."
                                )
                            if execution.get("visual_proof_stale"):
                                st.warning(
                                    "Часть сохранённого Visual Proof относится к другой версии страницы/элемента и не применена."
                                )
                            visual_provider_errors=[
                                str(value) for value in (visual_proof_summary.get("provider_errors") or [])
                                if str(value).strip()
                            ]
                            if visual_provider_errors:
                                st.warning(_provider_error_summary(visual_provider_errors))

                            if visual_item_queue and page_batches:
                                st.caption(
                                    "Visual AI получает только сохранённое изображение одной адресной страницы и список элементов для неё. "
                                    "Положительный proof требует независимого согласия двух фактически разных vision-провайдеров; "
                                    "NOT_PROVEN/UNREADABLE никогда не создают нарушение."
                                )
                                if st.button(
                                    "Проверить графические элементы двумя vision-моделями",
                                    type="primary",
                                    key="normative_visual_proof",
                                ):
                                    visual_cache,visual_checkpoint=_current_visual_state()
                                    judge=provider_for_role("judge",st.session_state,st.secrets)
                                    critic=provider_for_role("critic",st.session_state,st.secrets)
                                    if judge is None or critic is None:
                                        st.error(
                                            "Для Visual Proof настройте проверяющую и контрольную модели в разделе «Настройки → AI-модули»."
                                        )
                                    else:
                                        with st.spinner(
                                            "Проверяем сохранённые графические страницы Visual Judge → независимый Visual Critic..."
                                        ):
                                            visual_proof=run_normative_visual_proof(
                                                visual_item_queue,
                                                page_batches=page_batches,
                                                visual_cache=visual_cache,
                                                judge_provider=judge,
                                                critic_provider=critic,
                                                limit_batches=4,
                                                checkpoint=visual_checkpoint,
                                            )
                                        if not _persist_normative_visual_proof(visual_proof):
                                            st.error("Не удалось сохранить Visual Proof в цифровой снимок проекта.")
                                        else:
                                            errors=list(visual_proof.get("provider_errors") or [])
                                            if errors:
                                                st.warning(_provider_error_summary(errors))
                                            else:
                                                st.success(
                                                    f"Visual Proof: новых подтверждений {visual_proof.get('newly_confirmed',0)}; "
                                                    f"всего подтверждено {visual_proof.get('confirmed_total',0)} из {visual_proof.get('queue_total',0)}; "
                                                    f"обработано page-batches {visual_proof.get('processed_batches',0)}."
                                                )
                                            st.rerun()

                            visual_page_rows=[]
                            visual_element_rows=[]
                            for row in visual_rows:
                                requirement_id=row.get("requirement_id") or ""
                                visual_kind=visual_kind_labels.get(
                                    row.get("visual_kind") or "",
                                    row.get("visual_kind") or "",
                                )
                                for rank,page in enumerate(row.get("candidate_pages") or [],1):
                                    visual_page_rows.append({
                                        "ID":requirement_id,
                                        "Тип":visual_kind,
                                        "Ранг":rank,
                                        "Документ":page.get("document") or "",
                                        "Страница":page.get("page"),
                                        "Раздел":page.get("section") or "",
                                        "Источник":{
                                            "DRAWING_INTELLIGENCE_V2":"Drawing Intelligence 2.0",
                                            "GENERAL_PLAN_ENGINE":"General Plan Engine",
                                            "PZU_STRUCTURAL_PREFLIGHT":"ПЗУ structural preflight",
                                            "TEXT_LAYER":"Текстовый слой",
                                        }.get(
                                            page.get("selection_source") or "",
                                            page.get("selection_source") or "—",
                                        ),
                                        "Типы листа":"; ".join(page.get("drawing_kinds") or []),
                                        "Объект листа":page.get("object_name") or "",
                                        "Обозначение":page.get("designation") or "",
                                        "Совпавшие элементы":"; ".join(
                                            page.get("element_hit_labels") or []
                                        ),
                                        "Маркеры":"; ".join(page.get("marker_hits") or []),
                                        "Фрагмент":page.get("fragment") or "",
                                    })
                                for element in row.get("elements") or []:
                                    locations=list(element.get("candidate_locations") or [])
                                    first=locations[0] if locations else {}
                                    status_labels={
                                        "STRUCTURAL_CONFIRMED":"Подтверждено структурно",
                                        "STRUCTURAL_REINDEX_REQUIRED":"Нужна структурная переиндексация",
                                        "STRUCTURAL_NOT_LOCATED":"Структурно не локализовано",
                                        "VISUAL_REVIEW_REQUIRED":"Нужна визуальная проверка",
                                        "VISUAL_NOT_LOCATED":"Визуальный элемент не локализован",
                                    }
                                    mode_labels={
                                        "SHEET_PRESENCE":"Наличие листа/таблицы",
                                        "VISUAL_CONTENT":"Содержание графики",
                                    }
                                    visual_element_rows.append({
                                        "ID":requirement_id,
                                        "Элемент":element.get("label") or element.get("id") or "",
                                        "Режим":mode_labels.get(
                                            element.get("verification_mode") or "",
                                            element.get("verification_mode") or "—",
                                        ),
                                        "Статус proof":status_labels.get(
                                            element.get("proof_status") or "",
                                            element.get("proof_status") or "—",
                                        ),
                                        "Text-layer":"Есть маркер" if element.get("matched_in_text_layer") else "Не найден",
                                        "Документ":first.get("document") or "",
                                        "Страница":first.get("page"),
                                        "Фрагмент":first.get("fragment") or "",
                                    })

                            if visual_element_rows:
                                st.markdown("**Элементы visual-контрактов**")
                                st.dataframe(
                                    visual_element_rows,
                                    hide_index=True,
                                    width="stretch",
                                )
                            if visual_page_rows:
                                with st.expander(
                                    "Адресные листы-кандидаты для визуальной проверки",
                                    expanded=True,
                                ):
                                    st.dataframe(
                                        visual_page_rows,
                                        hide_index=True,
                                        width="stretch",
                                    )

                            rejected_rows=[]
                            for row in visual_rows:
                                for rejected in row.get("rejected_untrusted_pages") or []:
                                    rejected_rows.append({
                                        "ID":row.get("requirement_id") or "",
                                        "Документ":rejected.get("document") or "",
                                        "Страница":rejected.get("page"),
                                        "Распознанные типы листа":"; ".join(
                                            rejected.get("drawing_kinds") or []
                                        ),
                                        "Почему отклонено":rejected.get("reason") or "",
                                    })
                            if rejected_rows:
                                with st.expander(
                                    "Отклонённые страницы visual-preflight",
                                    expanded=False,
                                ):
                                    st.dataframe(
                                        rejected_rows,
                                        hide_index=True,
                                        width="stretch",
                                    )

                    set_diag=dict(frontier.get("set_completeness") or {})
                    if set_diag.get("total"):
                        with st.expander(
                            f"Контракты полноты обязательного набора · {int(set_diag.get('total') or 0)}",
                            expanded=True,
                        ):
                            set_rows=list(set_diag.get("rows") or [])
                            st.dataframe([
                                {
                                    "ID":row.get("requirement_id") or "",
                                    "НТД":row.get("source") or "",
                                    "Пункт":row.get("paragraph") or "",
                                    "Разделы":row.get("sections") or "",
                                    "Покрытие обязательных":(
                                        f"{row.get('matched_count') or 0}/{row.get('required_count') or 0}"
                                        if row.get("total_count") is not None
                                        else f"{row.get('matched_count') or 0}/?"
                                    ),
                                    "Применимость ожидает":int(
                                        row.get("applicability_pending_count") or 0
                                    ),
                                    "Не подтверждено":"; ".join(row.get("missing_labels") or []),
                                    "Не доказана применимость":"; ".join(
                                        row.get("applicability_pending_labels") or []
                                    ),
                                    "Инвентарь":"; ".join(row.get("observed_inventory") or []),
                                    "Кандидатов evidence":row.get("retrieval_candidate_count") or 0,
                                    "Тема":row.get("topic") or "",
                                }
                                for row in set_rows
                            ],hide_index=True,width="stretch")

                            element_rows=[]
                            set_near_miss_rows=[]
                            for row in set_rows:
                                requirement_id=row.get("requirement_id") or ""
                                for element in row.get("elements") or []:
                                    evidence=list(element.get("evidence") or [])
                                    first=evidence[0] if evidence else {}
                                    applicability_state=str(
                                        element.get("applicability_state") or "REQUIRED"
                                    )
                                    if element.get("matched"):
                                        element_status="Найден"
                                    elif applicability_state=="APPLICABILITY_PENDING":
                                        element_status="Применимость не доказана"
                                    else:
                                        element_status="Не найден"
                                    applicability_trace=list(
                                        element.get("applicability_trace") or []
                                    )
                                    applicability_first=(
                                        applicability_trace[0] if applicability_trace else {}
                                    )
                                    element_rows.append({
                                        "ID":requirement_id,
                                        "Элемент":element.get("label") or element.get("id") or "",
                                        "Статус":element_status,
                                        "Признак применимости":applicability_first.get(
                                            "matched_condition"
                                        ) or "",
                                        "Документ применимости":applicability_first.get(
                                            "document"
                                        ) or "",
                                        "Страница применимости":applicability_first.get("page"),
                                        "Документ":first.get("document") or "",
                                        "Страница":first.get("page"),
                                        "Фрагмент":first.get("fragment") or "",
                                    })
                                    if element.get("matched") or applicability_state=="APPLICABILITY_PENDING":
                                        continue
                                    for rank,candidate in enumerate(element.get("near_misses") or [],1):
                                        group_diag_parts=[]
                                        for diag in candidate.get("group_diagnostics") or []:
                                            span=diag.get("span_chars")
                                            if diag.get("matched"):
                                                detail="OK"
                                            elif diag.get("reason")=="TERMS_TOO_FAR_APART":
                                                detail=f"слова далеко ({span} симв.)"
                                            elif diag.get("missing_stems"):
                                                detail=(
                                                    "нет стемов: "
                                                    + ", ".join(diag.get("missing_stems") or [])
                                                )
                                            else:
                                                detail=diag.get("reason") or "не совпало"
                                            group_diag_parts.append(
                                                f"{diag.get('group') or 'группа'}: {detail}"
                                            )
                                        set_near_miss_rows.append({
                                            "ID":requirement_id,
                                            "Элемент":element.get("label") or element.get("id") or "",
                                            "Ранг":rank,
                                            "Документ":candidate.get("document") or "",
                                            "Страница":candidate.get("page"),
                                            "Раздел":candidate.get("section") or "",
                                            "Совпавшие термины":", ".join(candidate.get("matched_terms") or []),
                                            "Лексическое пересечение":(
                                                f"{candidate.get('overlap_count') or 0}/"
                                                f"{candidate.get('query_term_count') or 0}"
                                            ),
                                            "Обязательные группы":(
                                                f"{candidate.get('required_group_matched') or 0}/"
                                                f"{candidate.get('required_group_total') or 0}"
                                            ),
                                            "Не хватает":"; ".join(candidate.get("missing_groups") or []),
                                            "Диагностика групп":"; ".join(group_diag_parts),
                                            "Фрагмент":candidate.get("fragment") or "",
                                        })

                            if element_rows:
                                with st.expander("Элементы обязательных наборов",expanded=True):
                                    st.caption(
                                        "Для каждого элемента отдельно показаны применимость и evidence. "
                                        "«Применимость не доказана» и «Не найден» не являются автоматическим нарушением."
                                    )
                                    st.dataframe(
                                        element_rows,
                                        hide_index=True,
                                        width="stretch",
                                    )
                            if set_near_miss_rows:
                                with st.expander(
                                    "Near-miss для отсутствующих элементов набора",
                                    expanded=True,
                                ):
                                    st.caption(
                                        "Это страницы с частичным лексическим пересечением. "
                                        "Они нужны только для диагностики retrieval и не закрывают элемент набора."
                                    )
                                    st.dataframe(
                                        set_near_miss_rows,
                                        hide_index=True,
                                        width="stretch",
                                    )

                    applicability_diag=dict(frontier.get("applicability_trace") or {})
                    if applicability_diag.get("total"):
                        with st.expander(
                            f"Доказательства применимости · {int(applicability_diag.get('total') or 0)}",
                            expanded=True,
                        ):
                            st.caption(
                                "Эти адресные признаки разрешают перейти к proof-контракту, "
                                "но сами по себе не подтверждают выполнение нормативного требования."
                            )
                            st.dataframe([
                                {
                                    "ID":row.get("requirement_id") or "",
                                    "НТД":row.get("source") or "",
                                    "Пункт":row.get("paragraph") or "",
                                    "Документ":row.get("document") or "",
                                    "Страница":row.get("page"),
                                    "Признак":row.get("matched_condition") or "",
                                    "Фрагмент":row.get("fragment") or "",
                                }
                                for row in applicability_diag.get("rows") or []
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
                                limit=4,
                                checkpoint=_current_semantic_checkpoint(),
                            )
                        if not _persist_normative_semantic_proof(proof):
                            st.error("Не удалось сохранить результат смысловой проверки в цифровой снимок проекта.")
                        else:
                            if proof.get("provider_errors"):
                                st.warning(_provider_error_summary(proof.get("provider_errors") or []))
                            else:
                                st.success(
                                    f"Смысловая волна завершена: обработано {proof.get('new_decisions',proof.get('selected',0))}; "
                                    f"новых подтверждений {proof.get('newly_verified_ok',proof.get('verified_ok',0))}; "
                                    f"ещё не обработано {proof.get('pending_unprocessed',0)}. "
                                    f"Ранее завершённые решения сохранены: {proof.get('completed_before',0)}."
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
