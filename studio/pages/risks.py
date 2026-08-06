from __future__ import annotations

import pandas as pd
import streamlit as st

from core.expert_review_engine import build_expert_risks, summarize_risks
from studio.components import hero, card, section, empty


def _checklist_results() -> list[dict]:
    run = st.session_state.get("checklist_run") or {}
    rows = run.get("results") if isinstance(run, dict) else None
    return rows if isinstance(rows, list) else []


def render(ctx) -> None:
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero(
        "Риски экспертизы",
        "Предварительная оценка риска замечаний на основе состава проекта, межраздельных проверок и чек-листов.",
        "Expert Review Engine · выводы не являются гарантией позиции эксперта",
    )
    if not st.session_state.get("object_registry_confirmed"):
        st.warning("Сначала подтвердите состав проектируемых объектов. Оценка рисков заблокирована, чтобы не строить выводы по ошибочному реестру.")
        return

    risks = build_expert_risks(
        comparisons.to_dict("records") if not comparisons.empty else [],
        st.session_state.get("object_assembly_rows") or [],
        _checklist_results(),
    )
    summary = summarize_risks(risks)
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Всего рисков", summary["total"], "Сформировано по доказуемым результатам")
    with c2: card("Высокий", summary["high"], "Требуют первоочередной проверки", "bad" if summary["high"] else "ok")
    with c3: card("Средний", summary["medium"], "Желательно устранить до подачи", "warn" if summary["medium"] else "ok")
    with c4: card("Низкий", summary["low"], "Редакционные и локальные вопросы", "info")

    section("Карта рисков", "Формулировка возможного замечания является прогнозом ExpertCheck, а не цитатой будущего заключения.")
    if not risks:
        empty("Риски не сформированы", "Нет подтверждённых расхождений либо недостаточно данных для оценки.")
        return

    filters = st.columns([1, 1, 2])
    levels = ["Все", "Высокий", "Средний", "Низкий"]
    selected_level = filters[0].selectbox("Уровень", levels)
    categories = ["Все"] + sorted({str(x.get("category")) for x in risks})
    selected_category = filters[1].selectbox("Категория", categories)
    query = filters[2].text_input("Поиск по объекту или показателю")

    selected = []
    for risk in risks:
        if selected_level != "Все" and risk["level"] != selected_level:
            continue
        if selected_category != "Все" and risk["category"] != selected_category:
            continue
        blob = f"{risk['object']} {risk['parameter']} {risk['finding']}".lower()
        if query and query.lower() not in blob:
            continue
        selected.append(risk)

    table = pd.DataFrame([{
        "Риск": x["level"],
        "Категория": x["category"],
        "Объект": x["object"] or "—",
        "Вопрос": x["parameter"],
        "Оценка": x["score"],
    } for x in selected])
    st.dataframe(table, hide_index=True, width="stretch")

    section("Карточки риска", "Откройте карточку, чтобы увидеть основание, возможную формулировку и рекомендуемое действие.")
    for risk in selected[:50]:
        title = f"{risk['level']} · {risk['category']} · {risk['object'] or risk['parameter']}"
        with st.expander(title):
            st.write("**Выявленная проблема**")
            st.write(risk["finding"])
            st.write("**Возможная формулировка замечания**")
            st.info(risk["possible_remark"])
            st.write("**Рекомендуемое действие**")
            st.write(risk["recommendation"])
            if risk.get("sources"):
                st.write("**Источники**")
                st.write(risk["sources"])
            st.caption(f"Источник оценки: {risk['origin']} · Risk ID: {risk['risk_id']}")
