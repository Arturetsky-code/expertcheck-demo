from __future__ import annotations

import streamlit as st

from studio.components import hero, section, status_badge


def _reset_project() -> None:
    st.session_state.result = None
    st.session_state.analysis_time = None
    st.session_state.project_name = 'Новый проект'
    st.session_state.completeness_user_confirmed = False
    st.session_state.completeness_decisions = {}
    st.session_state.page = 'Проект'


def render(ctx) -> None:
    hero(
        'Настройки',
        'Параметры проекта, интерфейса, отчётов и инженерного ядра.',
        'Studio 3.0',
    )

    tabs = st.tabs([
        'Общие',
        'Проект',
        'Интерфейс',
        'Отчёты',
        'Knowledge Engine',
        'AI-модули',
        'Core',
    ])

    with tabs[0]:
        section('Общие настройки', 'Основные параметры рабочего пространства.')
        st.text_input('Название рабочего пространства', value=st.session_state.project_name, key='settings_project_name')
        if st.button('Сохранить название', width='content'):
            st.session_state.project_name = st.session_state.settings_project_name.strip() or 'Новый проект'
            st.success('Название проекта сохранено.')

    with tabs[1]:
        section('Управление проектом', 'Команды, влияющие на текущую проверку.')
        if st.session_state.result:
            st.markdown(status_badge('Проверка выполнена'), unsafe_allow_html=True)
            st.write('Новая проверка очистит результаты текущего анализа в этой сессии. Загруженные файлы потребуется выбрать заново.')
            confirm = st.checkbox('Подтверждаю запуск новой проверки', key='confirm_new_analysis')
            if st.button('Начать новую проверку', type='primary', disabled=not confirm, width='content'):
                _reset_project()
                st.rerun()
        else:
            st.markdown(status_badge('Комплект не загружен'), unsafe_allow_html=True)
            st.info('Текущая сессия уже готова к новой проверке.')

        st.divider()
        st.selectbox(
            'Профиль объекта для проверки комплектности',
            ['Капитальный объект', 'Линейный объект'],
            index=0 if st.session_state.completeness_profile == 'Капитальный объект' else 1,
            key='settings_completeness_profile',
        )
        if st.button('Применить профиль', width='content'):
            st.session_state.completeness_profile = st.session_state.settings_completeness_profile
            st.success('Профиль проекта обновлён.')

    with tabs[2]:
        section('Интерфейс', 'Режим интерфейса переключается в нижней части бокового меню.')
        mode = 'Режим разработчика' if st.session_state.expert_mode else 'Рабочий режим'
        st.markdown(status_badge(mode, 'info' if st.session_state.expert_mode else 'ok'), unsafe_allow_html=True)
        st.caption('Рабочий режим показывает основные результаты. Режим разработчика добавляет диагностику, причины сопоставления и технические поля.')
        st.info('Настройки темы, масштаба и языка будут добавлены после стабилизации основных рабочих пространств.')

    with tabs[3]:
        section('Отчёты', 'Настройки состава и форматов выгрузки.')
        st.checkbox('Включать сводку проекта', value=True, disabled=True)
        st.checkbox('Включать перечень замечаний', value=True, disabled=True)
        st.checkbox('Включать полный реестр объектов', value=True, disabled=True)
        st.caption('Расширенные шаблоны отчётов будут подключены в Sprint S4 — Report Workspace.')

    with tabs[4]:
        section('Knowledge Engine', 'Подключаемые библиотеки профилей объектов и характеристик.')
        st.markdown(status_badge('Knowledge Engine активен', 'ok'), unsafe_allow_html=True)
        st.caption('Редактирование отраслевых пакетов будет доступно в отдельном административном интерфейсе.')

    with tabs[5]:
        section('AI-модули', 'Подключение внешних аналитических сервисов. Полные PDF по умолчанию не передаются.')
        provider = st.selectbox(
            'Внешний провайдер',
            ['Отключён', 'OpenRouter', 'Groq', 'Авто: OpenRouter → Groq', 'Авто: Groq → OpenRouter', 'Gemini'],
            index=['Отключён', 'OpenRouter', 'Groq', 'Авто: OpenRouter → Groq', 'Авто: Groq → OpenRouter', 'Gemini'].index(st.session_state.get('external_ai_provider', 'Отключён')),
            key='settings_external_ai_provider',
        )
        st.radio(
            'Режим передачи данных',
            ['Только обезличенные структурированные данные'],
            disabled=True,
            key='settings_ai_transfer_mode',
        )
        st.caption('Ключи сохраняются в Streamlit Secrets, а не в GitHub. Для OpenRouter: OPENROUTER_API_KEY и OPENROUTER_MODEL. Для Groq: GROQ_API_KEY и GROQ_MODEL. Режим «Авто» переключается на резервного провайдера при временной недоступности или исчерпании лимита.')
        if st.button('Сохранить AI-настройки', width='content'):
            st.session_state.external_ai_provider = provider
            st.success('Настройки AI сохранены для текущей сессии.')
        if provider != 'Отключён':
            from core.ai_gateway import diagnostic_message, provider_from_settings
            ai_provider = provider_from_settings(provider, st.secrets)
            if st.button('Проверить подключение', width='content'):
                with st.spinner('Проверка подключения...'):
                    result = ai_provider.test_connection() if ai_provider else None
                if result and result.ok:
                    st.success(diagnostic_message(result))
                elif result:
                    st.error(diagnostic_message(result))
                    if st.session_state.expert_mode:
                        st.code(result.error)
        st.info('Рекомендуемый режим: «Авто: Groq → OpenRouter» для быстрых ответов с резервом на бесплатные модели OpenRouter.')
        st.warning('Не передавайте конфиденциальные документы в бесплатные внешние сервисы без согласования с владельцем информации.')

    with tabs[6]:
        section('Core', 'Служебные параметры инженерного ядра.')
        if st.session_state.expert_mode:
            st.code(ctx.version)
            st.write(f'Каталог конфигурации: {ctx.config_dir}')
            st.caption('Диагностические параметры доступны только в режиме разработчика.')
        else:
            st.info('Включите режим разработчика в боковом меню, чтобы увидеть технические сведения Core.')
