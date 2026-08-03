from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from analyzer import analyze_uploaded

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"

st.set_page_config(
    page_title="ExpertCheck Demo",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("ExpertCheck Demo")
st.caption("Предварительная облачная версия сервиса предэкспертной проверки проектной документации")

with st.sidebar:
    st.header("Параметры проекта")
    project_name = st.text_input("Наименование проекта", "Тестовый проект")
    st.markdown("**Версия:** Cloud Demo v0.1")
    st.info(
        "Файлы обрабатываются только в текущем сеансе. Внешние ИИ-API и постоянная база данных не используются."
    )

st.markdown(
    "Загрузите PDF-разделы проектной документации. Для демонстрации рекомендуется ПЗ, ПЗУ1, АР1 и ТХ1."
)

uploaded_files = st.file_uploader(
    "PDF-документы",
    type=["pdf"],
    accept_multiple_files=True,
    help="Для первой демонстрации используйте PDF с текстовым слоем. Максимальный практический комплект — 4–8 файлов.",
)

col_a, col_b = st.columns([1, 3])
with col_a:
    run = st.button("Начать проверку", type="primary", disabled=not uploaded_files, use_container_width=True)
with col_b:
    if uploaded_files:
        st.caption(f"Выбрано файлов: {len(uploaded_files)}")

if run:
    try:
        with st.spinner("Чтение документов, поиск параметров и межраздельная сверка…"):
            documents, findings, comparisons = analyze_uploaded(uploaded_files, CONFIG_DIR)
            st.session_state["result"] = (documents, findings, comparisons)
            st.session_state["project_name"] = project_name
        st.success("Проверка завершена")
    except Exception as exc:
        st.exception(exc)

if "result" in st.session_state:
    documents, findings, comparisons = st.session_state["result"]
    project_name = st.session_state.get("project_name", project_name)
    docs_df = pd.DataFrame(documents)
    findings_df = pd.DataFrame(findings)
    comparisons_df = pd.DataFrame(comparisons)

    mismatch_count = 0
    matched_count = 0
    if not comparisons_df.empty and "status" in comparisons_df.columns:
        mismatch_count = int((comparisons_df["status"] == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ").sum())
        matched_count = int((comparisons_df["status"] == "СОВПАДАЕТ").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Документов", len(docs_df))
    k2.metric("Найдено упоминаний", len(findings_df))
    k3.metric("Потенциальных расхождений", mismatch_count)
    k4.metric("Совпадений", matched_count)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Документы", "Найденные параметры", "Межраздельная сверка", "О версии"]
    )

    with tab1:
        st.dataframe(docs_df, use_container_width=True, hide_index=True)

    with tab2:
        if findings_df.empty:
            st.warning("Параметры не найдены. Возможно, в PDF отсутствует текстовый слой.")
        else:
            display_cols = [
                "document_type", "page", "object_hint", "parameter_name",
                "value_text", "unit", "confidence", "context",
            ]
            available = [c for c in display_cols if c in findings_df.columns]
            st.dataframe(findings_df[available], use_container_width=True, hide_index=True)

    with tab3:
        if comparisons_df.empty:
            st.info("Не найдено показателей, которые удалось сопоставить минимум в двух разделах.")
        else:
            st.dataframe(comparisons_df, use_container_width=True, hide_index=True)
            st.warning(
                "Это предварительный автоматический анализ. Каждое расхождение необходимо подтвердить специалисту."
            )

    with tab4:
        st.markdown(
            """
            **ExpertCheck Demo v0.1** показывает базовый сценарий будущего продукта:

            `PDF → извлечение текста → поиск показателя → привязка к объекту → сравнение разделов → отчёт`.

            Текущие ограничения:
            - анализируется текстовый слой PDF;
            - сканы без текста могут не читаться;
            - объект определяется по словарю и ближайшему контексту;
            - разные виды одноимённых показателей могут быть ошибочно сопоставлены;
            - графические решения, расчёты и нормативное соответствие не оцениваются;
            - сервис не заменяет нормоконтроль и экспертную оценку.
            """
        )

    def make_excel() -> bytes:
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            summary = pd.DataFrame(
                [
                    ["Проект", project_name],
                    ["Дата проверки", datetime.now().strftime("%d.%m.%Y %H:%M")],
                    ["Документов", len(docs_df)],
                    ["Найдено упоминаний", len(findings_df)],
                    ["Потенциальных расхождений", mismatch_count],
                    ["Совпадений", matched_count],
                ],
                columns=["Показатель", "Значение"],
            )
            summary.to_excel(writer, sheet_name="Сводка", index=False)
            docs_df.to_excel(writer, sheet_name="Документы", index=False)
            findings_df.to_excel(writer, sheet_name="Найденные параметры", index=False)
            comparisons_df.to_excel(writer, sheet_name="Сверка", index=False)

            for sheet in writer.book.worksheets:
                sheet.freeze_panes = "A2"
                sheet.auto_filter.ref = sheet.dimensions
                for column_cells in sheet.columns:
                    length = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 65)
                    sheet.column_dimensions[column_cells[0].column_letter].width = max(length, 12)
        return out.getvalue()

    safe_project = "".join(ch if ch.isalnum() or ch in " _-" else "_" for ch in project_name).strip() or "Проект"
    st.download_button(
        "Скачать Excel-отчёт",
        data=make_excel(),
        file_name=f"ExpertCheck_{safe_project}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

st.divider()
st.caption("ExpertCheck Demo — экспериментальный инструмент. Результаты требуют профессиональной проверки.")
