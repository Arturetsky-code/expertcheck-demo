from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path
import streamlit as st
BASE_DIR=Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
try:
    from analyzer import analyze_uploaded
    from studio.design import apply_design
    from studio.components import header,sidebar_brand,sidebar_group,sidebar_project
    from studio.data import frames,registry,passports,metrics,engineer_findings,assembly_rows,apply_project_assembly
    from studio.pages import PAGES
    from studio.auth import auth_screen
    from core.workspace_store import get_store, session_snapshot, snapshot_signature
    from core20.dual_run import build_dual_run_manifest
    from core.free_ai_patch import install as install_free_ai_patch
    from core.gemini_runtime_preference import install as install_gemini_runtime_preference
    from core.quality_gates_patch import install as install_quality_gates
    from core.gemini_model_tracking_patch import install as install_gemini_model_tracking
except Exception as startup_error:
    st.set_page_config(page_title='ExpertCheck Studio — ошибка запуска',layout='wide')
    st.error('ExpertCheck не смог загрузить обязательные модули.')
    st.code(f'{type(startup_error).__name__}: {startup_error}')
    st.stop()
install_free_ai_patch()
install_gemini_runtime_preference()
install_quality_gates()
install_gemini_model_tracking()
CONFIG_DIR=BASE_DIR/'config' if (BASE_DIR/'config').exists() else BASE_DIR
VERSION='ExpertCheck 20.0 Alpha 10.1.3 · Proof Trace Consistency · Dual Run'
st.set_page_config(page_title='ExpertCheck Studio',page_icon='EC',layout='wide',initial_sidebar_state='expanded')
apply_design()
WORKSPACE_STORE=get_store(st.secrets, base_dir=BASE_DIR/'.expertcheck_data')
if not st.session_state.get('auth_user'):
    auth_screen(WORKSPACE_STORE)
    st.stop()
for k,v in {'project_name':'Новый проект','result':None,'analysis_time':None,'page':'Проект','expert_mode':False,'completeness_profile':'Капитальный объект','completeness_forming':True,'completeness_user_confirmed':False,'completeness_decisions':{},'object_registry_confirmed':False,'object_assembly_rows':[],'checklist_run':None,'checklist_user_results':{},'external_ai_provider':'Отключён','ai_extraction_provider':'Groq','ai_judge_provider':'Groq','ai_critic_provider':'Gemini','ai_reviewer_provider':'Gemini','ai_assisted_extraction':True,'ai_pipeline_level':'Умный автоматический','ai_object_reviews':{},'ai_checklist_reviews':{},'risk_user_decisions':{},'object_learning_examples':[],'semantic_execution_checkpoint':{},'provider_benchmark_results':{},'provider_benchmark_runs':{},'active_project_id':None}.items():
    st.session_state.setdefault(k,v)
if not st.session_state.get('_verified_core_ai_migrated'):
    if st.session_state.get('ai_judge_provider') == 'Авто: OpenRouter → Groq':
        st.session_state.ai_judge_provider = 'Groq'
    if st.session_state.get('ai_critic_provider') == 'Groq':
        st.session_state.ai_critic_provider = 'OpenRouter'
    st.session_state.ai_reviewer_provider = st.session_state.ai_critic_provider
    st.session_state._verified_core_ai_migrated = True
if not st.session_state.get('_resilient_free_ai_181_migrated'):
    if st.session_state.get('ai_critic_provider') == 'OpenRouter':
        st.session_state.ai_critic_provider = 'Gemini'
    if st.session_state.get('ai_reviewer_provider') == 'OpenRouter':
        st.session_state.ai_reviewer_provider = 'Gemini'
    if st.session_state.get('external_ai_provider') == 'OpenRouter':
        st.session_state.external_ai_provider = 'Отключён'
    st.session_state._resilient_free_ai_181_migrated = True
if not st.session_state.get('_quality_gates_183_migrated'):
    st.session_state.provider_benchmark_results = {}
    st.session_state.provider_benchmark_runs = {}
    st.session_state.semantic_execution_checkpoint = {}
    st.session_state._quality_gates_183_migrated = True
if not st.session_state.get('_verification_runtime_184_migrated'):
    # 18.4 changes queue semantics and Critic participation. Reuse of an old
    # partial 18.3 semantic checkpoint would make the control run incomparable.
    st.session_state.semantic_execution_checkpoint = {}
    st.session_state._verification_runtime_184_migrated = True
_pending_page = st.session_state.pop('_navigate_to', None)
if _pending_page:
    st.session_state['page'] = _pending_page
