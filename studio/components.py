from __future__ import annotations
import html
import streamlit as st

def header(version: str) -> None:
    st.markdown(f'''<div class="ec-topbar"><div><div class="ec-title">Рабочее пространство проекта</div><div class="ec-sub">Предварительная проверка проектной документации перед экспертизой</div></div><div class="ec-version">{html.escape(version)}</div></div>''', unsafe_allow_html=True)

def sidebar_brand() -> None:
    st.markdown('''<div class="ec-sidebar-brand"><div class="ec-sidebar-logo"><div class="ec-sidebar-mark">EC</div><div><div class="ec-sidebar-name">ExpertCheck Studio</div><div class="ec-sidebar-caption">Инженерная проверка проекта</div></div></div></div>''', unsafe_allow_html=True)

def sidebar_group(text: str) -> None:
    st.markdown(f'<div class="ec-sidebar-group">{html.escape(text)}</div>', unsafe_allow_html=True)

def sidebar_project(name: str, status: str) -> None:
    st.markdown(f'<div class="ec-sidebar-project"><strong>{html.escape(name)}</strong><span>{html.escape(status)}</span></div>', unsafe_allow_html=True)

def hero(title: str, text: str, pill: str = "") -> None:
    p = f'<div class="ec-pill">{html.escape(pill)}</div>' if pill else ''
    st.markdown(f'<div class="ec-hero"><h2>{html.escape(title)}</h2><p>{html.escape(text)}</p>{p}</div>', unsafe_allow_html=True)

def card(label: str, value, note: str, kind: str = "info") -> None:
    st.markdown(f'<div class="ec-card ec-card-{kind}"><div class="ec-card-label">{html.escape(str(label))}</div><div class="ec-card-value">{html.escape(str(value))}</div><div class="ec-card-note">{html.escape(str(note))}</div></div>', unsafe_allow_html=True)

def section(title: str, note: str = "") -> None:
    st.markdown(f'<div class="ec-section"><h3>{html.escape(title)}</h3><p>{html.escape(note)}</p></div>', unsafe_allow_html=True)

def empty(text: str) -> None:
    st.markdown(f'<div class="ec-empty">{html.escape(text)}</div>', unsafe_allow_html=True)


def project_status_bar(name: str, status: str, *items: str) -> None:
    chips=''.join(f'<span class="ec-status-chip">{html.escape(str(x))}</span>' for x in items if x)
    st.markdown(f'<div class="ec-project-bar"><div><div class="ec-project-name">{html.escape(name)}</div><div class="ec-project-state">{html.escape(status)}</div></div><div class="ec-status-chips">{chips}</div></div>', unsafe_allow_html=True)

def timeline(events) -> None:
    rows=''.join(f'<div class="ec-timeline-row"><span class="ec-timeline-dot"></span><div><strong>{html.escape(str(title))}</strong><span>{html.escape(str(state))}</span></div></div>' for title,state in events)
    st.markdown(f'<div class="ec-timeline">{rows}</div>', unsafe_allow_html=True)
