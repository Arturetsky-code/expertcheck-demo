from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path
import streamlit as st
BASE_DIR=Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:sys.path.insert(0,str(BASE_DIR))
from analyzer import analyze_uploaded
from studio.design import apply_design
from studio.components import header,sidebar_brand,sidebar_group,sidebar_project
from studio.data import frames,registry,passports,metrics,engineer_findings
from studio.pages import PAGES
CONFIG_DIR=BASE_DIR/'config' if (BASE_DIR/'config').exists() else BASE_DIR
VERSION='Studio 2.0 Alpha 3 · Core 3.0 Alpha 4'
st.set_page_config(page_title='ExpertCheck Studio',page_icon='EC',layout='wide',initial_sidebar_state='expanded');apply_design()
for k,v in {'project_name':'Новый проект','result':None,'analysis_time':None,'page':'Обзор','expert_mode':False,'completeness_profile':'Капитальный объект','completeness_forming':True,'completeness_user_confirmed':False,'completeness_decisions':{}}.items():st.session_state.setdefault(k,v)
with st.sidebar:
    sidebar_brand()
    sidebar_group('Проект')
    page=st.radio('Раздел',list(PAGES),label_visibility='collapsed',key='page')
    sidebar_group('Режим работы')
    st.session_state.expert_mode=st.toggle('Аналитический режим',value=st.session_state.expert_mode,help='Показывает служебные сведения извлечения и диагностики Core.')
    status='Проверка выполнена' if st.session_state.result else 'Комплект не загружен'
    sidebar_project(st.session_state.project_name,status)
    st.caption(VERSION)
header(VERSION)
docs,findings,comparisons=frames(st.session_state.result)
data=(docs,findings,comparisons,registry(docs),passports(docs),metrics(comparisons),engineer_findings(findings))
@dataclass
class Context:
    data:tuple;version:str;config_dir:Path;analyze:object
PAGES[page](Context(data,VERSION,CONFIG_DIR,analyze_uploaded))
