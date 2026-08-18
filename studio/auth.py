
from __future__ import annotations
import streamlit as st
from core.workspace_store import WorkspaceStore

def auth_screen(store: WorkspaceStore):
    st.markdown("## ExpertCheck")
    st.caption("Защищённое рабочее пространство проверки проектной документации")
    tab_login,tab_register=st.tabs(["Войти","Регистрация"])
    with tab_login:
        with st.form("auth_login"):
            email=st.text_input("Email",key="auth_login_email")
            password=st.text_input("Пароль",type="password",key="auth_login_password")
            submit=st.form_submit_button("Войти",type="primary",use_container_width=True)
        if submit:
            ok,msg,user=store.authenticate(email,password)
            if ok and user:
                st.session_state.auth_user={"id":user.id,"email":user.email,"display_name":user.display_name}
                st.session_state.page="Мои проекты"
                st.rerun()
            st.error(msg)
    with tab_register:
        with st.form("auth_register"):
            name=st.text_input("Имя",key="auth_reg_name")
            email=st.text_input("Email",key="auth_reg_email")
            p1=st.text_input("Пароль",type="password",key="auth_reg_password")
            p2=st.text_input("Повторите пароль",type="password",key="auth_reg_password2")
            submit=st.form_submit_button("Создать аккаунт",type="primary",use_container_width=True)
        if submit:
            if p1!=p2:
                st.error("Пароли не совпадают.")
            else:
                ok,msg,user=store.register(email,p1,name)
                if ok and user:
                    st.session_state.auth_user={"id":user.id,"email":user.email,"display_name":user.display_name}
                    st.session_state.page="Мои проекты"
                    st.success(msg)
                    st.rerun()
                st.error(msg)
