from __future__ import annotations

import pandas as pd
import streamlit as st

from core.project_completeness import (
    PROFILE_CAPITAL, PROFILE_LINEAR, USER_DECISIONS,
    build_matrix, summarize,
)
from studio.components import card, empty, section


def _document_types(docs: pd.DataFrame) -> list[str]:
    if docs.empty:
        return []
    for col in ("Раздел", "document_type", "section", "doc_type"):
        if col in docs.columns:
            return docs[col].fillna("").astype(str).tolist()
    return []


def render(ctx):
    docs = ctx.data[0]
    section("Комплектность проекта", "Автоматическая проверка наличия разделов и подтверждение состава пользователем.")
    if docs.empty:
        return empty("Сначала загрузите и проанализируйте документы на странице «Обзор».")

    profile = st.selectbox(
        "Профиль объекта",
        [PROFILE_CAPITAL, PROFILE_LINEAR],
        index=0 if st.session_state.get("completeness_profile", PROFILE_CAPITAL) == PROFILE_CAPITAL else 1,
        key="completeness_profile",
        help="Матрица верхнего уровня выбирается по типу объекта. Применимость отдельных разделов подтверждает пользователь.",
    )
    forming = st.toggle(
        "Комплект пока формируется",
        value=st.session_state.get("completeness_forming", True),
        key="completeness_forming",
        help="В этом режиме отсутствующие разделы не трактуются как финальная неполнота проекта.",
    )

    decisions = st.session_state.setdefault("completeness_decisions", {})
    base = build_matrix(_document_types(docs), profile, decisions)
    edit = pd.DataFrame(base)[["Код", "Раздел", "Обязательность", "Обнаружен", "Найденные части", "Решение пользователя", "Обоснование", "Примечание"]]
    edited = st.data_editor(
        edit,
        use_container_width=True,
        hide_index=True,
        disabled=["Код", "Раздел", "Обязательность", "Обнаружен", "Найденные части", "Примечание"],
        column_config={
            "Решение пользователя": st.column_config.SelectboxColumn("Решение пользователя", options=USER_DECISIONS, required=True),
            "Обоснование": st.column_config.TextColumn("Обоснование", help="Обязательно для неприменимости или включения в другой раздел"),
        },
        key=f"completeness_editor_{profile}",
    )
    new_decisions = {}
    for row in edited.to_dict("records"):
        new_decisions[row["Код"]] = {"status": row["Решение пользователя"], "justification": row.get("Обоснование", "")}
    st.session_state.completeness_decisions = new_decisions

    matrix = build_matrix(_document_types(docs), profile, new_decisions)
    confirmed = st.session_state.get("completeness_user_confirmed", False)
    summary = summarize(matrix, confirmed, forming)
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Загружено", summary["present"], f"из {summary['total']} позиций матрицы")
    with c2: card("Разрешено", summary["resolved"], "загружено или обосновано", "ok" if not summary["missing"] else "warn")
    with c3: card("Не загружено", summary["missing"], "базово обязательные разделы", "bad" if summary["missing"] and not forming else "warn")
    with c4: card("Статус", summary["status"], f"покрытие {summary['coverage']}%")

    with st.container(border=True):
        st.markdown("#### Подтверждение состава проекта")
        st.caption("Подтверждение пользователя фиксирует состояние комплекта, но не скрывает автоматические предупреждения.")
        a = st.checkbox("Все доступные разделы текущей редакции загружены", key="confirm_available_sections")
        b = st.checkbox("Отсутствующие разделы отмечены как неприменимые, включенные в другой раздел или будут добавлены позднее", key="confirm_missing_sections")
        c = st.checkbox("Документы относятся к одному проекту и одной редакции", key="confirm_same_revision")
        d = st.checkbox("Выбран правильный профиль объекта", key="confirm_profile")
        confirm_enabled = a and b and c and d
        if st.button("Подтвердить состав проекта", type="primary", disabled=not confirm_enabled, use_container_width=True):
            st.session_state.completeness_user_confirmed = True
            st.session_state.completeness_confirmation = {
                "profile": profile,
                "forming": forming,
                "decisions": new_decisions,
            }
            st.success("Состав проекта подтвержден пользователем.")

    if st.session_state.get("completeness_user_confirmed"):
        st.success("Пользовательское подтверждение сохранено для текущей сессии проекта.")
    if summary["missing"] and st.session_state.get("completeness_user_confirmed"):
        st.warning("Комплект подтвержден пользователем, однако система по-прежнему обнаруживает отсутствующие базово обязательные разделы.")

    if st.session_state.expert_mode:
        with st.expander("Матрица итоговых статусов"):
            st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)
