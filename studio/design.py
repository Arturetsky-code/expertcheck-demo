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
.stApp{
 background:
   linear-gradient(rgba(47,111,237,.018) 1px,transparent 1px),
   linear-gradient(90deg,rgba(47,111,237,.018) 1px,transparent 1px),
   var(--ec-bg);
 background-size:32px 32px,32px 32px,auto;
 color:var(--ec-text);
}
.stApp::before{
 content:"";
 position:fixed;
 pointer-events:none;
 z-index:0;
 right:1.2rem;
 top:5.5rem;
 width:250px;
 height:170px;
 opacity:.045;
 background:
   linear-gradient(90deg,transparent 49.6%,#2F6FED 49.6%,#2F6FED 50.4%,transparent 50.4%),
   linear-gradient(transparent 49.6%,#2F6FED 49.6%,#2F6FED 50.4%,transparent 50.4%),
   radial-gradient(circle at 50% 50%,transparent 0 28px,#2F6FED 29px 30px,transparent 31px),
   linear-gradient(135deg,transparent 48.8%,#2F6FED 49%,#2F6FED 50%,transparent 50.2%);
 border:1px solid #2F6FED;
 border-left-width:2px;
}
.stApp::after{
 content:"A     1        2        3";
 position:fixed;
 pointer-events:none;
 z-index:0;
 right:2rem;
 bottom:1.6rem;
 width:330px;
 padding-top:8px;
 border-top:1px solid rgba(47,111,237,.16);
 color:rgba(47,111,237,.12);
 font:600 11px/1 "Cascadia Mono","Consolas",monospace;
 letter-spacing:10px;
}
.block-container,[data-testid="stSidebar"]{position:relative;z-index:1}
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
[data-testid="stSidebar"] button{background:#233442;border-color:#3B4D5C;color:#fff}
[data-testid="stSidebar"] .stAlert{background:#21323F;border-color:#344858}
[data-testid="stSidebar"] .stAlert p{color:#DDE7ED!important}

.ec-sidebar-brand{padding:.3rem .3rem .75rem}.ec-sidebar-logo{display:flex;align-items:center;gap:.7rem}
.ec-sidebar-mark{width:36px;height:36px;border-radius:9px;background:var(--ec-brand);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;letter-spacing:.02em}
.ec-sidebar-name{font-weight:750;font-size:1rem;color:#fff}.ec-sidebar-caption{font-size:.75rem;color:#9FB0BD;margin-top:.1rem}
.ec-sidebar-group{font-size:.68rem;color:#8496A4!important;text-transform:uppercase;letter-spacing:.09em;font-weight:700;margin:.6rem .25rem .25rem}
.ec-sidebar-project{border-top:1px solid #33424E;margin-top:.8rem;padding-top:.8rem}.ec-sidebar-project strong{display:block;font-size:.83rem;color:#fff}.ec-sidebar-status{margin-top:.45rem}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-size:.82rem!important;font-weight:650!important;color:#EAF0F4!important}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.72rem!important;color:#9FB0BD!important;margin-top:-.15rem}

.ec-topbar{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-bottom:1rem}
.ec-title{font-size:1.35rem;font-weight:760}.ec-sub{color:var(--ec-muted);font-size:.84rem;margin-top:.08rem}
.ec-version{color:#365A8B;background:#EAF1FC;border:1px solid #D4E1F7;border-radius:999px;padding:.32rem .65rem;font-size:.73rem;font-weight:650}
.ec-hero{background:var(--ec-surface);border:1px solid var(--ec-line);border-radius:16px;padding:1.25rem 1.4rem;margin-bottom:1rem;box-shadow:0 4px 18px rgba(25,39,52,.05)}
.ec-hero h2{margin:0;color:var(--ec-text);font-size:1.42rem}.ec-hero p{margin:.38rem 0 0;color:var(--ec-muted)}
.ec-pill{display:inline-flex;background:#EEF4FE;color:#315F9F;border:1px solid #D8E5F9;border-radius:999px;padding:.3rem .62rem;font-size:.75rem;margin-top:.75rem;font-weight:600}
.ec-card{background:var(--ec-surface);border:1px solid var(--ec-line);border-radius:14px;padding:1rem 1.05rem;box-shadow:0 2px 12px rgba(20,42,56,.035);height:100%}
.ec-card-label{color:var(--ec-muted);font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em}.ec-card-value{font-size:1.65rem;line-height:1.15;font-weight:760;margin-top:.38rem}.ec-card-status{margin-top:.52rem;min-height:29px;display:flex;align-items:center}.ec-card-note{color:var(--ec-muted);font-size:.78rem;line-height:1.35;margin-top:.45rem}
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

.ec-project-bar{display:flex;justify-content:space-between;align-items:center;gap:1rem;background:#fff;border:1px solid var(--ec-line);border-radius:16px;padding:1rem 1.2rem;margin-bottom:1rem;box-shadow:0 3px 14px rgba(25,39,52,.04)}
.ec-project-name{font-size:1.2rem;font-weight:780}.ec-project-state{font-size:.8rem;color:var(--ec-muted);margin-top:.12rem}
.ec-status-chips{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:.45rem}
.ec-status-badge{display:inline-flex;align-items:center;min-height:26px;border-radius:999px;padding:.28rem .62rem;font-size:13px;line-height:1;font-weight:650;white-space:nowrap;border:1px solid transparent}
.ec-status-ok{color:#176B45;background:#E8F5EF;border-color:#BFE4D2}.ec-status-warn{color:#8A5C08;background:#FFF5D9;border-color:#F0D995}.ec-status-alert{color:#A84D14;background:#FFF0E6;border-color:#F3C5A7}.ec-status-bad{color:#A52C2C;background:#FDECEC;border-color:#F2BDBD}.ec-status-info{color:#245AC4;background:#EAF1FC;border-color:#C8DAF5}.ec-status-neutral{color:#526170;background:#F1F4F6;border-color:#D8E0E6}
.ec-timeline{background:#fff;border:1px solid var(--ec-line);border-radius:14px;padding:.45rem 1rem}.ec-timeline-row{display:flex;gap:.75rem;align-items:flex-start;padding:.72rem 0;border-bottom:1px solid #EDF1F4}.ec-timeline-row:last-child{border-bottom:0}.ec-timeline-dot{width:9px;height:9px;border-radius:50%;background:var(--ec-brand);margin-top:.32rem;box-shadow:0 0 0 4px #EAF1FC}.ec-timeline-row strong{display:block;font-size:.86rem}.ec-timeline-row span{display:block;color:var(--ec-muted);font-size:.74rem;margin-top:.08rem}
[data-testid="stTabs"] button{font-weight:650}.stTabs [data-baseweb="tab-list"]{gap:.35rem}.stTabs [data-baseweb="tab"]{background:#fff;border:1px solid var(--ec-line);border-radius:9px;padding:.45rem .85rem}.stTabs [aria-selected="true"]{background:#EAF1FC!important;color:#245AC4!important}
</style>'''

def apply_design() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

# Studio 2.0 Alpha 2 workspace refinements are intentionally appended so that
# deployments upgrading from Alpha 1 keep the same base theme.
