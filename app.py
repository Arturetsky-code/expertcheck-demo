from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Поддержка обеих структур репозитория:
# 1) analyzer.py и JSON в корне;
# 2) modules/analyzer.py и config/*.json.
try:
    from analyzer import analyze_uploaded
except ModuleNotFoundError:
    from modules.analyzer import analyze_uploaded

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config" if (BASE_DIR / "config").exists() else BASE_DIR

st.set_page_config(
    page_title="ExpertCheck",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Стили ----------
st.markdown(
    """
    <style>
    :root {
        --ec-bg: #f5f7fb;
        --ec-card: #ffffff;
        --ec-text: #172033;
        --ec-muted: #6b7280;
        --ec-primary: #214761;
        --ec-accent: #0f8b8d;
        --ec-border: #e5e9f0;
        --ec-warn: #b7791f;
        --ec-danger: #b42318;
        --ec-success: #19734b;
    }

    .stApp { background: var(--ec-bg); }
    [data-testid="stSidebar"] { background: #152d3d; }
    [data-testid="stSidebar"] * { color: #f8fafc; }
    [data-testid="stSidebar"] .stRadio label { padding: .25rem 0; }
    [data-testid="stSidebar"] input { color: #172033 !important; }

    .block-container {
        max-width: 1480px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .ec-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .ec-brand { font-size: 1.75rem; font-weight: 750; color: var(--ec-text); }
    .ec-brand span { color: var(--ec-accent); }
    .ec-subtitle { color: var(--ec-muted); margin-top: .15rem; }
    .ec-badge {
        display: inline-block;
        background: #e8f4f4;
        color: #0b6b6d;
        border: 1px solid #c9e6e6;
        border-radius: 999px;
        padding: .35rem .7rem;
        font-size: .82rem;
        font-weight: 650;
    }

    .ec-card {
        background: var(--ec-card);
        border: 1px solid var(--ec-border);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(17, 32, 51, .04);
        height: 100%;
    }
    .ec-card-title { color: var(--ec-muted); font-size: .82rem; margin-bottom: .3rem; }
    .ec-card-value { color: var(--ec-text); font-size: 1.75rem; font-weight: 750; line-height: 1.15; }
    .ec-card-note { color: var(--ec-muted); font-size: .82rem; margin-top: .4rem; }

    .ec-section-title { color: var(--ec-text); font-size: 1.25rem; font-weight: 700; margin: .5rem 0 .85rem; }
    .ec-empty {
        background: var(--ec-card);
        border: 1px dashed #bdc6d2;
        border-radius: 14px;
        padding: 2rem;
        text-align: center;
        color: var(--ec-muted);
    }
    .ec-status-ok { color: var(--ec-success); font-weight: 700; }
    .ec-status-warn { color: var(--ec-warn); font-weight: 700; }
    .ec-status-danger { color: var(--ec-danger); font-weight: 700; }

    div[data-testid="stMetric"] {
        background: var(--ec-card);
        border: 1px solid var(--ec-border);
        padding: 1rem 1.05rem;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(17, 32, 51, .04);
    }
    div[data-testid="stMetricLabel"] { color: var(--ec-muted); }
    div[data-testid="stMetricValue"] { color: var(--ec-text); }

    .stButton > button, .stDownloadButton > button {
        border-radius: 9px;
        min-height: 2.7rem;
        font-weight: 650;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: var(--ec-primary);
        border-color: var(--ec-primary);
    }
    div[data-testid="stFileUploader"] {
        background: var(--ec-card);
        border: 1px solid var(--ec-border);
        border-radius: 14px;
        padding: .45rem;
    }
    .ec-steps { display:grid; grid-template-columns:repeat(4,1fr); gap:.65rem; margin:.3rem 0 1.2rem; }
    .ec-step { background:#fff; border:1px solid var(--ec-border); border-radius:12px; padding:.7rem .85rem; color:var(--ec-muted); font-size:.84rem; }
    .ec-step strong { display:block; color:var(--ec-text); margin-top:.15rem; }
    .ec-step.done { border-color:#a9d8cc; background:#f2fbf8; }
    .ec-step.active { border-color:#73a8bd; background:#f2f8fb; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Состояние ----------
def init_state() -> None:
    defaults = {
        "project_name": "Новый проект",
        "project_stage": "Проектная документация",
        "result": None,
        "analysis_time": None,
        "active_page": "Главная",
        "object_registry": None,
        "object_registry_confirmed": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def result_frames():
    if not st.session_state.get("result"):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    documents, findings, comparisons = st.session_state["result"]
    return pd.DataFrame(documents), pd.DataFrame(findings), pd.DataFrame(comparisons)


DISPLAY_FINDING_COLUMNS = {
    "document": "Файл",
    "document_type": "Раздел",
    "page": "Страница",
    "object_hint": "Объект",
    "genplan_position": "Позиция по генплану",
    "parameter_code": "Код характеристики",
    "parameter_name": "Характеристика",
    "value": "Числовое значение",
    "value_text": "Найденное значение",
    "unit": "Ед. изм.",
    "confidence": "Уверенность",
    "context": "Фрагмент документа",
    "match_method": "Способ извлечения",
    "structural_zone": "Структурный блок",
    "extraction_profile": "Профиль анализа",
    "review_note": "Примечание",
}

DISPLAY_COMPARISON_COLUMNS = {
    "check_code": "Код проверки",
    "object": "Объект",
    "parameter_code": "Код характеристики",
    "parameter_name": "Характеристика",
    "unit": "Ед. изм.",
    "priority": "Приоритет",
    "status": "Результат проверки",
    "evidence_level": "Надёжность доказательств",
    "evidence_count": "Подтверждающих разделов",
    "rejected_count": "Отброшено слабых находок",
    "min_value": "Минимальное значение",
    "max_value": "Максимальное значение",
    "difference": "Разница",
    "documents": "Разделы",
    "document_values": "Значения по разделам",
    "sources": "Источники",
    "comment": "Комментарий",
}

UNIT_LABELS = {
    "m2": "м²", "м2": "м²", "м²": "м²", "кв.м": "м²", "квм": "м²",
    "m3": "м³", "м3": "м³", "м³": "м³", "куб.м": "м³", "кубм": "м³",
    "kva": "кВА", "ква": "кВА", "kw": "кВт", "квт": "кВт",
    "mw": "МВт", "мвт": "МВт", "чел": "чел.", "чел.": "чел.",
    "эт": "эт.", "эт.": "эт.", "м": "м", "т/ч": "т/ч",
    "т/сут": "т/сут", "т/год": "т/год", "м3/ч": "м³/ч", "м³/ч": "м³/ч",
}

def humanize_units(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if "unit" in result.columns:
        result["unit"] = result["unit"].fillna("").astype(str).map(
            lambda x: UNIT_LABELS.get(x.strip().lower(), x)
        )
    return result

def findings_for_user(df: pd.DataFrame) -> pd.DataFrame:
    result = humanize_units(df)
    if "confidence" in result.columns:
        result["confidence"] = result["confidence"].apply(
            lambda value: f"{float(value):.0%}" if pd.notna(value) else "—"
        )
    return result.rename(columns=DISPLAY_FINDING_COLUMNS)

def comparisons_for_user(df: pd.DataFrame) -> pd.DataFrame:
    return humanize_units(df).rename(columns=DISPLAY_COMPARISON_COLUMNS)

def comparison_counts(comparisons_df: pd.DataFrame) -> tuple[int, int]:
    if comparisons_df.empty or "status" not in comparisons_df.columns:
        return 0, 0
    mismatches = int((comparisons_df["status"] == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ").sum())
    matches = int((comparisons_df["status"] == "СОВПАДАЕТ").sum())
    return mismatches, matches


def clarification_count(comparisons_df: pd.DataFrame) -> int:
    if comparisons_df.empty or "status" not in comparisons_df.columns:
        return 0
    return int((comparisons_df["status"] == "ТРЕБУЕТ УТОЧНЕНИЯ").sum())


def valid_object_findings(findings_df: pd.DataFrame) -> pd.DataFrame:
    if findings_df.empty or "object_hint" not in findings_df.columns:
        return pd.DataFrame()
    result = findings_df.copy()
    result["object_hint"] = result["object_hint"].fillna("Не определён").astype(str)
    return result[result["object_hint"].str.strip().ne("Не определён")]


def build_object_summary(findings_df: pd.DataFrame, comparisons_df: pd.DataFrame) -> pd.DataFrame:
    valid = valid_object_findings(findings_df)
    if valid.empty:
        return pd.DataFrame(columns=["Объект", "Характеристик", "Разделов", "Источников", "Статус"])
    comparison_status = {}
    if not comparisons_df.empty and {"object", "status"}.issubset(comparisons_df.columns):
        for object_name, group in comparisons_df.groupby("object"):
            has_mismatch = bool((group["status"] == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ").any())
            comparison_status[str(object_name)] = "Требует внимания" if has_mismatch else "Согласовано"
    rows = []
    for object_name, group in valid.groupby("object_hint"):
        characteristic_group = group
        if "parameter_code" in group.columns:
            characteristic_group = group[group["parameter_code"] != "OBJECT_ENTRY"]
        characteristics = characteristic_group["parameter_name"].dropna().astype(str).nunique() if "parameter_name" in characteristic_group else 0
        sections = group["document_type"].dropna().astype(str).nunique() if "document_type" in group else 0
        rows.append({
            "Объект": object_name,
            "Характеристик": characteristics,
            "Разделов": sections,
            "Источников": len(group),
            "Статус": comparison_status.get(str(object_name), "Недостаточно данных для сверки"),
        })
    return pd.DataFrame(rows).sort_values(["Статус", "Объект"], kind="stable").reset_index(drop=True)


def object_profile_for_user(findings_df: pd.DataFrame, object_name: str) -> pd.DataFrame:
    view = findings_df[findings_df["object_hint"] == object_name].copy()
    if "parameter_code" in view.columns:
        view = view[view["parameter_code"] != "OBJECT_ENTRY"]
    columns = ["genplan_position", "parameter_name", "value_text", "unit", "document_type", "page", "confidence", "context"]
    available = [column for column in columns if column in view.columns]
    result = findings_for_user(view[available])
    preferred = ["Позиция по генплану", "Характеристика", "Найденное значение", "Ед. изм.", "Раздел", "Страница", "Уверенность", "Фрагмент документа"]
    return result[[column for column in preferred if column in result.columns]]



def characteristic_findings(findings_df: pd.DataFrame) -> pd.DataFrame:
    if findings_df.empty or "parameter_code" not in findings_df.columns:
        return findings_df.copy()
    return findings_df[~findings_df["parameter_code"].isin(["OBJECT_ENTRY", "OBJECT_CANDIDATE"])].copy()


def _norm_object_key(value: str) -> str:
    import re
    value = str(value or "").lower().replace("ё", "е")
    return re.sub(r"[^а-яa-z0-9]+", "", value)


def build_candidate_registry(findings_df: pd.DataFrame) -> pd.DataFrame:
    columns = ["Включить", "Позиция по ГП", "Наименование объекта", "Количество", "Источники", "Подтверждений", "Статус", "Уверенность", "Страницы", "Исходные наименования"]
    if findings_df.empty or "parameter_code" not in findings_df.columns:
        return pd.DataFrame(columns=columns)
    candidates = findings_df[findings_df["parameter_code"].isin(["OBJECT_ENTRY", "OBJECT_CANDIDATE"])].copy()
    if candidates.empty:
        return pd.DataFrame(columns=columns)
    for col in ["genplan_position", "object_hint", "value_text", "document_type", "document", "page", "confidence", "value"]:
        if col not in candidates.columns:
            candidates[col] = ""
    candidates["genplan_position"] = candidates["genplan_position"].fillna("").astype(str).str.strip()
    candidates["object_hint"] = candidates["object_hint"].fillna("").astype(str).str.strip()
    candidates["value_text"] = candidates["value_text"].fillna("").astype(str).str.strip()
    candidates["group_key"] = candidates.apply(
        lambda row: f"GP:{row['genplan_position']}" if row["genplan_position"] else f"NM:{_norm_object_key(row['object_hint'] or row['value_text'])}", axis=1
    )
    rows = []
    for _, group in candidates.groupby("group_key", sort=False):
        position = next((x for x in group["genplan_position"].tolist() if x), "")
        ranked = group.assign(
            pz_rank=(group["parameter_code"] == "OBJECT_ENTRY").astype(int),
            name_len=group["value_text"].str.len(),
        ).sort_values(["pz_rank", "confidence", "name_len"], ascending=False)
        best = ranked.iloc[0]
        name = str(best["value_text"] or best["object_hint"]).strip()
        names = sorted({str(x).strip() for x in group["value_text"].tolist() if str(x).strip()})
        sections = sorted({str(x).strip() for x in group["document_type"].tolist() if str(x).strip()})
        pages = sorted({f"{r.document_type}: {int(r.page)}" for r in group.itertuples() if pd.notna(r.page)})
        quantities = [int(float(x)) for x in group["value"].tolist() if pd.notna(x) and str(x) != ""]
        quantity = max(quantities) if quantities else 1
        has_pz = bool((group["parameter_code"] == "OBJECT_ENTRY").any())
        if has_pz and len(sections) >= 2:
            status = "Подтверждено"
        elif len(sections) >= 2:
            status = "Подтверждено несколькими разделами"
        elif has_pz:
            status = "Извлечено из ПЗ"
        else:
            status = "Требует подтверждения"
        normalized_names = {_norm_object_key(x) for x in names if x}
        if position and len(normalized_names) >= 3:
            status = "Требует уточнения наименования"
        rows.append({
            "Включить": True,
            "Позиция по ГП": position,
            "Наименование объекта": name,
            "Количество": quantity,
            "Источники": ", ".join(sections),
            "Подтверждений": len(sections),
            "Статус": status,
            "Уверенность": f"{float(group['confidence'].max()):.0%}",
            "Страницы": "; ".join(pages),
            "Исходные наименования": " | ".join(names),
        })
    result = pd.DataFrame(rows, columns=columns)
    if not result.empty:
        result = result.sort_values(["Позиция по ГП", "Наименование объекта"], kind="stable").reset_index(drop=True)
    return result


def registry_for_export(findings_df: pd.DataFrame) -> pd.DataFrame:
    stored = st.session_state.get("object_registry")
    if stored:
        return pd.DataFrame(stored)
    return build_candidate_registry(findings_df)

def make_excel(project_name: str, docs_df: pd.DataFrame, findings_df: pd.DataFrame, comparisons_df: pd.DataFrame) -> bytes:
    mismatch_count, matched_count = comparison_counts(comparisons_df)
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        summary = pd.DataFrame(
            [
                ["Проект", project_name],
                ["Версия ExpertCheck", "Demo Cloud v0.7.0"],
                ["Дата проверки", datetime.now().strftime("%d.%m.%Y %H:%M")],
                ["Документов", len(docs_df)],
                ["Извлечено характеристик", len(findings_df)],
                ["Потенциальных расхождений", mismatch_count],
                ["Совпадений", matched_count],
                ["Требуют уточнения", clarification_count(comparisons_df)],
            ],
            columns=["Характеристика", "Значение"],
        )
        summary.to_excel(writer, sheet_name="Сводка", index=False)
        docs_df.to_excel(writer, sheet_name="Документы", index=False)
        build_object_summary(findings_df, comparisons_df).to_excel(writer, sheet_name="Перечень объектов", index=False)
        findings_for_user(characteristic_findings(findings_df)).to_excel(writer, sheet_name="Характеристики проекта", index=False)
        comparisons_for_user(comparisons_df).to_excel(writer, sheet_name="Проверки", index=False)

        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column_cells in sheet.columns:
                width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 65)
                sheet.column_dimensions[column_cells[0].column_letter].width = max(width, 12)
    return out.getvalue()


# ---------- Боковая навигация ----------
with st.sidebar:
    st.markdown("## ✓ ExpertCheck")
    st.caption("Предэкспертная проверка документации")
    st.divider()

    pages = [
        "Главная",
        "Проект",
        "Документы",
        "Перечень объектов",
        "Характеристики проекта",
        "Проверки",
        "Несоответствия",
        "Отчёт",
        "О версии",
    ]
    page = st.radio("Навигация", pages, label_visibility="collapsed", key="active_page")

    st.divider()
    st.markdown("**Текущий проект**")
    st.caption(st.session_state.get("project_name", "Новый проект"))
    if st.session_state.get("result"):
        st.success("Анализ завершён")
    else:
        st.info("Документы не проверены")
    st.caption("Demo Cloud v0.7.0")


# ---------- Общая шапка ----------
st.markdown(
    """
    <div class="ec-header">
      <div>
        <div class="ec-brand">Expert<span>Check</span></div>
        <div class="ec-subtitle">Интеллектуальная система предэкспертной проверки проектной документации</div>
      </div>
      <div class="ec-badge">Demo Cloud v0.7.0</div>
    </div>
    """,
    unsafe_allow_html=True,
)


docs_df, findings_df, comparisons_df = result_frames()
mismatch_count, matched_count = comparison_counts(comparisons_df)
registry_df = registry_for_export(findings_df) if not findings_df.empty else pd.DataFrame()
registry_confirmed = bool(st.session_state.get("object_registry_confirmed"))

st.markdown(
    f"""<div class="ec-steps">
      <div class="ec-step {'done' if not docs_df.empty else 'active'}">01<strong>Документы</strong></div>
      <div class="ec-step {'done' if registry_confirmed else ('active' if not docs_df.empty else '')}">02<strong>Перечень объектов</strong></div>
      <div class="ec-step {'done' if registry_confirmed and not characteristic_findings(findings_df).empty else ''}">03<strong>Характеристики</strong></div>
      <div class="ec-step {'done' if not comparisons_df.empty else ''}">04<strong>Проверки</strong></div>
    </div>""", unsafe_allow_html=True
)

# ---------- Главная ----------
if page == "Главная":
    st.markdown('<div class="ec-section-title">Рабочая панель</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Документов", len(docs_df), help="Количество документов в последнем анализе")
    c2.metric("Извлечено характеристик", len(characteristic_findings(findings_df)), help="Количество найденных упоминаний характеристик")
    c3.metric("Расхождений", mismatch_count, help="Потенциальные межраздельные расхождения")
    c4.metric("Совпадений", matched_count, help="Сопоставленные одинаковые значения")

    left, right = st.columns([1.55, 1])
    with left:
        st.markdown('<div class="ec-section-title">Новый анализ</div>', unsafe_allow_html=True)
        with st.container(border=True):
            project_name = st.text_input(
                "Наименование проекта",
                value=st.session_state.get("project_name", "Новый проект"),
            )
            project_stage = st.selectbox(
                "Комплект документации",
                ["Проектная документация", "Рабочая документация", "Инженерные изыскания"],
                index=0,
            )
            uploaded_files = st.file_uploader(
                "Загрузите PDF-документы",
                type=["pdf"],
                accept_multiple_files=True,
                help="Для демонстрации рекомендуется загрузить ПЗ, ПЗУ1, АР1 и ТХ1 с текстовым слоем.",
            )
            run = st.button(
                "Построить цифровой профиль проекта",
                type="primary",
                disabled=not uploaded_files,
                use_container_width=True,
            )

            if run:
                try:
                    with st.spinner("Анализируем документы и сопоставляем параметры…"):
                        result = analyze_uploaded(uploaded_files, CONFIG_DIR)
                        st.session_state["result"] = result
                        st.session_state["project_name"] = project_name.strip() or "Новый проект"
                        st.session_state["project_stage"] = project_stage
                        st.session_state["analysis_time"] = datetime.now()
                        st.session_state["object_registry"] = None
                        st.session_state["object_registry_confirmed"] = False
                    st.success("Цифровой профиль проекта сформирован")
                    st.rerun()
                except Exception as exc:
                    st.error("Не удалось выполнить анализ. Откройте технические сведения ниже.")
                    st.exception(exc)

    with right:
        st.markdown('<div class="ec-section-title">Профиль проекта</div>', unsafe_allow_html=True)
        if st.session_state.get("result"):
            last_time = st.session_state.get("analysis_time")
            last_time_text = last_time.strftime("%d.%m.%Y %H:%M") if last_time else "—"
            st.markdown(
                f"""
                <div class="ec-card">
                    <div class="ec-card-title">Проект</div>
                    <div style="font-size:1.2rem;font-weight:720;color:#172033;">{st.session_state['project_name']}</div>
                    <div class="ec-card-note">{st.session_state.get('project_stage', 'Проектная документация')}</div>
                    <hr style="border:none;border-top:1px solid #e5e9f0;margin:1rem 0;">
                    <div class="ec-card-title">Последний анализ</div>
                    <div style="font-weight:650;color:#172033;">{last_time_text}</div>
                    <div class="ec-card-note">Статус: <span class="ec-status-ok">завершён</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="ec-empty">
                    <div style="font-size:2rem;margin-bottom:.5rem;">◫</div>
                    <div style="font-weight:700;color:#172033;">Проект ещё не проанализирован</div>
                    <div style="margin-top:.35rem;">Загрузите документы, чтобы получить цифровой профиль.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="ec-section-title">Как работает ExpertCheck</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    for col, number, title, text in [
        (f1, "01", "Распознавание", "Определяет типы загруженных разделов и извлекает текст по страницам."),
        (f2, "02", "Цифровой профиль", "Находит объекты, показатели и источники каждого значения."),
        (f3, "03", "Сверка", "Сопоставляет одинаковые показатели между разделами и отмечает расхождения."),
    ]:
        with col:
            st.markdown(
                f"""
                <div class="ec-card">
                    <div class="ec-card-title">{number}</div>
                    <div style="font-size:1.05rem;font-weight:720;color:#172033;">{title}</div>
                    <div class="ec-card-note">{text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------- Проект ----------
elif page == "Проект":
    st.markdown('<div class="ec-section-title">Карточка проекта</div>', unsafe_allow_html=True)
    if docs_df.empty:
        st.info("Сначала выполните анализ на главной странице.")
    else:
        left, right = st.columns([1.3, 1])
        with left:
            st.markdown(
                f"""
                <div class="ec-card">
                    <div class="ec-card-title">Наименование проекта</div>
                    <div style="font-size:1.35rem;font-weight:750;color:#172033;">{st.session_state['project_name']}</div>
                    <div class="ec-card-note">{st.session_state.get('project_stage', 'Проектная документация')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            types = []
            if "Тип документа" in docs_df.columns:
                types = sorted(docs_df["Тип документа"].dropna().astype(str).unique().tolist())
            st.markdown(
                f"""
                <div class="ec-card">
                    <div class="ec-card-title">Распознано разделов</div>
                    <div class="ec-card-value">{len(types)}</div>
                    <div class="ec-card-note">{', '.join(types) if types else 'Типы документов не определены'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="ec-section-title">Состав цифрового профиля</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        p1.metric("Документы", len(docs_df))
        p2.metric("Страницы", int(docs_df["Страниц"].sum()) if "Страниц" in docs_df.columns else 0)
        p3.metric("Извлечённые характеристики", len(findings_df))

# ---------- Документы ----------
elif page == "Документы":
    st.markdown('<div class="ec-section-title">Документы проекта</div>', unsafe_allow_html=True)
    if docs_df.empty:
        st.info("Документы появятся после анализа на главной странице.")
    else:
        st.dataframe(docs_df, use_container_width=True, hide_index=True)
        st.caption("Тип раздела определяется по имени файла, шифру и содержанию первых страниц.")

# ---------- Перечень объектов ----------
elif page == "Перечень объектов":
    st.markdown('<div class="ec-section-title">Перечень объектов</div>', unsafe_allow_html=True)
    st.caption("Проверьте автоматически сформированный перечень до запуска содержательной сверки. Позиция по генплану является основным идентификатором.")
    candidate_registry = build_candidate_registry(findings_df)
    if candidate_registry.empty:
        st.info("Перечень объектов пока не сформирован. Загрузите ПЗ, ПЗУ, АР и ТХ на главной странице.")
    else:
        source_df = pd.DataFrame(st.session_state["object_registry"]) if st.session_state.get("object_registry") else candidate_registry
        physical_count = int(pd.to_numeric(source_df.get("Количество", pd.Series(dtype=float)), errors="coerce").fillna(1).sum())
        confirmed_count = int(source_df["Статус"].astype(str).str.startswith("Подтверждено").sum()) if "Статус" in source_df else 0
        review_count = int(source_df["Статус"].astype(str).str.contains("уточн|подтверждения", case=False).sum()) if "Статус" in source_df else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Реестровых позиций", len(source_df))
        c2.metric("Физических объектов", physical_count)
        c3.metric("Подтверждено", confirmed_count)
        c4.metric("Требует внимания", review_count)

        st.info("Можно исправлять наименование, позицию, количество и исключать ошибочные строки. Служебные поля источников оставлены только для контроля распознавания.")
        edited = st.data_editor(
            source_df,
            key="object_registry_editor",
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            disabled=["Источники", "Подтверждений", "Статус", "Уверенность", "Страницы", "Исходные наименования"],
            column_config={
                "Включить": st.column_config.CheckboxColumn("Включить", help="Использовать объект в цифровом профиле"),
                "Позиция по ГП": st.column_config.TextColumn("Позиция по ГП", width="small"),
                "Наименование объекта": st.column_config.TextColumn("Наименование объекта", width="large", required=True),
                "Количество": st.column_config.NumberColumn("Количество", min_value=1, step=1, format="%d"),
                "Источники": st.column_config.TextColumn("Источники", width="medium"),
                "Исходные наименования": st.column_config.TextColumn("Исходные наименования", width="large"),
            },
        )
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            if st.button("Подтвердить перечень", type="primary", use_container_width=True):
                clean = edited.copy()
                clean["Включить"] = clean["Включить"].fillna(True).astype(bool)
                clean = clean[clean["Включить"]]
                clean["Количество"] = pd.to_numeric(clean["Количество"], errors="coerce").fillna(1).clip(lower=1).astype(int)
                clean = clean[clean["Наименование объекта"].fillna("").astype(str).str.strip().ne("")]
                st.session_state["object_registry"] = clean.to_dict("records")
                st.session_state["object_registry_confirmed"] = True
                st.success("Перечень объектов подтверждён и сохранён в текущей сессии")
                st.rerun()
        with b2:
            if st.button("Сбросить правки", use_container_width=True):
                st.session_state["object_registry"] = None
                st.session_state["object_registry_confirmed"] = False
                st.rerun()
        with b3:
            if registry_confirmed:
                st.success("Подтверждённый перечень используется как основа цифрового профиля.")
            else:
                st.warning("До подтверждения результаты по объектам считаются предварительными.")

        st.markdown('<div class="ec-section-title">Диагностика источников</div>', unsafe_allow_html=True)
        with st.expander("Показать исходные находки по объектам"):
            raw = findings_df[findings_df["parameter_code"].isin(["OBJECT_ENTRY", "OBJECT_CANDIDATE"])].copy()
            cols = ["document_type", "page", "genplan_position", "value_text", "confidence", "match_method", "context"]
            raw = raw[[x for x in cols if x in raw.columns]]
            st.dataframe(findings_for_user(raw), use_container_width=True, hide_index=True)

        if registry_confirmed and st.session_state.get("object_registry"):
            st.markdown('<div class="ec-section-title">Карточка объекта</div>', unsafe_allow_html=True)
            confirmed = pd.DataFrame(st.session_state["object_registry"])
            selected = st.selectbox("Выберите объект", confirmed["Наименование объекта"].astype(str).tolist())
            selected_row = confirmed[confirmed["Наименование объекта"].astype(str) == selected].iloc[0]
            left, right = st.columns([1.2, 2])
            with left:
                pos = selected_row.get("Позиция по ГП") or "—"
                qty = selected_row.get("Количество", 1)
                st.markdown(f"""<div class="ec-card"><div class="ec-card-title">Позиция по генплану</div><div class="ec-card-value">{pos}</div><div class="ec-card-note">Количество: {qty}</div></div>""", unsafe_allow_html=True)
            with right:
                srcs = selected_row.get("Источники", "—")
                st.markdown(f"""<div class="ec-card"><div class="ec-card-title">Наименование объекта</div><div style="font-size:1.18rem;font-weight:750;color:#172033;">{selected}</div><div class="ec-card-note">Источники: {srcs}</div></div>""", unsafe_allow_html=True)
            profile = characteristic_findings(findings_df)
            position = str(selected_row.get("Позиция по ГП") or "").strip()
            by_name = profile["object_hint"].fillna("").astype(str).map(_norm_object_key) == _norm_object_key(selected)
            by_position = profile["genplan_position"].fillna("").astype(str).str.strip().eq(position) if position else pd.Series(False, index=profile.index)
            object_profile = profile[by_name | by_position]
            if object_profile.empty:
                st.info("Для объекта пока не удалось надёжно извлечь характеристики.")
            else:
                st.dataframe(findings_for_user(object_profile), use_container_width=True, hide_index=True)

# ---------- Найденные данные ----------
elif page == "Характеристики проекта":
    st.markdown('<div class="ec-section-title">Характеристики проекта</div>', unsafe_allow_html=True)
    if findings_df.empty:
        st.info("Данные ещё не извлечены либо в PDF отсутствует текстовый слой.")
    else:
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            doc_options = sorted(characteristic_findings(findings_df)["document_type"].dropna().astype(str).unique()) if "document_type" in findings_df else []
            selected_docs = st.multiselect("Разделы", doc_options, default=doc_options)
        with filter_col2:
            param_options = sorted(characteristic_findings(findings_df)["parameter_name"].dropna().astype(str).unique()) if "parameter_name" in findings_df else []
            selected_params = st.multiselect("Характеристики", param_options)

        view = characteristic_findings(findings_df)
        if selected_docs and "document_type" in view:
            view = view[view["document_type"].isin(selected_docs)]
        if selected_params and "parameter_name" in view:
            view = view[view["parameter_name"].isin(selected_params)]

        display_cols = [
            "document_type", "page", "object_hint", "parameter_name",
            "value_text", "unit", "confidence", "context",
        ]
        available = [c for c in display_cols if c in view.columns]
        user_view = findings_for_user(view[available])
        st.dataframe(
            user_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Фрагмент документа": st.column_config.TextColumn(width="large"),
                "Уверенность": st.column_config.TextColumn(width="small"),
                "Страница": st.column_config.NumberColumn(format="%d"),
            },
        )
        st.caption(f"Показано характеристик: {len(view)} из {len(characteristic_findings(findings_df))}")

# ---------- Проверка ----------
elif page == "Проверки":
    st.markdown('<div class="ec-section-title">Результаты межраздельной проверки</div>', unsafe_allow_html=True)
    if comparisons_df.empty:
        st.info("Не найдено характеристик, которые удалось сопоставить минимум в двух разделах.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Всего сравнений", len(comparisons_df))
        c2.metric("Совпадает", matched_count)
        c3.metric("Требует проверки", mismatch_count)
        st.dataframe(comparisons_for_user(comparisons_df), use_container_width=True, hide_index=True)
        st.warning("Автоматический результат является предварительным и требует подтверждения специалистом.")

# ---------- Расхождения ----------
elif page == "Несоответствия":
    st.markdown('<div class="ec-section-title">Потенциальные расхождения</div>', unsafe_allow_html=True)
    if comparisons_df.empty or "status" not in comparisons_df.columns:
        st.info("Расхождения ещё не сформированы.")
    else:
        mismatch_df = comparisons_df[comparisons_df["status"] == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ"].copy()
        if mismatch_df.empty:
            st.success("В текущем анализе потенциальные расхождения не найдены.")
        else:
            st.metric("Требует ручной проверки", len(mismatch_df))
            st.dataframe(comparisons_for_user(mismatch_df), use_container_width=True, hide_index=True)

# ---------- Отчёт ----------
elif page == "Отчёт":
    st.markdown('<div class="ec-section-title">Отчёт по результатам анализа</div>', unsafe_allow_html=True)
    if docs_df.empty:
        st.info("Сформируйте цифровой профиль проекта, чтобы скачать отчёт.")
    else:
        safe_project = "".join(
            ch if ch.isalnum() or ch in " _-" else "_"
            for ch in st.session_state["project_name"]
        ).strip() or "Проект"
        st.markdown(
            """
            <div class="ec-card">
                <div style="font-size:1.05rem;font-weight:720;color:#172033;">Excel-отчёт ExpertCheck</div>
                <div class="ec-card-note">Сводка, документы, подтверждённый перечень объектов, характеристики и результаты межраздельной проверки.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.download_button(
            "Скачать Excel-отчёт",
            data=make_excel(st.session_state["project_name"], docs_df, findings_df, comparisons_df),
            file_name=f"ExpertCheck_{safe_project}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

# ---------- О версии ----------
elif page == "О версии":
    st.markdown('<div class="ec-section-title">ExpertCheck Demo Cloud v0.7.0</div>', unsafe_allow_html=True)
    st.markdown(
        """
        **Назначение версии:** сформировать проверяемый перечень объектов из нескольких разделов и не допускать, чтобы ошибки распознавания автоматически превращались в замечания.

        **Что изменилось:**
        - вкладка переименована в «Перечень объектов»;
        - перечень собирается из ПЗ, шифров АР/ТХ, ведомостей и заголовков подразделов;
        - поддержано продолжение многостраничной таблицы ПЗ без повторной шапки;
        - добавлено ручное редактирование, исключение и добавление объектов;
        - разделены реестровые позиции и физическое количество объектов;
        - межраздельная работа начинается с подтверждения перечня;
        - обновлён дизайн и добавлен пошаговый маршрут анализа.

        **Ограничения Demo:**
        - анализируется текстовый слой PDF;
        - сканы без текста могут не читаться;
        - автоматическое извлечение перечня требует подтверждения специалистом;
        - графические решения и нормативное соответствие пока не оцениваются;
        - найденное расхождение не является готовым замечанием экспертизы.
        """
    )

st.divider()
st.caption("ExpertCheck Demo — экспериментальный инструмент. Результаты требуют профессиональной проверки.")
