from __future__ import annotations

import json
import streamlit as st

from core.ai_gateway import diagnostic_message, provider_for_role
from core.document_intelligence import build_structured_ai_context
from core.engineering_advisor import answer_local_question, summarize_object_registry
from studio.components import card, section

SYSTEM_PROMPT = '''Вы — инженерный аналитик ExpertCheck. Возвращайте выводы только на основании переданного контекста. Для классификационных задач возвращайте валидный JSON. Анализируйте только переданный структурированный контекст проекта. Не выдумывайте отсутствующие сведения. Каждый вывод связывайте с объектом, характеристикой и источником, если они переданы. При недостатке данных прямо пишите «Недостаточно данных». Не изменяйте подтверждённый реестр и не выдавайте предположение за установленный факт.'''


def _external_prompt(question: str, context: dict) -> str:
    return (
        'Вопрос пользователя:\n' + question.strip() +
        '\n\nСтруктурированный контекст проекта (обезличен):\n' +
        json.dumps(context, ensure_ascii=False, indent=2) +
        '\n\nДайте краткий инженерный ответ. Отдельно укажите: 1) вывод; 2) доказательства; 3) что требует ручной проверки.'
    )


def render(ctx):
    section('Инженерный советник','Локальный анализ работает без внешнего API. Подключаемый внешний AI анализирует только обезличенную структурированную модель, а не полные PDF.')
    rows = st.session_state.get('object_assembly_rows') or []
    comparisons = ctx.data[2].to_dict('records') if hasattr(ctx.data[2], 'to_dict') else []
    summary = summarize_object_registry(rows)
    cols = st.columns(4)
    with cols[0]: card('Кандидатов', summary['total'], 'Все найденные сущности')
    with cols[1]: card('Предложено включить', summary['included'], 'До ручного подтверждения', 'ok')
    with cols[2]: card('Требуют решения', summary['review'], 'Недостаточно доказательств', 'warn')
    with cols[3]: card('Заблокировано', summary['blocked'], 'Служебные источники', 'bad')

    mode = st.radio('Режим анализа', ['Локальный советник', 'Внешний AI'], horizontal=True, key='advisor_mode')
    task = st.selectbox('Задача советника', ['Ответ на вопрос', 'Проверить сомнительные объекты', 'Проверить результаты межраздельной сверки', 'Проанализировать текущий чек-лист'])
    default_question = {
        'Проверить сомнительные объекты': 'Проанализируй только объекты со статусом review или blocked. Для каждого укажи: объект ли это, статус проектирования, основания и рекомендуемое действие.',
        'Проверить результаты межраздельной сверки': 'Найди только недостоверные или противоречивые сверки. Укажи объект, характеристику, источники и что проверить вручную.',
        'Проанализировать текущий чек-лист': 'Проанализируй результаты текущего чек-листа. Покажи пункты без достаточных доказательств и недостающие сведения.',
    }.get(task, '')
    question = st.text_area('Вопрос по загруженной документации', value=default_question, placeholder='Например: какие объекты выглядят сомнительно и почему?')

    if mode == 'Локальный советник':
        if st.button('Проанализировать локально', type='primary', disabled=not question.strip()):
            st.markdown(answer_local_question(question, rows, comparisons))
        st.caption('Локальный советник работает по правилам и цифровой модели ExpertCheck. Внешние сервисы не используются.')
        return

    provider = provider_for_role('reviewer', st.session_state, st.secrets)
    if provider is None:
        st.warning('Внешний AI не настроен. Откройте «Настройки → AI-модули» и выберите OpenRouter, Groq, DeepSeek или автоматический резерв.')
        return
    st.info(f'Провайдер: {provider.name}. Режим передачи: только обезличенные структурированные данные.')
    if st.button('Отправить запрос внешнему AI', type='primary', disabled=not question.strip()):
        checklist_rows = st.session_state.get('checklist_run') or []
        if isinstance(checklist_rows, dict):
            checklist_rows = checklist_rows.get('rows') or checklist_rows.get('results') or []
        context = build_structured_ai_context(rows, comparisons, checklist_rows)
        with st.spinner('Внешний AI анализирует структурированную модель проекта...'):
            result = provider.generate(_external_prompt(question, context), SYSTEM_PROMPT)
        if result.ok:
            st.markdown(result.text)
            st.caption(f'{result.provider} · {result.model}')
        else:
            st.error(diagnostic_message(result))
            if st.session_state.get('expert_mode'):
                st.code(result.error)
