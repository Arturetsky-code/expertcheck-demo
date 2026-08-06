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
except Exception as startup_error:
    st.set_page_config(page_title='ExpertCheck Studio — ошибка запуска',layout='wide')
    st.error('ExpertCheck не смог загрузить обязательные модули.')
    st.code(f'{type(startup_error).__name__}: {startup_error}')
    st.stop()
CONFIG_DIR=BASE_DIR/'config' if (BASE_DIR/'config').exists() else BASE_DIR
VERSION='ExpertCheck 5.0 Alpha 1 · Cognitive Document Intelligence'
st.set_page_config(page_title='ExpertCheck Studio',page_icon='EC',layout='wide',initial_sidebar_state='expanded')
apply_design()
for k,v in {'project_name':'Новый проект','result':None,'analysis_time':None,'page':'Проект','expert_mode':False,'completeness_profile':'Капитальный объект','completeness_forming':True,'completeness_user_confirmed':False,'completeness_decisions':{},'object_registry_confirmed':False,'object_assembly_rows':[],'checklist_run':None,'checklist_user_results':{},'external_ai_provider':'Отключён','ai_assisted_extraction':False,'ai_object_reviews':{},'ai_checklist_reviews':{}}.items():
    st.session_state.setdefault(k,v)
with st.sidebar:
    sidebar_brand()
    if st.button('＋ Начать новую проверку', type='primary', width='stretch', key='sidebar_new_check'):
        st.session_state.result=None
        st.session_state.analysis_time=None
        st.session_state.project_name='Новый проект'
        st.session_state.object_registry_confirmed=False
        st.session_state.object_assembly_rows=[]
        st.session_state.checklist_run=None
        st.session_state.checklist_user_results={}
        st.session_state.page='Проект'
        st.rerun()
    sidebar_group('Рабочее пространство')
    page=st.radio('Раздел',list(PAGES),label_visibility='collapsed',key='page')
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
PAGES[page](Context(data,VERSION,CONFIG_DIR,analyze_uploaded))
