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
except Exception as startup_error:
    st.set_page_config(page_title='ExpertCheck Studio — ошибка запуска',layout='wide')
    st.error('ExpertCheck не смог загрузить обязательные модули.')
    st.code(f'{type(startup_error).__name__}: {startup_error}')
    st.stop()
CONFIG_DIR=BASE_DIR/'config' if (BASE_DIR/'config').exists() else BASE_DIR
VERSION='ExpertCheck 17.0 · Verified Core'
st.set_page_config(page_title='ExpertCheck Studio',page_icon='EC',layout='wide',initial_sidebar_state='expanded')
apply_design()
WORKSPACE_STORE=get_store(st.secrets, base_dir=BASE_DIR/'.expertcheck_data')
if not st.session_state.get('auth_user'):
    auth_screen(WORKSPACE_STORE)
    st.stop()
for k,v in {'project_name':'Новый проект','result':None,'analysis_time':None,'page':'Проект','expert_mode':False,'completeness_profile':'Капитальный объект','completeness_forming':True,'completeness_user_confirmed':False,'completeness_decisions':{},'object_registry_confirmed':False,'object_assembly_rows':[],'checklist_run':None,'checklist_user_results':{},'external_ai_provider':'Отключён','ai_extraction_provider':'Groq','ai_judge_provider':'Groq','ai_critic_provider':'OpenRouter','ai_reviewer_provider':'OpenRouter','ai_assisted_extraction':True,'ai_pipeline_level':'Умный автоматический','ai_object_reviews':{},'ai_checklist_reviews':{},'risk_user_decisions':{},'object_learning_examples':[],'semantic_execution_checkpoint':{},'provider_benchmark_results':{},'active_project_id':None}.items():
    st.session_state.setdefault(k,v)
# One-time migration from the 16.0 defaults.  Explicit non-default choices are
# preserved, while existing sessions receive the deterministic Verified Core
# routing instead of the old OpenRouter-first automatic route.
if not st.session_state.get('_verified_core_ai_migrated'):
    if st.session_state.get('ai_judge_provider') == 'Авто: OpenRouter → Groq':
        st.session_state.ai_judge_provider = 'Groq'
    if st.session_state.get('ai_critic_provider') == 'Groq':
        st.session_state.ai_critic_provider = 'OpenRouter'
    st.session_state.ai_reviewer_provider = st.session_state.ai_critic_provider
    st.session_state._verified_core_ai_migrated = True
# Apply deferred navigation before the sidebar radio widget is instantiated.
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
    sidebar_group('Этапы проверки')
    has_result = bool(st.session_state.result)
    object_gate = bool(st.session_state.get('object_registry_confirmed'))
    if st.session_state.get('expert_mode'):
        guided_pages = ['Мои проекты', 'Проект']
        if has_result:
            guided_pages.extend(['Состав объектов', 'Чек-листы'])
        if object_gate:
            guided_pages.extend(['Межраздельная сверка', 'Риски экспертизы', 'Отчёт'])
        guided_pages.append('Настройки')
    else:
        # Рабочий интерфейс: только пользовательский маршрут.
        guided_pages=['Мои проекты','Проект']
        if has_result:
            guided_pages.extend(['Подтверждение','Проверка','Чек-листы','Результаты','Отчёт'])
        guided_pages.append('Настройки')
    if st.session_state.get('page') not in guided_pages:
        st.session_state.page = ('Проверка' if has_result and not st.session_state.get('expert_mode') else 'Состав объектов') if has_result else 'Мои проекты'
    page=st.radio('Раздел',guided_pages,label_visibility='collapsed',key='page')
    if not has_result:
        st.caption('Следующий этап откроется после загрузки проекта.')
    elif not object_gate:
        st.caption('Результаты до подтверждения состава считаются предварительными.')
    else:
        st.caption('Все основные этапы доступны.')
    user=st.session_state.get('auth_user') or {}
    st.caption(f"Пользователь: {user.get('display_name') or user.get('email','')}")
    if st.button('Выйти', width='stretch', key='sidebar_logout'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    status='Проверка выполнена' if st.session_state.result else 'Комплект не загружен'
    sidebar_project(st.session_state.project_name,status)
    sidebar_group('Режим интерфейса')
    st.session_state.expert_mode=st.toggle(
        'Режим разработчика',
        value=st.session_state.expert_mode,
        help='Включает служебные сведения, причины сопоставления и диагностику Core.',
        key='interface_mode_toggle',
    )
    st.caption('Рабочий режим' if not st.session_state.expert_mode else 'Отображаются технические данные')
    if not st.session_state.expert_mode:
        with st.expander('Дополнительно', expanded=False):
            st.caption('История проектов и расширенные настройки доступны в режиме разработчика.')
    st.caption(VERSION)
header(VERSION)
docs,findings,raw_comparisons=frames(st.session_state.result)
if st.session_state.result and not st.session_state.object_assembly_rows:
    st.session_state.object_assembly_rows=assembly_rows(docs,findings)
raw_passports=passports(docs)
filtered_registry,filtered_passports,comparisons=apply_project_assembly(docs,raw_passports,raw_comparisons,st.session_state.object_assembly_rows,st.session_state.object_registry_confirmed)
data=(docs,findings,comparisons,filtered_registry,filtered_passports,metrics(comparisons),engineer_findings(findings))
@dataclass
class Context:
    data:tuple
    version:str
    config_dir:Path
    analyze:object
    workspace_store:object
    current_user:dict
ctx=Context(data,VERSION,CONFIG_DIR,analyze_uploaded,WORKSPACE_STORE,st.session_state.get('auth_user') or {})
PAGES[page](ctx)

# Persist the current private project after every completed rerun.
# Access is owner-scoped in WorkspaceStore, so a project id from another user cannot be saved.
_active=st.session_state.get('active_project_id')
_user=st.session_state.get('auth_user') or {}
if _active and _user.get('id') and st.session_state.get('result') is not None:
    try:
        _snapshot=session_snapshot(st.session_state)
        _signature=snapshot_signature(_snapshot)
        if st.session_state.get('_workspace_saved_signature') != _signature:
            WORKSPACE_STORE.save_project(
                _user['id'],_active,st.session_state.get('project_name') or 'Проект',
                _snapshot,status='analyzed',app_version=VERSION
            )
            st.session_state['_workspace_saved_signature']=_signature
    except PermissionError:
        st.error('Доступ к выбранному проекту запрещён.')
    except Exception as workspace_error:
        if st.session_state.get('expert_mode'):
            st.warning(f'Не удалось сохранить проект: {type(workspace_error).__name__}: {workspace_error}')
