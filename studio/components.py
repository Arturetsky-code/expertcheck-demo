from __future__ import annotations
import streamlit as st

def header(version: str) -> None:
    st.markdown(f'''<div class="ec-topbar"><div class="ec-brand"><div class="ec-mark">EC</div><div><div class="ec-title">ExpertCheck Studio</div><div class="ec-sub">Цифровая проверка проектной документации перед экспертизой</div></div></div><div class="ec-version">{version}</div></div>''', unsafe_allow_html=True)

def hero(title: str, text: str, pill: str = "") -> None:
    p = f'<div class="ec-pill">{pill}</div>' if pill else ''
    st.markdown(f'<div class="ec-hero"><h2>{title}</h2><p>{text}</p>{p}</div>', unsafe_allow_html=True)

def card(label: str, value, note: str, kind: str = "info") -> None:
    st.markdown(f'<div class="ec-card ec-card-{kind}"><div class="ec-card-label">{label}</div><div class="ec-card-value">{value}</div><div class="ec-card-note">{note}</div></div>', unsafe_allow_html=True)

def section(title: str, note: str = "") -> None:
    st.markdown(f'<div class="ec-section"><h3>{title}</h3><p>{note}</p></div>', unsafe_allow_html=True)

def empty(text: str) -> None:
    st.markdown(f'<div class="ec-empty">{text}</div>', unsafe_allow_html=True)