with st.sidebar:
    sidebar_brand()
    if st.button('＋ Новый проект', type='primary', width='stretch', key='sidebar_new_check'):
        user=st.session_state.get('auth_user') or {}
        pid=WORKSPACE_STORE.create_project(user.get('id'),'Новый проект')
        st.session_state.active_project_id=pid
        st.session_state.result=None
        st.session_state.analysis_time=None
        st.session_state.project_name='Новый проект'
        st.session_state.object_registry_confirmed=False
        st.session_state.object_assembly_rows=[]
        st.session_state.checklist_run=None
        st.session_state.checklist_user_results={}
        st.session_state.risk_user_decisions={}
        st.session_state.ai_checklist_batch_reviews={}
        st.session_state.semantic_execution_checkpoint={}
        st.session_state.page='Проект'
        st.rerun()
    # Streamlit updates widget-state before the script reruns. Synchronise the
    # developer-mode mirror before building the navigation, otherwise the
    # sidebar can show the old page set for one rerun after the toggle.
    if 'interface_mode_toggle' in st.session_state:
        st.session_state.expert_mode=bool(st.session_state.get('interface_mode_toggle'))
    sidebar_group('Этапы проверки')
    has_result = bool(st.session_state.result)
    object_gate = bool(st.session_state.get('object_registry_confirmed'))
    if st.session_state.get('expert_mode'):
        guided_pages = ['Мои проекты', 'Проект']
        if has_result:
            guided_pages.extend(['Состав объектов', 'Чек-листы', 'НТД и практика'])
        if object_gate:
            guided_pages.extend(['Межраздельная сверка', 'Риски экспертизы', 'Отчёт'])
        guided_pages.append('Настройки')
    else:
        guided_pages = ['Мои проекты', 'Проект']
        if has_result:
            guided_pages.extend(['Состав объектов', 'Чек-листы', 'НТД и практика'])
        if object_gate:
            guided_pages.extend(['Межраздельная сверка', 'Риски экспертизы', 'Отчёт'])
        guided_pages.append('Настройки')
    for name in guided_pages:
        active=st.session_state.get('page')==name
        if st.button(('● ' if active else '○ ')+name,key=f'nav_{name}',width='stretch'):
            st.session_state.page=name;st.rerun()
    st.caption('Все основные этапы доступны.')
    user=st.session_state.get('auth_user') or {}
    st.caption(f"Пользователь: {user.get('name') or user.get('username') or '—'}")
    if st.button('Выйти',width='stretch'):
        st.session_state.clear();st.rerun()
    if st.session_state.get('result'):
        sidebar_project(st.session_state.project_name,'Проект открыт')
        st.info('Следующий шаг: на странице «Проект» завершить AI-очередь, если она ещё не закрыта; затем разобрать подтверждённые замечания и инженерные вопросы.')
    sidebar_group('Режим интерфейса')
    st.toggle('Режим разработчика',value=bool(st.session_state.get('expert_mode')),key='interface_mode_toggle',help='Отображаются технические данные')
    st.caption(VERSION)

@dataclass
class StudioContext:
    data:tuple
    version:str


def _autosave_current_project():
    pid=st.session_state.get('active_project_id')
    user=st.session_state.get('auth_user') or {}
    if not pid or not user:return
    try:
        snapshot=session_snapshot(st.session_state)
        sig=snapshot_signature(snapshot)
        if sig != st.session_state.get('_workspace_saved_signature'):
            WORKSPACE_STORE.save_project(pid,user.get('id'),snapshot)
            st.session_state._workspace_saved_signature=sig
    except Exception as exc:
        if st.session_state.get('expert_mode'):
            st.sidebar.caption(f'Автосохранение: {type(exc).__name__}')

if st.session_state.result:
    d,f,c=frames(st.session_state.result)
    raw_passports=passports(d)
    raw_registry=registry(d)
    rows=st.session_state.get('object_assembly_rows') or []
    if not rows:
        rows=assembly_rows(d,f)
        st.session_state.object_assembly_rows=rows
    raw_comparisons=c
    reg,pas,cmp=apply_project_assembly(d,raw_passports,raw_comparisons,rows,st.session_state.get('object_registry_confirmed'))
    # Always build the canonical 20.0 shadow manifest. The legacy UI remains the
    # executable baseline, while the shadow manifest lets us measure parity and
    # migrate one engineering contract at a time without a big-bang rewrite.
    try:
        manifest=build_dual_run_manifest(
            d.to_dict('records') if hasattr(d,'to_dict') else [],
            f.to_dict('records') if hasattr(f,'to_dict') else [],
            cmp.to_dict('records') if hasattr(cmp,'to_dict') else [],
        )
        st.session_state.canonical_core_20_manifest=manifest
    except Exception as exc:
        st.session_state.canonical_core_20_manifest={}
        if st.session_state.get('expert_mode'):
            st.sidebar.caption(f'Core20 shadow: {type(exc).__name__}')
    ctx=StudioContext(data=(d,f,c,reg,pas,cmp,engineer_findings(f)),version=VERSION)
    page=st.session_state.get('page','Проект')
    renderer=PAGES.get(page,PAGES['Проект'])
    renderer(ctx)
    _autosave_current_project()
else:
    st.session_state.canonical_core_20_manifest={}
    ctx=StudioContext(data=(None,None,None,None,None,None,None),version=VERSION)
    page=st.session_state.get('page','Проект')
    renderer=PAGES.get(page,PAGES['Проект'])
    renderer(ctx)
    _autosave_current_project()
