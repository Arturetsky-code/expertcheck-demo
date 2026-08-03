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
    from analyzer import Finding, analyze_uploaded, compare_findings, load_json
except ModuleNotFoundError:
    from modules.analyzer import Finding, analyze_uploaded, compare_findings, load_json

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
        "active_page": "Обзор",
        "object_registry": None,
        "object_registry_confirmed": False,
        "raw_result": None,
        "registry_application_stats": None,
        "review_register": None,
        "review_register_saved": False,
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
    # Позиция по генплану не является частью наименования.
    value = re.sub(r"^\s*(?:поз(?:иция)?\.?\s*)?4\.\d+(?:\.\d+){0,2}\s*[-–—.:)]*\s*", "", value)
    # Удаляем частые служебные хвосты, попадающие из основных надписей.
    value = re.sub(r"\b(?:богер|завьялов|некрасова|гуськов|потапенко|смирнова|васильев|бурда|долгушин)\b", " ", value)
    value = re.sub(r"\bплощадка дробильно[- ]сортировочного комплекса\b.*$", "", value)
    return re.sub(r"[^а-яa-z0-9]+", "", value)


def _object_tokens(value: str) -> set[str]:
    import re
    text = str(value or "").lower().replace("ё", "е")
    text = re.sub(r"^\s*(?:поз(?:иция)?\.?\s*)?4\.\d+(?:\.\d+){0,2}\s*[-–—.:)]*\s*", "", text)
    stop = {"здание", "сооружение", "площадка", "комплекс", "объект", "с", "и", "для", "на", "по"}
    return {x for x in re.findall(r"[а-яa-z0-9]+", text) if len(x) > 2 and x not in stop}


def _name_similarity(left: str, right: str) -> float:
    a, b = _norm_object_key(left), _norm_object_key(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if min(len(a), len(b)) >= 8 and (a in b or b in a):
        return 0.94
    ta, tb = _object_tokens(left), _object_tokens(right)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)



def _extract_genplan_position(value: str) -> str:
    import re
    text = str(value or "")
    match = re.search(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)", text)
    return match.group(1) if match else ""


def _registry_aliases(row: pd.Series) -> list[str]:
    aliases = [str(row.get("Наименование объекта", "") or "")]
    raw = str(row.get("Исходные наименования", "") or "")
    aliases.extend(x.strip() for x in raw.split("|") if x.strip())
    return [x for x in aliases if x]


