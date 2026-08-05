from __future__ import annotations
import streamlit as st

CSS = r'''
<style>
:root{
 --ec-bg:#F3F5F7;--ec-surface:#FFFFFF;--ec-surface-soft:#F8FAFB;
 --ec-sidebar:#17212B;--ec-sidebar-hover:#243342;--ec-sidebar-text:#EAF0F4;
 --ec-text:#18212B;--ec-muted:#66717E;--ec-line:#E1E6EB;
 --ec-brand:#2F6FED;--ec-brand-dark:#245AC4;
 --ec-ok:#21875A;--ec-warn:#C48616;--ec-alert:#D96C22;--ec-bad:#C83C3C;--ec-neutral:#66717E;
}
html,body,[class*="css"]{font-family:"Segoe UI",Arial,sans-serif}
.stApp{background:var(--ec-bg);color:var(--ec-text)}
.block-container{max-width:1560px;padding-top:1.1rem;padding-bottom:2.5rem}
#MainMenu,footer{visibility:hidden}header[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:var(--ec-sidebar);border-right:1px solid #263440}
[data-testid="stSidebar"]>div{padding-top:.75rem}
[data-testid="stSidebar"] *{color:var(--ec-sidebar-text)}
[data-testid="stSidebar"] hr{border-color:#33424E;margin:.85rem 0}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{margin-bottom:.2rem}
[data-testid="stSidebar"] div[role="radiogroup"]{gap:.18rem}
[data-testid="stSidebar"] div[role="radiogroup"] label{
 background:transparent;border-radius:8px;padding:.54rem .7rem;margin:.05rem 0;transition:.15s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:var(--ec-sidebar-hover)}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:#2B3E50}
[data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stMarkdownContainer"] p{font-size:.9rem;font-weight:600}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"]{display:none}
[data-testid="stSidebar"] button{background:#233442;border-color:#3B4D5C;color:#fff}
[data-testid="stSidebar"] .stAlert{background:#21323F;border-color:#344858}
[data-testid="stSidebar"] .stAlert p{color:#DDE7ED!important}

.ec-sidebar-brand{padding:.3rem .3rem .75rem}.ec-sidebar-logo{display:flex;align-items:center;gap:.7rem}
.ec-sidebar-mark{width:36px;height:36px;border-radius:9px;background:var(--ec-brand);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;letter-spacing:.02em}
.ec-sidebar-name{font-weight:750;font-size:1rem;color:#fff}.ec-sidebar-caption{font-size:.75rem;color:#9FB0BD;margin-top:.1rem}
.ec-sidebar-group{font-size:.68rem;color:#8496A4!important;text-transform:uppercase;letter-spacing:.09em;font-weight:700;margin:.6rem .25rem .25rem}
.ec-sidebar-project{border-top:1px solid #33424E;margin-top:.8rem;padding-top:.8rem}.ec-sidebar-project strong{display:block;font-size:.83rem;color:#fff}.ec-sidebar-project span{font-size:.73rem;color:#9FB0BD}

.ec-topbar{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-bottom:1rem}
.ec-title{font-size:1.35rem;font-weight:760}.ec-sub{color:var(--ec-muted);font-size:.84rem;margin-top:.08rem}
.ec-version{color:#365A8B;background:#EAF1FC;border:1px solid #D4E1F7;border-radius:999px;padding:.32rem .65rem;font-size:.73rem;font-weight:650}
.ec-hero{background:var(--ec-surface);border:1px solid var(--ec-line);border-radius:16px;padding:1.25rem 1.4rem;margin-bottom:1rem;box-shadow:0 4px 18px rgba(25,39,52,.05)}
.ec-hero h2{margin:0;color:var(--ec-text);font-size:1.42rem}.ec-hero p{margin:.38rem 0 0;color:var(--ec-muted)}
.ec-pill{display:inline-flex;background:#EEF4FE;color:#315F9F;border:1px solid #D8E5F9;border-radius:999px;padding:.3rem .62rem;font-size:.75rem;margin-top:.75rem;font-weight:600}
.ec-card{background:var(--ec-surface);border:1px solid var(--ec-line);border-radius:14px;padding:1rem 1.05rem;box-shadow:0 2px 12px rgba(20,42,56,.035);height:100%}
.ec-card-label{color:var(--ec-muted);font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em}.ec-card-value{font-size:1.65rem;font-weight:760;margin-top:.22rem}.ec-card-note{color:var(--ec-muted);font-size:.79rem;margin-top:.3rem}
.ec-card-ok{border-left:4px solid var(--ec-ok)}.ec-card-warn{border-left:4px solid var(--ec-warn)}.ec-card-bad{border-left:4px solid var(--ec-bad)}.ec-card-info{border-left:4px solid var(--ec-brand)}
.ec-section{margin:1.15rem 0 .58rem}.ec-section h3{margin:0;font-size:1.08rem}.ec-section p{margin:.18rem 0 0;color:var(--ec-muted);font-size:.82rem}
.ec-empty{background:#fff;border:1px dashed #B7C5CD;border-radius:14px;padding:1.8rem;text-align:center;color:var(--ec-muted)}
.ec-progress-panel{background:#fff;border:1px solid var(--ec-line);border-radius:16px;padding:1.2rem 1.3rem;box-shadow:0 4px 18px rgba(25,39,52,.05)}
.ec-progress-title{font-size:1.05rem;font-weight:730}.ec-progress-stage{color:var(--ec-text);font-weight:650;margin-top:.45rem}.ec-progress-detail{color:var(--ec-muted);font-size:.8rem;margin-top:.15rem}
.stButton>button,.stDownloadButton>button{border-radius:9px;min-height:2.55rem;font-weight:650}
.stButton>button[kind="primary"]{background:var(--ec-brand);border-color:var(--ec-brand)}.stButton>button[kind="primary"]:hover{background:var(--ec-brand-dark);border-color:var(--ec-brand-dark)}
div[data-testid="stFileUploader"]{background:#fff;border:1px dashed #AEBBC5;border-radius:14px;padding:.35rem}
div[data-testid="stFileUploader"] section{background:#FAFBFC}
div[data-testid="stDataFrame"],div[data-testid="stDataEditor"]{border:1px solid var(--ec-line);border-radius:11px;overflow:hidden}
div[data-testid="stMetric"]{background:#fff;border:1px solid var(--ec-line);border-radius:13px;padding:.85rem .95rem}
.stProgress>div>div>div>div{background:var(--ec-brand)}
code{font-family:"Cascadia Mono","Consolas",monospace}
</style>'''

def apply_design() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

# Studio 2.0 Alpha 2 workspace refinements are intentionally appended so that
# deployments upgrading from Alpha 1 keep the same base theme.
