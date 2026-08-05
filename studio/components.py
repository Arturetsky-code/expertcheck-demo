from __future__ import annotations
import html
import re
import streamlit as st

_STATUS_RULES = (
    ("bad", ("крит", "ошиб", "не пройден", "высокий риск")),
    ("alert", ("расхожд", "конфликт", "отсутствует", "неполный")),
    ("warn", ("требует", "провер", "не подтверж", "недостаточно", "формируется")),
    ("ok", ("подтверж", "совпад", "выполнен", "заверш", "загружен", "готов")),
    ("info", ("анализ", "обработ", "выполня", "в работе")),
)

def status_kind(value: object, default: str = "neutral") -> str:
    text = str(value or "").strip().lower()
    for kind, tokens in _STATUS_RULES:
        if any(token in text for token in tokens):
            return kind
    return default

def status_badge(value: object, kind: str | None = None) -> str:
    text = html.escape(str(value or "Не определено"))
    resolved = kind or status_kind(value)
    return f'<span class="ec-status-badge ec-status-{resolved}">{text}</span>'

def header(version: str) -> None:
    st.markdown(
        f'<div class="ec-topbar"><div><div class="ec-title">Рабочее пространство проекта</div>'
        f'<div class="ec-sub">Предварительная проверка проектной документации перед экспертизой</div>'
        f'</div><div class="ec-version">{html.escape(version)}</div></div>',
        unsafe_allow_html=True,
    )

def sidebar_brand() -> None:
    st.markdown(
        '<div class="ec-sidebar-brand"><div class="ec-sidebar-logo">'
        '<div class="ec-sidebar-mark">EC</div><div><div class="ec-sidebar-name">ExpertCheck Studio</div>'
        '<div class="ec-sidebar-caption">Инженерная проверка проекта</div></div></div></div>',
        unsafe_allow_html=True,
    )

def sidebar_group(text: str) -> None:
    st.markdown(f'<div class="ec-sidebar-group">{html.escape(text)}</div>', unsafe_allow_html=True)

def sidebar_project(name: str, status: str) -> None:
    badge = status_badge(status)
    st.markdown(
        f'<div class="ec-sidebar-project"><strong>{html.escape(name)}</strong>'
        f'<div class="ec-sidebar-status">{badge}</div></div>',
        unsafe_allow_html=True,
    )

def hero(title: str, text: str, pill: str = "") -> None:
    p = f'<div class="ec-pill">{html.escape(pill)}</div>' if pill else ""
    st.markdown(
        f'<div class="ec-hero"><h2>{html.escape(title)}</h2><p>{html.escape(text)}</p>{p}</div>',
        unsafe_allow_html=True,
    )

def card(label: str, value, note: str, kind: str = "info") -> None:
    value_text = str(value)
    is_status = bool(re.search(
        r'(подтверж|совпад|требует|расхожд|конфликт|ошиб|недостаточно|не провер|формируется|заверш|готов|загружен)',
        value_text,
        re.I,
    ))
    if is_status:
        value_html = f'<div class="ec-card-status">{status_badge(value_text, status_kind(value_text, kind))}</div>'
    else:
        value_html = f'<div class="ec-card-value">{html.escape(value_text)}</div>'
    st.markdown(
        f'<div class="ec-card ec-card-{kind}"><div class="ec-card-label">{html.escape(str(label))}</div>'
        f'{value_html}<div class="ec-card-note">{html.escape(str(note))}</div></div>',
        unsafe_allow_html=True,
    )

def section(title: str, note: str = "") -> None:
    st.markdown(
        f'<div class="ec-section"><h3>{html.escape(title)}</h3><p>{html.escape(note)}</p></div>',
        unsafe_allow_html=True,
    )

def empty(text: str) -> None:
    st.markdown(f'<div class="ec-empty">{html.escape(text)}</div>', unsafe_allow_html=True)

def project_status_bar(name: str, status: str, *items: str) -> None:
    chips = ''.join(status_badge(x) for x in items if x)
    state = status_badge(status)
    st.markdown(
        f'<div class="ec-project-bar"><div><div class="ec-project-name">{html.escape(name)}</div>'
        f'<div class="ec-project-state">{state}</div></div><div class="ec-status-chips">{chips}</div></div>',
        unsafe_allow_html=True,
    )

def timeline(events) -> None:
    rows = ''.join(
        f'<div class="ec-timeline-row"><span class="ec-timeline-dot"></span><div>'
        f'<strong>{html.escape(str(title))}</strong><span>{html.escape(str(state))}</span></div></div>'
        for title, state in events
    )
    st.markdown(f'<div class="ec-timeline">{rows}</div>', unsafe_allow_html=True)
