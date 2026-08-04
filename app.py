from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path
import streamlit as st
BASE_DIR=Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:sys.path.insert(0,str(BASE_DIR))
from analyzer import analyze_uploaded
from studio.design import apply_design
from studio.components import header
from studio.data import frames,registry,passports,metrics,engineer_findings
from studio.pages import PAGES
CONFIG_DIR=BASE_DIR/'config' if (BASE_DIR/'config').exists() else BASE_DIR
VERSION='Studio 1.0 Alpha 2 · Core 3.0 Alpha 4'
st.set_page_config(page_title='ExpertCheck Studio',page_icon='◩',layout='wide',initial_sidebar_state='expanded');apply_design()
for k,v in {'project_name':'Новый проект','result':None,'analysis_time':None,'page':'Обзор','expert_mode':False}.items():st.session_state.setdefault(k,v)
with st.sidebar:
    st.markdown('### ◩ ExpertCheck');st.caption('Инженерная проверка проекта');st.divider();page=st.radio('Раздел',list(PAGES),label_visibility='collapsed',key='page');st.divider();st.session_state.expert_mode=st.toggle('Аналитический режим',value=st.session_state.expert_mode);st.markdown('**Текущий проект**');st.caption(st.session_state.project_name);st.success('Проверка выполнена') if st.session_state.result else st.info('Комплект не загружен');st.caption(VERSION)
header(VERSION)
docs,findings,comparisons=frames(st.session_state.result)
data=(docs,findings,comparisons,registry(docs),passports(docs),metrics(comparisons),engineer_findings(findings))
@dataclass
class Context:
    data:tuple;version:str;config_dir:Path;analyze:object
PAGES[page](Context(data,VERSION,CONFIG_DIR,analyze_uploaded))
