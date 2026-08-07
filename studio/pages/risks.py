from __future__ import annotations

import pandas as pd
import streamlit as st

from core.expert_review_engine import build_expert_risks, summarize_risks
from studio.components import hero, card, section, empty


def _checklist_results() -> list[dict]:
    run=st.session_state.get("checklist_run") or {}; rows=run.get("results") if isinstance(run,dict) else None
    return rows if isinstance(rows,list) else []


def render(ctx)->None:
    docs,findings,comparisons,registry,passports,metrics,eng=ctx.data
    hero("Риски экспертизы","Оценка рисков замечаний на основе межраздельной сверки, чек-листов и базы типовых замечаний проектов-аналогов.","GGE Risk Intelligence · прогноз, а не гарантия позиции эксперта")
    if not st.session_state.get("object_registry_confirmed"):
        st.warning("Сначала подтвердите состав проектируемых объектов. Оценка рисков заблокирована."); return
    risks=build_expert_risks(comparisons.to_dict("records") if not comparisons.empty else [],st.session_state.get("object_assembly_rows") or [],_checklist_results(),documents=docs.to_dict("records") if not docs.empty else [])
    decisions=st.session_state.setdefault("risk_user_decisions",{})
    summary=summarize_risks(risks)
    cols=st.columns(5)
    for col,title,value,tone in zip(cols,["Всего","Высокий","Средний","Низкий","По базе замечаний"],[summary["total"],summary["high"],summary["medium"],summary["low"],summary["matched_knowledge"]],["info","bad" if summary["high"] else "ok","warn" if summary["medium"] else "ok","info","ok"]):
        with col: card(title,value,"",tone)
    tabs=st.tabs(["Критично до подачи","Требует внимания","Контроль специалиста"])
    groups=[{"Высокий"},{"Средний"},{"Низкий","Недостаточно данных"}]
    for tab_index, (tab, levels) in enumerate(zip(tabs, groups)):
        with tab:
            selected=[r for r in risks if r.get("level") in levels]
            if not selected: empty("Риски этой группы не сформированы."); continue
            table=pd.DataFrame([{"ID":r["risk_id"],"Категория":r["category"],"Объект / раздел":r.get("object") or "—","Вопрос":r["parameter"],"Аналоги":", ".join(r.get("analog_projects") or []),"Решение":decisions.get(r["risk_id"],{}).get("status","Не рассмотрено")} for r in selected])
            st.dataframe(table,hide_index=True,width="stretch")
            section("Карточки риска","Каждый вывод содержит источник, аналогичный сценарий и действие до подачи.")
            for risk_index, risk in enumerate(selected[:50]):
                with st.expander(f"{risk['level']} · {risk.get('scenario_title') or risk['category']} · {risk.get('object') or risk['parameter']}"):
                    st.write("**Выявленная проблема**"); st.write(risk["finding"])
                    st.write("**Возможная формулировка замечания**"); st.info(risk["possible_remark"])
                    st.write("**Рекомендация до подачи**"); st.write(risk["recommendation"])
                    if risk.get("scenario_id"):
                        st.write("**Связь с базой замечаний**")
                        st.write(f"Сценарий: {risk['scenario_id']} — {risk.get('scenario_title','')}")
                        st.write(f"Повторяемость в базе: {risk.get('recurrence',0)}; проекты-аналоги: {', '.join(risk.get('analog_projects') or []) or 'не указаны'}")
                    historical=risk.get('historical_remark_analogs') or []
                    if historical:
                        st.write('**Похожие реальные замечания экспертов**')
                        for analog in historical[:3]:
                            st.markdown(f"- {analog.get('remark','')}  ")
                            st.caption(f"Совпадение: {analog.get('similarity_score','—')} · Повторяемость: {analog.get('recurrence',0)} · Разделы: {', '.join(analog.get('sections') or []) or '—'}")
                    if risk.get("sources"): st.write("**Доказательства**"); st.write(risk["sources"])
                    current=decisions.get(risk["risk_id"],{})
                    c1,c2=st.columns([1,2])
                    status=c1.selectbox("Решение",["Не рассмотрено","Принято в работу","Проверено","Не применимо"],index=["Не рассмотрено","Принято в работу","Проверено","Не применимо"].index(current.get("status","Не рассмотрено")),key=f"risk_status_{tab_index}_{risk_index}_{risk.get('risk_id', 'risk')}")
                    comment=c2.text_input("Комментарий",value=current.get("comment",""),key=f"risk_comment_{tab_index}_{risk_index}_{risk.get('risk_id', 'risk')}")
                    decisions[risk["risk_id"]]={"status":status,"comment":comment}
                    st.caption(f"Источник оценки: {risk['origin']} · Risk ID: {risk['risk_id']} · Надёжность доказательств: {risk.get('evidence_strength','—')}")