def apply_confirmed_registry(findings_df: pd.DataFrame, registry_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Применяет подтверждённый пользователем перечень к найденным характеристикам.

    Сначала используется позиция по генплану, затем однозначное совпадение
    наименования. Неуверенные связи не назначаются автоматически.
    """
    if findings_df.empty or registry_df.empty:
        return findings_df.copy(), {"mapped": 0, "by_position": 0, "by_name": 0, "unmapped": len(findings_df)}

    registry = registry_df.copy()
    registry["Позиция по ГП"] = registry.get("Позиция по ГП", "").fillna("").astype(str).str.strip()
    registry["Наименование объекта"] = registry["Наименование объекта"].fillna("").astype(str).str.strip()
    position_map = {
        row["Позиция по ГП"]: row["Наименование объекта"]
        for _, row in registry.iterrows()
        if row["Позиция по ГП"] and row["Наименование объекта"]
    }
    registry_records = []
    for _, row in registry.iterrows():
        registry_records.append({
            "position": str(row.get("Позиция по ГП", "") or "").strip(),
            "name": str(row.get("Наименование объекта", "") or "").strip(),
            "aliases": _registry_aliases(row),
        })

    result = findings_df.copy()
    stats = {"mapped": 0, "by_position": 0, "by_name": 0, "unmapped": 0}
    methods = []
    new_names = []
    new_positions = []
    for _, item in result.iterrows():
        code = str(item.get("parameter_code", "") or "")
        if code in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            new_names.append(str(item.get("object_hint", "") or ""))
            new_positions.append(str(item.get("genplan_position", "") or ""))
            methods.append("реестровая находка")
            continue
        position = str(item.get("genplan_position", "") or "").strip()
        source_name = str(item.get("object_hint", "") or "").strip()
        if not position:
            position = _extract_genplan_position(source_name) or _extract_genplan_position(str(item.get("context", "") or ""))
        if position and position in position_map:
            new_names.append(position_map[position])
            new_positions.append(position)
            methods.append("по позиции по генплану")
            stats["mapped"] += 1
            stats["by_position"] += 1
            continue

        scored = []
        for rec in registry_records:
            score = max((_name_similarity(source_name, alias) for alias in rec["aliases"]), default=0.0)
            if score:
                scored.append((score, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored and scored[0][0] >= 0.88 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.08):
            rec = scored[0][1]
            new_names.append(rec["name"])
            new_positions.append(rec["position"] or position)
            methods.append("по подтверждённому наименованию")
            stats["mapped"] += 1
            stats["by_name"] += 1
        else:
            new_names.append(source_name)
            new_positions.append(position)
            methods.append("не сопоставлено")
            stats["unmapped"] += 1
    result["object_hint"] = new_names
    result["genplan_position"] = new_positions
    result["registry_match_method"] = methods
    return result, stats


def recompute_comparisons(findings_df: pd.DataFrame) -> pd.DataFrame:
    parameters = load_json(CONFIG_DIR / "parameters.json")
    objects = []
    for row in findings_df.to_dict("records"):
        payload = {field: row.get(field) for field in Finding.__dataclass_fields__}
        payload["page"] = int(payload.get("page") or 0)
        payload["confidence"] = float(payload.get("confidence") or 0)
        objects.append(Finding(**payload))
    return pd.DataFrame(compare_findings(objects, parameters))


def registry_coverage(registry_df: pd.DataFrame) -> pd.DataFrame:
    if registry_df.empty:
        return registry_df.copy()
    result = registry_df.copy()
    source_series = result.get("Источники", pd.Series("", index=result.index)).fillna("").astype(str)
    for code in ["ПЗ", "ПЗУ1", "ПЗУ2", "АР1", "АР2", "ТХ1", "ТХ2"]:
        result[code] = source_series.str.split(" · ").map(lambda items: "✓" if code in items else "")
    result["Покрытие"] = result[["ПЗ", "ПЗУ1", "ПЗУ2", "АР1", "АР2", "ТХ1", "ТХ2"]].eq("✓").sum(axis=1)
    result["Проверить"] = result.apply(
        lambda r: "Нет позиции по ГП" if not str(r.get("Позиция по ГП", "")).strip()
        else ("Только один источник" if int(r.get("Подтверждений", 0) or 0) < 2 else ""),
        axis=1,
    )
    return result

def build_candidate_registry(findings_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Включить", "Позиция по ГП", "Наименование объекта", "Количество",
        "Источники", "Подтверждений", "Статус", "Уверенность", "Страницы",
        "Исходные наименования", "Способ объединения",
    ]
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
    candidates["preferred_name"] = candidates.apply(
        lambda r: str(r["object_hint"] or r["value_text"]).strip(), axis=1
    )
    # Если позиция присутствует внутри наименования, переносим её в отдельное поле.
    embedded_positions = candidates["preferred_name"].map(_extract_genplan_position)
    candidates.loc[candidates["genplan_position"].eq("") & embedded_positions.ne(""), "genplan_position"] = embedded_positions

    # Шаг 1. Создаём опорные группы по позиции по генплану.
    positioned = candidates[candidates["genplan_position"].ne("")].copy()
    no_position = candidates[candidates["genplan_position"].eq("")].copy()
    groups: dict[str, list[int]] = {}
    for idx, row in positioned.iterrows():
        groups.setdefault(f"GP:{row['genplan_position']}", []).append(idx)

    # Шаг 2. Находки без позиции присоединяем к позиции по совпадению наименования.
    # Это устраняет дубли вида «4.13 Здание проборазделки» / «Здание проборазделки».
    merge_method: dict[str, str] = {key: "По позиции по генплану" for key in groups}
    unassigned: list[int] = []
    for idx, row in no_position.iterrows():
        source_name = str(row["preferred_name"] or row["value_text"]).strip()
        scored: list[tuple[float, str]] = []
        for key, indices in groups.items():
            names = []
            for gi in indices:
                gr = candidates.loc[gi]
                names.extend([str(gr["object_hint"] or ""), str(gr["value_text"] or ""), str(gr["preferred_name"] or "")])
            score = max((_name_similarity(source_name, name) for name in names if name), default=0.0)
            if score > 0:
                scored.append((score, key))
        scored.sort(reverse=True)
        if scored and scored[0][0] >= 0.88 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.08):
            groups[scored[0][1]].append(idx)
            merge_method[scored[0][1]] = "Позиция + совпадение наименования"
        else:
            unassigned.append(idx)

    # Шаг 3. Оставшиеся находки без позиции группируем только между собой.
    name_groups: dict[str, list[int]] = {}
    for idx in unassigned:
        row = candidates.loc[idx]
        key_name = _norm_object_key(row["preferred_name"] or row["value_text"])
        if not key_name:
            key_name = f"row{idx}"
        key = f"NM:{key_name}"
        name_groups.setdefault(key, []).append(idx)
        merge_method[key] = "Только по наименованию — требуется подтверждение"
    groups.update(name_groups)

    rows = []
    for group_key, indices in groups.items():
        group = candidates.loc[indices].copy()
        position = next((x for x in group["genplan_position"].tolist() if x), "")
        group["name_len"] = group["value_text"].str.len()
        group["pz_rank"] = (group["parameter_code"] == "OBJECT_ENTRY").astype(int)
        # Предпочитаем наименование из таблицы ПЗ, затем каноническое object_hint.
        ranked = group.sort_values(["pz_rank", "confidence", "name_len"], ascending=False)
        best = ranked.iloc[0]
        pz_rows = ranked[ranked["parameter_code"] == "OBJECT_ENTRY"]
        if not pz_rows.empty:
            name = str(pz_rows.iloc[0]["value_text"] or pz_rows.iloc[0]["object_hint"]).strip()
        else:
            name = str(best["object_hint"] or best["value_text"]).strip()
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
        normalized_names = {_norm_object_key(x) for x in names if _norm_object_key(x)}
        if position and len(normalized_names) >= 3:
            # Разные варианты сами по себе не создают дубль, но требуют просмотра.
            status = "Требует уточнения наименования"
        rows.append({
            "Включить": True,
            "Позиция по ГП": position,
            "Наименование объекта": name,
            "Количество": quantity,
            "Источники": " · ".join(sections),
            "Подтверждений": len(sections),
            "Статус": status,
            "Уверенность": f"{float(group['confidence'].max()):.0%}",
            "Страницы": "; ".join(pages),
            "Исходные наименования": " | ".join(names),
            "Способ объединения": merge_method.get(group_key, ""),
        })
    result = pd.DataFrame(rows, columns=columns)
    if not result.empty:
        # Защитный финальный дедуп: одна позиция по ГП — одна строка.
        with_pos = result[result["Позиция по ГП"].astype(str).str.strip().ne("")]
        without_pos = result[result["Позиция по ГП"].astype(str).str.strip().eq("")]
        with_pos = with_pos.sort_values(["Подтверждений", "Уверенность"], ascending=False).drop_duplicates("Позиция по ГП", keep="first")
        result = pd.concat([with_pos, without_pos], ignore_index=True)
        result = result.sort_values(["Позиция по ГП", "Наименование объекта"], kind="stable").reset_index(drop=True)
    return result

def registry_for_export(findings_df: pd.DataFrame) -> pd.DataFrame:
    stored = st.session_state.get("object_registry")
    if stored:
        return pd.DataFrame(stored)
    return build_candidate_registry(findings_df)


REVIEW_STATUSES = [
    "Новое",
    "Подтверждено",
    "Ложное срабатывание",
    "Требует уточнения",
    "Передано в работу",
    "Устранено",
]
REVIEW_PRIORITIES = ["Высокий", "Средний", "Низкий"]
REVIEW_SECTIONS = ["Не назначен", "ПЗ", "ПЗУ", "АР", "КР", "ТХ", "ИОС", "ПОС", "ООС", "ПБ", "ГОЧС", "Изыскания", "Межраздельное"]


def _review_key(row: pd.Series | dict) -> str:
    getter = row.get
    code = str(getter("check_code", "") or "").strip()
    obj = str(getter("object", "") or "").strip()
    param = str(getter("parameter_code", "") or getter("parameter_name", "") or "").strip()
    return "|".join([code, obj, param])


def build_review_register(comparisons_df: pd.DataFrame, existing: list[dict] | None = None) -> pd.DataFrame:
    columns = [
        "Ключ", "Включить в отчёт", "Объект", "Характеристика", "Автоматический результат",
        "Рабочий статус", "Приоритет", "Ответственный раздел", "Комментарий проверяющего",
        "Разделы-источники", "Значения по разделам", "Источники", "Код проверки",
    ]
    if comparisons_df.empty:
        return pd.DataFrame(columns=columns)
    work = comparisons_df.copy()
    if "status" in work.columns:
        work = work[work["status"].isin(["ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ", "ТРЕБУЕТ УТОЧНЕНИЯ"])].copy()
    old_map = {_review_key(x): x for x in (existing or [])}
    rows = []
    for _, row in work.iterrows():
        key = _review_key(row)
        old = old_map.get(key, {})
        auto_status = str(row.get("status", "") or "")
        default_status = "Требует уточнения" if auto_status == "ТРЕБУЕТ УТОЧНЕНИЯ" else "Новое"
        priority = str(old.get("Приоритет") or row.get("priority") or "Средний")
        if priority.capitalize() in REVIEW_PRIORITIES:
            priority = priority.capitalize()
        elif priority not in REVIEW_PRIORITIES:
            priority = "Средний"
        rows.append({
            "Ключ": key,
            "Включить в отчёт": bool(old.get("Включить в отчёт", True)),
            "Объект": str(row.get("object", "") or ""),
            "Характеристика": str(row.get("parameter_name", "") or ""),
            "Автоматический результат": auto_status,
            "Рабочий статус": str(old.get("Рабочий статус") or default_status),
            "Приоритет": priority,
            "Ответственный раздел": str(old.get("Ответственный раздел") or "Не назначен"),
            "Комментарий проверяющего": str(old.get("Комментарий проверяющего") or ""),
            "Разделы-источники": str(row.get("documents", "") or ""),
            "Значения по разделам": str(row.get("document_values", "") or ""),
            "Источники": str(row.get("sources", "") or ""),
            "Код проверки": str(row.get("check_code", "") or ""),
        })
    return pd.DataFrame(rows, columns=columns)


def current_review_register(comparisons_df: pd.DataFrame) -> pd.DataFrame:
    existing = st.session_state.get("review_register")
    return build_review_register(comparisons_df, existing)


def review_metrics(review_df: pd.DataFrame) -> dict[str, int]:
    if review_df.empty:
        return {"total": 0, "confirmed": 0, "false": 0, "work": 0, "resolved": 0, "included": 0}
    statuses = review_df["Рабочий статус"].fillna("").astype(str)
    return {
        "total": len(review_df),
        "confirmed": int(statuses.eq("Подтверждено").sum()),
        "false": int(statuses.eq("Ложное срабатывание").sum()),
        "work": int(statuses.isin(["Новое", "Требует уточнения", "Передано в работу"]).sum()),
        "resolved": int(statuses.eq("Устранено").sum()),
        "included": int(review_df["Включить в отчёт"].fillna(False).astype(bool).sum()),
    }



def parameter_metadata() -> dict[str, dict]:
    try:
        return {str(item.get("code")): item for item in load_json(CONFIG_DIR / "parameters.json")}
    except Exception:
        return {}


def build_object_passport(object_name: str, genplan_position: str, findings_df: pd.DataFrame, comparisons_df: pd.DataFrame) -> pd.DataFrame:
    """Строит цифровой паспорт объекта: одна строка на характеристику, значения по разделам и итог сверки."""
    profile = characteristic_findings(findings_df)
    if profile.empty:
        return pd.DataFrame()
    by_name = profile["object_hint"].fillna("").astype(str).map(_norm_object_key).eq(_norm_object_key(object_name))
    if genplan_position:
        by_position = profile["genplan_position"].fillna("").astype(str).str.strip().eq(str(genplan_position).strip())
    else:
        by_position = pd.Series(False, index=profile.index)
    rows = profile[by_name | by_position].copy()
    if rows.empty:
        return pd.DataFrame()
    meta = parameter_metadata()
    records=[]
    for (code, name, unit), group in rows.groupby(["parameter_code","parameter_name","unit"], dropna=False):
        values={}
        sources=[]
        confidence=[]
        for doc, doc_group in group.groupby("document_type"):
            best=doc_group.sort_values("confidence", ascending=False).iloc[0]
            value_text=str(best.get("value_text","") or "")
            values[str(doc)] = value_text
            sources.append(f"{doc}, стр. {int(best.get('page',0) or 0)}")
            confidence.append(float(best.get("confidence",0) or 0))
        comp = comparisons_df[
            comparisons_df.get("object", pd.Series(dtype=str)).fillna("").astype(str).map(_norm_object_key).eq(_norm_object_key(object_name)) &
            comparisons_df.get("parameter_code", pd.Series(dtype=str)).fillna("").astype(str).eq(str(code))
        ] if not comparisons_df.empty else pd.DataFrame()
        status = str(comp.iloc[0].get("status")) if not comp.empty else ("НЕДОСТАТОЧНО ДАННЫХ" if len(values)<2 else "НЕ ПРОВЕРЕНО")
        category = str(meta.get(str(code),{}).get("group") or "Прочие характеристики")
        rec={
            "Группа": category,
            "Характеристика": str(name),
            "Ед. изм.": UNIT_LABELS.get(str(unit).lower(), str(unit or "")),
            "Статус": status,
            "Источников": len(values),
            "Уверенность": f"{max(confidence, default=0):.0%}",
            "Источники": "; ".join(sources),
        }
        for doc in ["ПЗ","ПЗУ1","ПЗУ2","АР1","АР2","ТХ1","ТХ2"]:
            rec[doc]=values.get(doc, "—")
        records.append(rec)
    result=pd.DataFrame(records)
    order={"Идентификация":0,"Геометрия":1,"Технология":2,"Электроснабжение":3,"Водоснабжение":4,"Пожарная безопасность":5,"Прочие характеристики":9}
    result["_order"]=result["Группа"].map(order).fillna(8)
    return result.sort_values(["_order","Группа","Характеристика"]).drop(columns="_order")


def object_profile_metrics(passport: pd.DataFrame) -> dict[str,int]:
    if passport.empty:
        return {"total":0,"confirmed":0,"mismatch":0,"insufficient":0}
    statuses=passport["Статус"].fillna("").astype(str)
    return {
        "total":len(passport),
        "confirmed":int(statuses.eq("СОВПАДАЕТ").sum()),
        "mismatch":int(statuses.str.contains("РАСХОЖДЕНИЕ|УТОЧНЕНИЯ", regex=True).sum()),
        "insufficient":int(statuses.str.contains("НЕДОСТАТОЧНО|НЕ ПРОВЕРЕНО", regex=True).sum()),
    }

def make_excel(project_name: str, docs_df: pd.DataFrame, findings_df: pd.DataFrame, comparisons_df: pd.DataFrame, review_df: pd.DataFrame | None = None) -> bytes:
    mismatch_count, matched_count = comparison_counts(comparisons_df)
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        summary = pd.DataFrame(
            [
                ["Проект", project_name],
                ["Версия ExpertCheck", "Demo Cloud v0.11.0"],
                ["Дата проверки", datetime.now().strftime("%d.%m.%Y %H:%M")],
                ["Документов", len(docs_df)],
                ["Извлечено характеристик", len(findings_df)],
                ["Потенциальных расхождений", mismatch_count],
                ["Совпадений", matched_count],
                ["Требуют уточнения", clarification_count(comparisons_df)],
                ["Рабочих записей в реестре", len(review_df) if review_df is not None else 0],
                ["Подтверждённых замечаний", int((review_df["Рабочий статус"] == "Подтверждено").sum()) if review_df is not None and not review_df.empty else 0],
            ],
            columns=["Характеристика", "Значение"],
        )
        summary.to_excel(writer, sheet_name="Сводка", index=False)
        docs_df.to_excel(writer, sheet_name="Документы", index=False)
        registry_coverage(registry_for_export(findings_df)).to_excel(writer, sheet_name="Перечень объектов", index=False)
        findings_for_user(characteristic_findings(findings_df)).to_excel(writer, sheet_name="Характеристики", index=False)
        comparisons_for_user(comparisons_df).to_excel(writer, sheet_name="Проверки", index=False)
        if review_df is not None:
            export_review = review_df.drop(columns=["Ключ"], errors="ignore")
            export_review.to_excel(writer, sheet_name="Реестр замечаний", index=False)

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
        "Обзор",
        "Объекты",
        "Проверки",
        "Замечания",
        "Отчёт",
    ]
    page = st.radio("Навигация", pages, label_visibility="collapsed", key="active_page")

    st.divider()
    st.markdown("**Текущий проект**")
    st.caption(st.session_state.get("project_name", "Новый проект"))
    if st.session_state.get("result"):
        st.success("Анализ завершён")
    else:
        st.info("Документы не проверены")
    st.caption("Demo Cloud v0.11.0")


# ---------- Общая шапка ----------
st.markdown(
    """
    <div class="ec-header">
      <div>
        <div class="ec-brand">Expert<span>Check</span></div>
        <div class="ec-subtitle">Интеллектуальная система предэкспертной проверки проектной документации</div>
      </div>
      <div class="ec-badge">Demo Cloud v0.11.0</div>
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
      <div class="ec-step {'done' if registry_confirmed and not characteristic_findings(findings_df).empty else ''}">03<strong>Паспорта объектов</strong></div>
      <div class="ec-step {'done' if not comparisons_df.empty else ''}">04<strong>Проверки</strong></div>
    </div>""", unsafe_allow_html=True
)

# ---------- Главная ----------
if page == "Обзор":
    st.markdown('<div class="ec-section-title">Обзор проекта</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Документов", len(docs_df), help="Количество документов в последнем анализе")
    c2.metric("Объектов", len(registry_df), help="Количество позиций в предварительном или подтверждённом перечне")
    c3.metric("Расхождений", mismatch_count, help="Потенциальные межраздельные расхождения")
    c4.metric("Подтверждено", matched_count, help="Характеристики, совпадающие между разделами")

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
                        st.session_state["raw_result"] = result
                        st.session_state["result"] = result
                        st.session_state["project_name"] = project_name.strip() or "Новый проект"
                        st.session_state["project_stage"] = project_stage
                        st.session_state["analysis_time"] = datetime.now()
                        st.session_state["object_registry"] = None
                        st.session_state["object_registry_confirmed"] = False
                        st.session_state["registry_application_stats"] = None
                        st.session_state["review_register"] = None
                        st.session_state["review_register_saved"] = False
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
elif page == "Объекты":
    st.markdown('<div class="ec-section-title">Объекты и цифровые паспорта</div>', unsafe_allow_html=True)
    st.caption("Проверьте автоматически сформированный перечень до запуска содержательной сверки. Позиция по генплану является основным идентификатором.")
    candidate_registry = build_candidate_registry(findings_df)
    if candidate_registry.empty:
        st.info("Перечень объектов пока не сформирован. Загрузите ПЗ, ПЗУ, АР и ТХ на главной странице.")
    else:
        source_df = pd.DataFrame(st.session_state["object_registry"]) if st.session_state.get("object_registry") else candidate_registry
        physical_count = int(pd.to_numeric(source_df.get("Количество", pd.Series(dtype=float)), errors="coerce").fillna(1).sum())
        confirmed_count = int(source_df["Статус"].astype(str).str.startswith("Подтверждено").sum()) if "Статус" in source_df else 0
        review_count = int(source_df["Статус"].astype(str).str.contains("уточн|подтверждения", case=False).sum()) if "Статус" in source_df else 0
        auto_merged = int(source_df.get("Способ объединения", pd.Series(dtype=str)).astype(str).str.contains("совпадение наименования", case=False).sum())
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Позиций по ГП", int(source_df["Позиция по ГП"].astype(str).str.strip().ne("").sum()))
        c2.metric("Физических объектов", physical_count)
        c3.metric("Подтверждено", confirmed_count)
        c4.metric("Объединено автоматически", auto_merged)
        c5.metric("Требует внимания", review_count)

        st.info("Записи без позиции по генплану автоматически присоединяются к позиции с совпадающим наименованием. После подтверждения перечень применяется к характеристикам и межраздельным проверкам.")
        mapping_stats = st.session_state.get("registry_application_stats")
        if registry_confirmed and mapping_stats:
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Связано характеристик", mapping_stats.get("mapped", 0))
            s2.metric("По позиции ГП", mapping_stats.get("by_position", 0))
            s3.metric("По наименованию", mapping_stats.get("by_name", 0))
            s4.metric("Не сопоставлено", mapping_stats.get("unmapped", 0))
        attention = source_df[source_df["Статус"].astype(str).str.contains("уточн|подтверждения", case=False, na=False)] if "Статус" in source_df else pd.DataFrame()
        if not attention.empty:
            with st.expander(f"Сначала проверить: {len(attention)} строк", expanded=True):
                preview_cols = ["Позиция по ГП", "Наименование объекта", "Источники", "Статус", "Способ объединения"]
                st.dataframe(attention[[c for c in preview_cols if c in attention.columns]], use_container_width=True, hide_index=True)
        coverage_view = registry_coverage(source_df)
        with st.expander("Матрица присутствия объектов по разделам", expanded=False):
            coverage_cols = [
                "Позиция по ГП", "Наименование объекта", "Количество",
                "ПЗ", "ПЗУ1", "ПЗУ2", "АР1", "АР2", "ТХ1", "ТХ2",
                "Покрытие", "Проверить",
            ]
            st.dataframe(
                coverage_view[[c for c in coverage_cols if c in coverage_view.columns]],
                use_container_width=True, hide_index=True,
            )

        edited = st.data_editor(
            source_df,
            key="object_registry_editor",
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            disabled=["Источники", "Подтверждений", "Статус", "Уверенность", "Страницы", "Исходные наименования", "Способ объединения"],
            column_config={
                "Включить": st.column_config.CheckboxColumn("Включить", help="Использовать объект в цифровом профиле"),
                "Позиция по ГП": st.column_config.TextColumn("Позиция по ГП", width="small"),
                "Наименование объекта": st.column_config.TextColumn("Наименование объекта", width="large", required=True),
                "Количество": st.column_config.NumberColumn("Количество", min_value=1, step=1, format="%d"),
                "Источники": st.column_config.TextColumn("Источники", width="medium"),
                "Исходные наименования": st.column_config.TextColumn("Исходные наименования", width="large"),
                "Способ объединения": st.column_config.TextColumn("Как объединено", width="medium", help="Показывает, почему находки из разных разделов сведены в одну строку"),
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
                # Подтверждённый перечень сразу применяется к характеристикам и проверкам.
                base_result = st.session_state.get("raw_result") or st.session_state.get("result")
                if base_result:
                    base_docs, base_findings, _ = base_result
                    mapped_findings, mapping_stats = apply_confirmed_registry(
                        pd.DataFrame(base_findings), clean
                    )
                    updated_comparisons = recompute_comparisons(mapped_findings)
                    st.session_state["result"] = (
                        base_docs, mapped_findings.to_dict("records"), updated_comparisons.to_dict("records")
                    )
                    st.session_state["registry_application_stats"] = mapping_stats
                st.success("Перечень подтверждён и применён к характеристикам и межраздельным проверкам")
                st.rerun()
        with b2:
            if st.button("Сбросить правки", use_container_width=True):
                st.session_state["object_registry"] = None
                st.session_state["object_registry_confirmed"] = False
                st.session_state["registry_application_stats"] = None
                if st.session_state.get("raw_result"):
                    st.session_state["result"] = st.session_state["raw_result"]
                st.rerun()
        with b3:
            if registry_confirmed:
                st.success("Подтверждённый перечень используется как основа цифрового профиля.")
            else:
                st.warning("До подтверждения результаты по объектам считаются предварительными.")

        st.markdown('<div class="ec-section-title">Диагностика источников</div>', unsafe_allow_html=True)
        with st.expander("Показать исходные находки по объектам"):
            raw = findings_df[findings_df["parameter_code"].isin(["OBJECT_ENTRY", "OBJECT_CANDIDATE"])].copy()
            cols = ["document_type", "page", "genplan_position", "value_text", "object_hint", "confidence", "match_method", "context"]
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
            passport = build_object_passport(selected, position, findings_df, comparisons_df)
            if passport.empty:
                st.info("Для объекта пока не удалось надёжно извлечь характеристики.")
            else:
                pm = object_profile_metrics(passport)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Характеристик", pm["total"])
                m2.metric("Подтверждено", pm["confirmed"])
                m3.metric("Требует внимания", pm["mismatch"])
                m4.metric("Недостаточно данных", pm["insufficient"])
                st.markdown("#### Цифровой паспорт объекта")
                st.dataframe(
                    passport, use_container_width=True, hide_index=True,
                    column_config={
                        "Группа": st.column_config.TextColumn(width="medium"),
                        "Характеристика": st.column_config.TextColumn(width="large"),
                        "Источники": st.column_config.TextColumn(width="large"),
                    },
                )
                with st.expander("Диагностика исходных извлечений", expanded=False):
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

# ---------- Реестр замечаний ----------
elif page == "Замечания":
    st.markdown('<div class="ec-section-title">Реестр предэкспертных замечаний</div>', unsafe_allow_html=True)
    st.caption("Автоматическая находка становится рабочим замечанием только после проверки специалистом.")
    review_df = current_review_register(comparisons_df)
    if review_df.empty:
        st.success("Потенциальные расхождения и неопределённые результаты для включения в реестр не найдены.")
    else:
        metrics = review_metrics(review_df)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Записей", metrics["total"])
        c2.metric("В работе", metrics["work"])
        c3.metric("Подтверждено", metrics["confirmed"])
        c4.metric("Ложных срабатываний", metrics["false"])
        c5.metric("Устранено", metrics["resolved"])

        st.info("Измените рабочий статус, приоритет и ответственный раздел. Ложные срабатывания можно исключить из отчёта, сохранив их в истории проверки.")
        edited_review = st.data_editor(
            review_df,
            key="review_register_editor",
            use_container_width=True,
            hide_index=True,
            disabled=["Ключ", "Объект", "Характеристика", "Автоматический результат", "Разделы-источники", "Значения по разделам", "Источники", "Код проверки"],
            column_config={
                "Ключ": None,
                "Включить в отчёт": st.column_config.CheckboxColumn("В отчёт", help="Включить запись в итоговый реестр замечаний"),
                "Объект": st.column_config.TextColumn("Объект", width="large"),
                "Характеристика": st.column_config.TextColumn("Характеристика", width="medium"),
                "Автоматический результат": st.column_config.TextColumn("Результат системы", width="medium"),
                "Рабочий статус": st.column_config.SelectboxColumn("Рабочий статус", options=REVIEW_STATUSES, required=True, width="medium"),
                "Приоритет": st.column_config.SelectboxColumn("Приоритет", options=REVIEW_PRIORITIES, required=True, width="small"),
                "Ответственный раздел": st.column_config.SelectboxColumn("Ответственный раздел", options=REVIEW_SECTIONS, required=True, width="medium"),
                "Комментарий проверяющего": st.column_config.TextColumn("Комментарий проверяющего", width="large"),
                "Разделы-источники": st.column_config.TextColumn("Разделы", width="medium"),
                "Значения по разделам": st.column_config.TextColumn("Значения по разделам", width="large"),
                "Источники": st.column_config.TextColumn("Источники", width="large"),
                "Код проверки": st.column_config.TextColumn("Код проверки", width="small"),
            },
        )
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            if st.button("Сохранить реестр", type="primary", use_container_width=True):
                clean = edited_review.copy()
                clean["Включить в отчёт"] = clean["Включить в отчёт"].fillna(False).astype(bool)
                st.session_state["review_register"] = clean.to_dict("records")
                st.session_state["review_register_saved"] = True
                st.success("Реестр сохранён в текущей сессии")
                st.rerun()
        with b2:
            if st.button("Сбросить решения", use_container_width=True):
                st.session_state["review_register"] = None
                st.session_state["review_register_saved"] = False
                st.rerun()
        with b3:
            if st.session_state.get("review_register_saved"):
                st.success("Рабочие решения сохранены и будут включены в Excel-отчёт.")
            else:
                st.warning("Изменения в таблице необходимо сохранить отдельной кнопкой.")

        saved_or_edited = edited_review
        included = saved_or_edited[saved_or_edited["Включить в отчёт"].fillna(False).astype(bool)]
        with st.expander(f"Предварительный итоговый реестр: {len(included)} записей", expanded=False):
            cols = ["Объект", "Характеристика", "Рабочий статус", "Приоритет", "Ответственный раздел", "Комментарий проверяющего", "Значения по разделам"]
            st.dataframe(included[[c for c in cols if c in included.columns]], use_container_width=True, hide_index=True)

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
                <div class="ec-card-note">Сводка, документы, подтверждённый перечень объектов, характеристики, автоматические проверки и управляемый реестр замечаний.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.download_button(
            "Скачать Excel-отчёт",
            data=make_excel(
                st.session_state["project_name"], docs_df, findings_df, comparisons_df,
                current_review_register(comparisons_df),
            ),
            file_name=f"ExpertCheck_{safe_project}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

# ---------- О версии ----------
elif page == "О версии":
    st.markdown('<div class="ec-section-title">ExpertCheck Demo Cloud v0.11.0</div>', unsafe_allow_html=True)
    st.markdown(
        """
        **Назначение версии:** превратить автоматические результаты проверки в управляемый реестр предэкспертных замечаний.

        **Что добавлено:**
        - рабочие статусы замечаний;
        - подтверждение и отклонение ложных срабатываний;
        - изменение приоритета;
        - назначение ответственного раздела;
        - комментарий проверяющего;
        - включение или исключение записи из итогового отчёта;
        - сохранение решений в текущей пользовательской сессии;
        - отдельный лист «Реестр замечаний» в Excel-отчёте.

        **Ограничения Demo:**
        - данные пока не сохраняются после перезапуска облачного приложения;
        - регистрация, личные кабинеты и постоянное хранилище будут добавляться позднее;
        - анализируется текстовый слой PDF;
        - автоматическая находка требует профессионального подтверждения;
        - графические решения и нормативное соответствие пока не оцениваются полностью.
        """
    )

st.divider()
st.caption("ExpertCheck Demo — экспериментальный инструмент. Результаты требуют профессиональной проверки.")
