
from __future__ import annotations
import streamlit as st
from studio.components import section, card
from core.project_snapshot import load_project_snapshot, snapshot_to_workspace_payload

def _reset_project_session():
    for k,v in {
        "project_name":"Новый проект","result":None,"analysis_time":None,
        "object_registry_confirmed":False,"object_assembly_rows":[],
        "completeness_user_confirmed":False,"completeness_decisions":{},
        "checklist_run":None,"checklist_user_results":{},"risk_user_decisions":{},
        "semantic_execution_checkpoint":{},
    }.items():
        st.session_state[k]=v

def render(ctx):
    user=st.session_state.get("auth_user") or {}
    store=ctx.workspace_store
    section("Мои проекты",f"Личное рабочее пространство: {user.get('email','')}")
    if not store.persistent_mode:
        st.warning("Сейчас используется локальное хранилище разработки. Для постоянного многопользовательского хранения в Streamlit Cloud подключите PostgreSQL через DATABASE_URL.")
    with st.expander("Восстановить проект из цифрового снимка", expanded=False):
        st.caption(
            "Загрузите ExpertCheck_Цифровой_снимок.json.gz. "
            "Извлечённый корпус страниц и результаты будут восстановлены без повторного чтения исходных PDF."
        )
        restore_file=st.file_uploader(
            "Цифровой снимок ExpertCheck",
            type=["gz"],
            accept_multiple_files=False,
            key="workspace_snapshot_restore_file",
        )
        restore_name=st.text_input(
            "Наименование восстановленного проекта",
            value="Восстановленный проект",
            key="workspace_snapshot_restore_name",
        )
        if st.button(
            "Восстановить проект",
            type="primary",
            width="stretch",
            key="workspace_restore_snapshot",
            disabled=restore_file is None,
        ):
            try:
                snapshot=load_project_snapshot(restore_file.getvalue())
                restored=snapshot_to_workspace_payload(
                    snapshot,
                    project_name=restore_name.strip() or "",
                )
                pid=store.create_project(user["id"],restored["project_name"])
                store.save_project(
                    user["id"],
                    pid,
                    restored["project_name"],
                    restored,
                    status="analyzed",
                    app_version=ctx.version,
                )
            except Exception as exc:
                st.error(f"Не удалось восстановить цифровой снимок: {type(exc).__name__}: {exc}")
            else:
                _reset_project_session()
                st.session_state.active_project_id=pid
                for k,v in restored.items():
                    st.session_state[k]=v
                st.session_state.project_name=restored["project_name"]
                st.session_state["_navigate_to"]="Проект"
                info=restored.get("snapshot_restore_info") or {}
                st.session_state["snapshot_restore_notice"]={
                    "snapshot_id":info.get("snapshot_id"),
                    "ai_checkpoint_restored":bool(info.get("ai_checkpoint_restored")),
                    "source_pdf_required":False,
                }
                st.rerun()

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
