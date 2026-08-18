
from __future__ import annotations
import streamlit as st
from studio.components import section, card

def _reset_project_session():
    for k,v in {
        "project_name":"Новый проект","result":None,"analysis_time":None,
        "object_registry_confirmed":False,"object_assembly_rows":[],
        "completeness_user_confirmed":False,"completeness_decisions":{},
        "checklist_run":None,"checklist_user_results":{},"risk_user_decisions":{}
    }.items():
        st.session_state[k]=v

def render(ctx):
    user=st.session_state.get("auth_user") or {}
    store=ctx.workspace_store
    section("Мои проекты",f"Личное рабочее пространство: {user.get('email','')}")
    if not store.persistent_mode:
        st.warning("Сейчас используется локальное хранилище разработки. Для постоянного многопользовательского хранения в Streamlit Cloud подключите PostgreSQL через DATABASE_URL.")
    with st.container(border=True):
        c1,c2=st.columns([4,1])
        with c1:
            name=st.text_input("Новый проект",placeholder="Наименование проекта",key="workspace_new_project_name")
        with c2:
            st.write("")
            if st.button("Создать",type="primary",width="stretch",key="workspace_create_project"):
                pid=store.create_project(user["id"],name.strip() or "Новый проект")
                _reset_project_session()
                st.session_state.active_project_id=pid
                st.session_state.project_name=name.strip() or "Новый проект"
                st.session_state["_navigate_to"]="Проект"
                st.rerun()

    projects=store.list_projects(user["id"])
    if not projects:
        st.info("У вас пока нет проектов. Создайте первый проект выше.")
        return
    for row in projects:
        with st.container(border=True):
            c1,c2,c3=st.columns([6,1.4,1.2])
            with c1:
                st.markdown(f"### {row['name']}")
                when=row.get("last_analysis_at") or row.get("updated_at")
                st.caption(f"Последнее изменение: {when} · Статус: {row.get('status','—')}")
            with c2:
                if st.button("Открыть",key=f"open_project_{row['id']}",width="stretch"):
                    project=store.load_project(user["id"],row["id"])
                    if not project:
                        st.error("Проект недоступен.")
                    else:
                        _reset_project_session()
                        st.session_state.active_project_id=row["id"]
                        payload=project.get("payload") or {}
                        for k,v in payload.items():
                            st.session_state[k]=v
                        st.session_state.project_name=project["name"]
                        st.session_state["_navigate_to"]="Проект"
                        st.rerun()
            with c3:
                confirm_key=f"delete_confirm_{row['id']}"
                if st.session_state.get(confirm_key):
                    if st.button("Удалить",type="primary",key=f"delete_yes_{row['id']}",width="stretch"):
                        store.delete_project(user["id"],row["id"])
                        if st.session_state.get("active_project_id")==row["id"]:
                            st.session_state.active_project_id=None
                            _reset_project_session()
                        st.rerun()
                elif st.button("Удаление",key=f"delete_project_{row['id']}",width="stretch"):
                    st.session_state[confirm_key]=True
                    st.rerun()
