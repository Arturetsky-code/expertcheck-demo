from __future__ import annotations
import os, streamlit as st
from core.ai_agent import answer_locally,ask_openai_grounded,build_grounded_snapshot,openai_available,run_local_agents
from studio.components import card,empty,section

def _secret(name):
    try:
        value=st.secrets.get(name);return str(value) if value else None
    except Exception:return None

def render(ctx):
    docs,findings,comparisons,registry,passports=ctx.data[:5]
    section('AI-анализ проекта','Агент анализирует только структурированную цифровую модель и не изменяет результаты Core без решения пользователя.')
    if docs.empty:return empty('Сначала загрузите и проанализируйте проектную документацию.')
    snapshot=build_grounded_snapshot(docs,registry,passports,comparisons,findings,registry_confirmed=st.session_state.get('object_registry_confirmed',False),checklist_runs=st.session_state.get('checklist_user_results',{}))
    report=run_local_agents(snapshot);high=sum(x.severity=='high' for x in report.observations);medium=sum(x.severity=='medium' for x in report.observations);low=sum(x.severity=='low' for x in report.observations)
    c1,c2,c3,c4=st.columns(4)
    with c1:card('Готовность',f'{report.readiness}%','Оценка по структурированной модели','ok' if report.readiness>=85 else 'warn')
    with c2:card('Высокий риск',high,'Требуют первоочередной проверки','bad' if high else 'ok')
    with c3:card('Требует внимания',medium,'Неоднозначные результаты','warn' if medium else 'ok')
    with c4:card('Наблюдений',len(report.observations),f'Низкий риск: {low}','info')
    section('Наблюдения агентов','Каждый вывод содержит основание из цифровой модели проекта.')
    if not report.observations:st.success('Дополнительные предупреждения не сформированы.')
    for item in report.observations[:50]:
        icon={'high':'🔴','medium':'🟠','low':'🔵'}.get(item.severity,'⚪')
        with st.container(border=True):
            st.markdown(f'**{icon} {item.title}**');st.caption(f'{item.agent} · уверенность {item.confidence:.0%} · {item.observation_id}');st.write(item.explanation);st.markdown(f'**Рекомендация:** {item.recommendation}')
            if item.evidence:
                with st.expander('Показать доказательства'):st.json(item.evidence,expanded=False)
    section('Спросить ExpertCheck','Ответ формируется только по цифровой модели текущего проекта.')
    key=_secret('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY');ready=openai_available(key)
    mode=st.radio('Режим ответа',['Локальный анализ','OpenAI API'],horizontal=True,disabled=not ready)
    if not ready:st.info('Для свободного диалога добавьте OPENAI_API_KEY в Streamlit Secrets. Локальный режим работает без внешнего API.');mode='Локальный анализ'
    model=st.text_input('Модель API',value=_secret('OPENAI_MODEL') or os.getenv('OPENAI_MODEL','gpt-5-mini'),disabled=mode!='OpenAI API')
    question=st.text_area('Вопрос',placeholder='Например: какие объекты выглядят сомнительно и почему?')
    if st.button('Проанализировать вопрос',type='primary',disabled=not question.strip(),width='stretch'):
        with st.spinner('Агент анализирует цифровую модель проекта…'):
            try:st.session_state.ai_last_answer=ask_openai_grounded(snapshot,question,api_key=key,model=model.strip() or 'gpt-5-mini') if mode=='OpenAI API' else answer_locally(snapshot,question)
            except Exception as error:st.error(str(error))
    if st.session_state.get('ai_last_answer'):st.markdown('### Ответ агента');st.write(st.session_state.ai_last_answer)
    with st.expander('Ограничения и безопасность'):
        for text in report.limitations:st.write('• '+text)
        st.write('• Во внешний API передаётся компактная структурированная модель, а не исходные PDF-файлы.');st.write('• Запрос отправляется с параметром store=false.')
