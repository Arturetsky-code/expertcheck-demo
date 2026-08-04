from __future__ import annotations

import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from analyzer import analyze_uploaded
from core.project_upload import (
    DOCUMENT_TYPE_OPTIONS,
    apply_document_type_overrides,
    prepare_uploads,
)

CONFIG_DIR = BASE_DIR / "config" if (BASE_DIR / "config").exists() else BASE_DIR
VERSION = "Studio 1.0 Alpha 1 · Core 3.0 Alpha 4"

st.set_page_config(
    page_title="ExpertCheck Studio",
    page_icon="◩",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
  --bg:#f3f6f8; --surface:#ffffff; --surface-2:#f8fafb;
  --ink:#17212b; --muted:#687683; --line:#dfe6eb;
  --brand:#173f55; --brand-2:#0f7180; --soft:#eaf2f5;
  --ok:#257653; --warn:#a76510; --bad:#b23a31; --info:#386b8c;
}
html, body, [class*="css"] { font-family: Inter, "Segoe UI", Arial, sans-serif; }
.stApp { background:var(--bg); color:var(--ink); }
.block-container { max-width:1500px; padding-top:1.35rem; padding-bottom:2.5rem; }
[data-testid="stSidebar"] { background:#102f40; border-right:0; }
[data-testid="stSidebar"] > div { padding-top:1rem; }
[data-testid="stSidebar"] * { color:#edf5f7; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.30rem .2rem; }
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * { color:var(--ink); }
[data-testid="stSidebar"] .stToggle label span { color:#edf5f7 !important; }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent; }

.ec-topbar { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:1.15rem; }
.ec-brand { display:flex; gap:.8rem; align-items:center; }
.ec-mark { width:42px; height:42px; border-radius:11px; background:linear-gradient(145deg,var(--brand),var(--brand-2)); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800; letter-spacing:-.08em; box-shadow:0 6px 18px rgba(23,63,85,.18); }
.ec-title { font-size:1.65rem; line-height:1.1; font-weight:760; color:var(--ink); }
.ec-sub { color:var(--muted); font-size:.90rem; margin-top:.22rem; }
.ec-version { color:var(--brand); background:var(--soft); border:1px solid #d5e5eb; border-radius:999px; padding:.35rem .72rem; font-size:.78rem; font-weight:650; }

.ec-hero { background:linear-gradient(130deg,#11384e 0%,#195f70 100%); border-radius:20px; padding:1.5rem 1.65rem; color:#fff; box-shadow:0 10px 30px rgba(20,55,73,.16); margin-bottom:1rem; }
.ec-hero h2 { margin:0; color:#fff; font-size:1.45rem; }
.ec-hero p { margin:.45rem 0 0; color:#d8e8ed; }
.ec-status-pill { display:inline-flex; align-items:center; gap:.42rem; background:rgba(255,255,255,.13); border:1px solid rgba(255,255,255,.22); border-radius:999px; padding:.34rem .68rem; font-size:.80rem; margin-top:.9rem; }

.ec-card { background:var(--surface); border:1px solid var(--line); border-radius:15px; padding:1.05rem 1.12rem; box-shadow:0 2px 10px rgba(20,42,56,.045); height:100%; }
.ec-card-label { color:var(--muted); font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.035em; }
.ec-card-value { color:var(--ink); font-size:1.75rem; line-height:1.12; font-weight:760; margin-top:.26rem; }
.ec-card-note { color:var(--muted); font-size:.82rem; margin-top:.38rem; }
.ec-card-ok { border-top:3px solid var(--ok); }
.ec-card-warn { border-top:3px solid var(--warn); }
.ec-card-bad { border-top:3px solid var(--bad); }
.ec-card-info { border-top:3px solid var(--info); }

.ec-section { margin:1.25rem 0 .65rem; }
.ec-section h3 { margin:0; font-size:1.14rem; color:var(--ink); }
.ec-section p { margin:.22rem 0 0; color:var(--muted); font-size:.86rem; }
.ec-empty { background:var(--surface); border:1px dashed #b8c5cd; border-radius:16px; padding:2rem; text-align:center; color:var(--muted); }
.ec-row { display:flex; justify-content:space-between; gap:1rem; align-items:center; border-bottom:1px solid var(--line); padding:.72rem 0; }
.ec-row:last-child { border-bottom:0; }
.ec-row-title { font-weight:680; color:var(--ink); }
.ec-row-note { color:var(--muted); font-size:.80rem; margin-top:.12rem; }
.ec-tag { display:inline-block; border-radius:999px; padding:.24rem .55rem; font-size:.75rem; font-weight:650; background:#edf2f5; color:#425563; }
.ec-tag.ok { background:#e7f4ed; color:var(--ok); }
.ec-tag.warn { background:#fff1dc; color:var(--warn); }
.ec-tag.bad { background:#fae9e7; color:var(--bad); }

.stButton>button, .stDownloadButton>button { border-radius:10px; min-height:2.65rem; font-weight:650; }
.stButton>button[kind="primary"] { background:var(--brand); border-color:var(--brand); }
div[data-testid="stFileUploader"] { background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:.35rem; }
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
div[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:.9rem 1rem; }
.stTabs [data-baseweb="tab-list"] { gap:.25rem; background:#e9eef1; border-radius:12px; padding:.25rem; }
.stTabs [data-baseweb="tab"] { border-radius:9px; padding:.48rem .85rem; }
.stTabs [aria-selected="true"] { background:#fff; }
</style>
""",
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "project_name": "Новый проект",
        "result": None,
        "analysis_time": None,
        "page": "Обзор",
        "expert_mode": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()


def frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result = st.session_state.get("result")
    if not result:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    docs, findings, comparisons = result
    return pd.DataFrame(docs), pd.DataFrame(findings), pd.DataFrame(comparisons)


def status_group(value: str) -> str:
    text = str(value or "").upper()
    if "РАСХОЖД" in text or "КОНФЛИКТ" in text:
        return "bad"
    if "УТОЧ" in text or "НЕДОСТАТОЧ" in text or "НЕ ПРОВЕРЕНО" in text:
        return "warn"
    if "СОВПАД" in text or "ПОДТВЕРЖ" in text:
        return "ok"
    return "info"


def comparison_metrics(df: pd.DataFrame) -> dict[str, int]:
    if df.empty or "status" not in df.columns:
        return {"total": 0, "ok": 0, "warn": 0, "bad": 0}
    groups = df["status"].map(status_group)
    return {
        "total": len(df),
        "ok": int(groups.eq("ok").sum()),
        "warn": int(groups.eq("warn").sum()),
        "bad": int(groups.eq("bad").sum()),
    }


def engineer_findings(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    excluded = {
        "PROJECT_NAME", "PROJECT_CODE", "PROJECT_YEAR", "ISSUE_AUTHOR",
        "CHIEF_ENGINEER", "SIGNER", "DOCUMENT_CODE", "DOCUMENT_YEAR",
        "XML_SCHEMA", "FILE_NAME", "FILE_CHECKSUM", "OBJECT_ENTRY",
        "OBJECT_CANDIDATE",
    }
    result = df.copy()
    if "parameter_code" in result.columns:
        result = result[~result["parameter_code"].fillna("").astype(str).isin(excluded)]
    return result


def consolidated_registry(docs: pd.DataFrame) -> pd.DataFrame:
    if docs.empty or "consolidated_registry" not in docs.columns:
        return pd.DataFrame()
    value = docs.iloc[0].get("consolidated_registry")
    return pd.DataFrame(value or [])


def object_passports(docs: pd.DataFrame) -> list[dict]:
    if docs.empty or "object_passports" not in docs.columns:
        return []
    return docs.iloc[0].get("object_passports") or []


def display_card(label: str, value: str | int, note: str, kind: str = "info") -> None:
    st.markdown(
        f'<div class="ec-card ec-card-{kind}"><div class="ec-card-label">{label}</div>'
        f'<div class="ec-card-value">{value}</div><div class="ec-card-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def section_title(title: str, note: str = "") -> None:
    st.markdown(
        f'<div class="ec-section"><h3>{title}</h3><p>{note}</p></div>',
        unsafe_allow_html=True,
    )


def excel_report(project: str, docs: pd.DataFrame, findings: pd.DataFrame, comparisons: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([
            ["Проект", project],
            ["Версия", VERSION],
            ["Дата проверки", datetime.now().strftime("%d.%m.%Y %H:%M")],
            ["Документов", len(docs)],
            ["Инженерных характеристик", len(engineer_findings(findings))],
            ["Проверок", len(comparisons)],
        ], columns=["Показатель", "Значение"]).to_excel(writer, sheet_name="Сводка", index=False)
        docs.to_excel(writer, sheet_name="Документы", index=False)
        consolidated_registry(docs).to_excel(writer, sheet_name="Реестр объектов", index=False)
        engineer_findings(findings).to_excel(writer, sheet_name="Характеристики", index=False)
        comparisons.to_excel(writer, sheet_name="Сверки", index=False)
        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cells in ws.columns:
                width = min(max(len(str(c.value or "")) for c in cells) + 2, 62)
                ws.column_dimensions[cells[0].column_letter].width = max(12, width)
    return output.getvalue()


# Sidebar
with st.sidebar:
    st.markdown("### ◩ ExpertCheck")
    st.caption("Инженерная проверка проекта")
    st.divider()
    pages = ["Обзор", "Документы", "Объекты", "Сверки", "Замечания"]
    page = st.radio("Раздел", pages, label_visibility="collapsed", key="page")
    st.divider()
    st.session_state["expert_mode"] = st.toggle(
        "Аналитический режим",
        value=st.session_state.get("expert_mode", False),
        help="Показывает диагностические поля, уверенность и служебные данные Core.",
    )
    st.markdown("**Текущий проект**")
    st.caption(st.session_state.get("project_name", "Новый проект"))
    if st.session_state.get("result"):
        st.success("Проверка выполнена")
    else:
        st.info("Комплект не загружен")
    st.caption(VERSION)

# Header
st.markdown(
    f"""
<div class="ec-topbar">
  <div class="ec-brand">
    <div class="ec-mark">EC</div>
    <div><div class="ec-title">ExpertCheck Studio</div><div class="ec-sub">Цифровая проверка проектной документации перед экспертизой</div></div>
  </div>
  <div class="ec-version">{VERSION}</div>
</div>
""",
    unsafe_allow_html=True,
)

docs_df, findings_df, comparisons_df = frames()
registry_df = consolidated_registry(docs_df)
passport_list = object_passports(docs_df)
metrics = comparison_metrics(comparisons_df)
eng_findings = engineer_findings(findings_df)

if page == "Обзор":
    project = st.session_state.get("project_name", "Новый проект")
    if docs_df.empty:
        st.markdown(
            """
<div class="ec-hero">
  <h2>Новая проверка проекта</h2>
  <p>Загрузите PDF, XML или ZIP-комплект. Перед запуском можно проверить состав и исправить типы документов.</p>
  <div class="ec-status-pill">01 · Загрузка &nbsp; → &nbsp; 02 · Проверка состава &nbsp; → &nbsp; 03 · Анализ &nbsp; → &nbsp; 04 · Результат</div>
</div>
""",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            name = st.text_input("Наименование проекта", value=project)
            uploads = st.file_uploader(
                "Комплект проекта",
                type=["pdf", "xml", "zip"],
                accept_multiple_files=True,
                help="Можно загрузить отдельные документы либо ZIP с сохранённой структурой папок.",
            )
            prepared = []
            edited = pd.DataFrame()
            confirmed = False
            errors: list[str] = []
            if uploads:
                package = prepare_uploads(uploads)
                prepared = package.files
                errors = package.errors
                for item in errors:
                    st.error(item)
                for item in package.warnings:
                    st.warning(item)
                if prepared:
                    s = package.package_summary
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Файлов", int(s.get("files", 0)))
                    c2.metric("Общий объём", f"{float(s.get('total_bytes', 0))/1024/1024:.1f} МБ")
                    c3.metric("XML", ", ".join(s.get("identity", {}).get("xml_schemas", [])) or "нет")
                    section_title("Состав комплекта", "Проверьте классификацию документов до запуска анализа.")
                    inventory = pd.DataFrame(package.inventory)
                    edited = st.data_editor(
                        inventory,
                        hide_index=True,
                        use_container_width=True,
                        disabled=["ID", "Файл", "Формат", "Семейство", "Размер, МБ", "Источник", "Статус"],
                        column_config={
                            "Предполагаемый раздел": st.column_config.SelectboxColumn(
                                "Раздел", options=DOCUMENT_TYPE_OPTIONS, required=True
                            ),
                            "Размер, МБ": st.column_config.NumberColumn(format="%.2f"),
                        },
                        key="studio_upload_inventory",
                    )
                    completeness = s.get("completeness", {})
                    available = completeness.get("available_checks", [])
                    limits = completeness.get("limitations", [])
                    if available:
                        st.success("Доступно: " + "; ".join(available))
                    if limits:
                        st.info("Ограничения: " + "; ".join(limits))
                    confirmed = st.checkbox("Состав комплекта проверен", key="studio_package_confirmed")
            run = st.button(
                "Запустить проверку проекта",
                type="primary",
                use_container_width=True,
                disabled=not prepared or bool(errors) or not confirmed,
            )
            if run:
                files = apply_document_type_overrides(prepared, edited.to_dict("records"))
                with st.spinner("Строим цифровой профиль и выполняем межраздельную сверку…"):
                    st.session_state["result"] = analyze_uploaded(files, CONFIG_DIR)
                    st.session_state["project_name"] = name.strip() or "Новый проект"
                    st.session_state["analysis_time"] = datetime.now().isoformat(timespec="minutes")
                st.rerun()
    else:
        model_quality = {}
        xml_summary = {}
        if "dem_model_quality" in docs_df.columns:
            model_quality = docs_df.iloc[0].get("dem_model_quality") or {}
        if "xml_engine_summary" in docs_df.columns:
            xml_summary = docs_df.iloc[0].get("xml_engine_summary") or {}
        quality = int(round(float(model_quality.get("model_quality_index", 0)) * 100)) if model_quality else 0
        st.markdown(
            f"""
<div class="ec-hero">
  <h2>{project}</h2>
  <p>Проверка завершена. Ниже показаны только результаты, влияющие на инженерное решение.</p>
  <div class="ec-status-pill">Индекс цифровой модели: {quality}% · Последняя проверка: {st.session_state.get('analysis_time') or '—'}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        with c1: display_card("Документы", len(docs_df), "PDF и XML в комплекте", "info")
        with c2: display_card("Объекты", len(registry_df), "Позиции консолидированного реестра", "info")
        with c3: display_card("Требуют внимания", metrics["bad"] + metrics["warn"], "Расхождения и неподтверждённые сведения", "bad" if metrics["bad"] else "warn")
        with c4: display_card("Подтверждено", metrics["ok"], "Согласованные межраздельные проверки", "ok")

        section_title("Состояние проекта", "Краткая сводка без технических полей и служебных находок.")
        left, right = st.columns([1.45, 1])
        with left:
            problem_df = comparisons_df.copy()
            if not problem_df.empty and "status" in problem_df.columns:
                problem_df["_group"] = problem_df["status"].map(status_group)
                problem_df = problem_df[problem_df["_group"].isin(["bad", "warn"])]
            if problem_df.empty:
                st.success("Существенные расхождения не выявлены либо пока недостаточно сопоставимых данных.")
            else:
                shown = problem_df.head(8)
                for _, row in shown.iterrows():
                    obj = str(row.get("object") or "Объект не определён")
                    param = str(row.get("parameter_name") or row.get("rule_name") or "Проверка")
                    status = str(row.get("status") or "Требует проверки")
                    vals = str(row.get("document_values") or row.get("documents") or "")
                    kind = status_group(status)
                    st.markdown(
                        f'<div class="ec-card" style="margin-bottom:.55rem"><div class="ec-row-title">{obj} · {param}</div>'
                        f'<div class="ec-row-note">{vals}</div><div style="margin-top:.45rem"><span class="ec-tag {kind}">{status}</span></div></div>',
                        unsafe_allow_html=True,
                    )
                if len(problem_df) > len(shown):
                    st.caption(f"Ещё результатов: {len(problem_df)-len(shown)}. Полный перечень находится в разделах «Сверки» и «Замечания».")
        with right:
            with st.container(border=True):
                st.markdown("**Покрытие проверки**")
                st.write(f"Инженерных характеристик: **{len(eng_findings)}**")
                st.write(f"Межраздельных проверок: **{metrics['total']}**")
                st.write(f"XML-файлов: **{int(xml_summary.get('files', 0) or 0)}**")
                st.write(f"PDF ↔ XML проверок: **{int(xml_summary.get('pdf_xml_checks', 0) or 0)}**")
                st.write(f"Реестровых позиций: **{len(registry_df)}**")
            if st.button("Новая проверка", use_container_width=True):
                st.session_state["result"] = None
                st.session_state["analysis_time"] = None
                st.rerun()
            st.download_button(
                "Скачать отчёт Excel",
                data=excel_report(project, docs_df, findings_df, comparisons_df),
                file_name="ExpertCheck_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

elif page == "Документы":
    section_title("Документы проекта", "Состав комплекта, типы разделов и результаты обработки.")
    if docs_df.empty:
        st.markdown('<div class="ec-empty">Сначала загрузите комплект на странице «Обзор».</div>', unsafe_allow_html=True)
    else:
        preferred = ["Файл", "Раздел", "Страниц", "Размер", "XML-схема", "Распознано страниц с таблицами"]
        view = docs_df[[c for c in preferred if c in docs_df.columns]].copy()
        if view.empty:
            view = docs_df[[c for c in docs_df.columns if not c.endswith("summary") and not c.startswith("dem_")]].copy()
        st.dataframe(view, use_container_width=True, hide_index=True)
        if st.session_state["expert_mode"]:
            with st.expander("Диагностика документов", expanded=False):
                st.dataframe(docs_df, use_container_width=True, hide_index=True)

elif page == "Объекты":
    section_title("Реестр объектов", "Консолидированный перечень по ПЗ, генплану, XML и профильным разделам.")
    if registry_df.empty:
        st.markdown('<div class="ec-empty">Реестр объектов ещё не сформирован.</div>', unsafe_allow_html=True)
    else:
        search = st.text_input("Поиск по позиции или наименованию", placeholder="Например: 4.18 или насосная")
        view = registry_df.copy()
        if search:
            mask = view.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            view = view[mask]
        main_cols = [
            "Позиция по ГП", "Наименование объекта", "Количество", "Количество источников",
            "Статус консолидации", "Конфликты"
        ]
        st.dataframe(view[[c for c in main_cols if c in view.columns]], use_container_width=True, hide_index=True)
        if passport_list:
            section_title("Цифровой паспорт объекта", "Выберите объект для просмотра характеристик и подтверждающих разделов.")
            labels = [f"{p.get('position','')} · {p.get('name','')}" for p in passport_list]
            selected_label = st.selectbox("Объект", labels)
            passport = passport_list[labels.index(selected_label)]
            c1, c2, c3, c4 = st.columns(4)
            with c1: display_card("Позиция", passport.get("position") or "—", "Позиция по генеральному плану", "info")
            with c2: display_card("Количество", passport.get("quantity", 1), "Физических экземпляров", "info")
            with c3: display_card("Характеристики", len(passport.get("characteristics", [])), "Связанные параметры", "ok")
            with c4: display_card("Полнота", f"{float(passport.get('passport_completeness',0)):.0f}%", "Наполнение цифрового паспорта", "warn")
            chars = pd.DataFrame(passport.get("characteristics", []))
            if not chars.empty:
                rename = {
                    "parameter_name": "Характеристика", "unit": "Ед. изм.",
                    "values_by_section": "Значения по разделам", "status": "Статус",
                    "source_count": "Источников", "confidence": "Уверенность",
                }
                chars = chars.rename(columns=rename)
                visible = ["Характеристика", "Ед. изм.", "Значения по разделам", "Статус", "Источников"]
                if st.session_state["expert_mode"]:
                    visible += ["Уверенность", "pages_by_section", "evidence_count"]
                st.dataframe(chars[[c for c in visible if c in chars.columns]], use_container_width=True, hide_index=True)

elif page == "Сверки":
    section_title("Межраздельные сверки", "Сопоставление только инженерных характеристик; метаданные проекта вынесены из рабочего представления.")
    if comparisons_df.empty:
        st.markdown('<div class="ec-empty">Сопоставимые сведения не найдены.</div>', unsafe_allow_html=True)
    else:
        statuses = sorted(comparisons_df.get("status", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
        c1, c2 = st.columns([1, 2])
        selected_status = c1.multiselect("Статус", statuses, default=statuses)
        query = c2.text_input("Поиск", placeholder="Объект, характеристика или раздел")
        view = comparisons_df.copy()
        if selected_status and "status" in view.columns:
            view = view[view["status"].isin(selected_status)]
        if query:
            mask = view.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
            view = view[mask]
        cols = ["object", "parameter_name", "status", "documents", "document_values", "explanation"]
        if st.session_state["expert_mode"]:
            cols += ["check_code", "priority", "evidence_count", "sources", "engineering_risk_level"]
        labels = {
            "object":"Объект", "parameter_name":"Характеристика", "status":"Результат",
            "documents":"Разделы", "document_values":"Значения", "explanation":"Объяснение",
            "check_code":"Код", "priority":"Приоритет", "evidence_count":"Подтверждений",
            "sources":"Источники", "engineering_risk_level":"Риск",
        }
        st.dataframe(view[[c for c in cols if c in view.columns]].rename(columns=labels), use_container_width=True, hide_index=True)

elif page == "Замечания":
    section_title("Результаты, требующие решения", "Отфильтрованные расхождения и неподтверждённые сведения — без совпадений и технических находок.")
    if comparisons_df.empty or "status" not in comparisons_df.columns:
        st.markdown('<div class="ec-empty">Замечания пока не сформированы.</div>', unsafe_allow_html=True)
    else:
        view = comparisons_df.copy()
        view["_group"] = view["status"].map(status_group)
        view = view[view["_group"].isin(["bad", "warn"])]
        if view.empty:
            st.success("Результаты, требующие решения, не выявлены.")
        else:
            priority_options = sorted(view.get("priority", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
            selected_priority = st.multiselect("Приоритет", priority_options, default=priority_options)
            if selected_priority and "priority" in view.columns:
                view = view[view["priority"].isin(selected_priority)]
            cols = ["object", "parameter_name", "status", "priority", "document_values", "explanation", "sources"]
            labels = {
                "object":"Объект", "parameter_name":"Характеристика", "status":"Статус",
                "priority":"Приоритет", "document_values":"Значения по разделам",
                "explanation":"Почему требуется проверка", "sources":"Источники",
            }
            st.dataframe(view[[c for c in cols if c in view.columns]].rename(columns=labels), use_container_width=True, hide_index=True)
            st.download_button(
                "Скачать перечень замечаний",
                data=view.drop(columns=["_group"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                file_name="ExpertCheck_remarks.csv",
                mime="text/csv",
            )
