from __future__ import annotations

import streamlit as st

from studio.components import hero, section, status_badge


def _reset_project() -> None:
    st.session_state.result = None
    st.session_state.analysis_time = None
    st.session_state.project_name = 'Новый проект'
    st.session_state.completeness_user_confirmed = False
    st.session_state.completeness_decisions = {}
    st.session_state['_navigate_to'] = 'Проект'


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
        section('Knowledge Engine', 'Профили объектов, нормативная база, кейсы замечаний и проверенные решения пользователя.')
        st.markdown(status_badge('Knowledge Engine активен', 'ok'), unsafe_allow_html=True)
        from core.learning_engine import build_learning_pack, learning_pack_bytes, parse_learning_pack, merge_examples
        examples=st.session_state.get('object_learning_examples',[])
        c1,c2=st.columns(2)
        with c1: st.metric('Проверенных решений по объектам',len(examples))
        with c2: st.metric('Решений по рискам',len(st.session_state.get('risk_user_decisions',{})))
        pack=build_learning_pack(examples,st.session_state.get('risk_user_decisions',{}))
        st.download_button('Скачать learning pack',data=learning_pack_bytes(pack),file_name='expertcheck_learning_pack.json',mime='application/json',width='content')
        uploaded=st.file_uploader('Подключить ранее сохранённый learning pack',type=['json'],key='learning_pack_upload')
        if uploaded and st.button('Импортировать learning pack',width='content'):
            try:
                incoming=parse_learning_pack(uploaded.getvalue())
                st.session_state.object_learning_examples=merge_examples(examples,incoming.get('object_examples') or [])
                st.session_state.risk_user_decisions.update(incoming.get('risk_decisions') or {})
                st.success('Learning pack подключён к текущей сессии.')
            except Exception as exc:
                st.error(f'Не удалось импортировать learning pack: {exc}')
        st.caption('Обучение консервативное: решения пользователя сохраняются как примеры и не превращаются автоматически в глобальное правило после одного случая.')

    with tabs[5]:
        section('AI-модули', 'Подключение внешних аналитических сервисов. Полные PDF по умолчанию не передаются.')
        provider_options = [
            'Отключён', 'OpenRouter', 'Groq', 'DeepSeek',
            'Авто: OpenRouter → Groq', 'Авто: Groq → OpenRouter',
            'Авто: DeepSeek → OpenRouter → Groq', 'Авто: OpenRouter → Groq → DeepSeek',
            'Gemini',
        ]
        provider = st.selectbox(
            'Провайдер для свободного AI-диалога',
            provider_options,
            index=provider_options.index(st.session_state.get('external_ai_provider', 'Отключён')) if st.session_state.get('external_ai_provider', 'Отключён') in provider_options else 0,
            key='settings_external_ai_provider',
        )
        c_extract, c_judge, c_critic = st.columns(3)
        with c_extract:
            extraction_provider = st.selectbox(
                'AI Extraction — извлечение фактов',
                provider_options[1:-1],
                index=provider_options[1:-1].index(st.session_state.get('ai_extraction_provider', 'Groq')) if st.session_state.get('ai_extraction_provider', 'Groq') in provider_options[1:-1] else 0,
                key='settings_ai_extraction_provider',
                help='Быстро извлекает объекты, показатели и спорные смысловые кандидаты. Рекомендуется Groq.',
            )
        with c_judge:
            judge_provider = st.selectbox(
                'AI Judge — оценка доказательства',
                provider_options[1:-1],
                index=provider_options[1:-1].index(st.session_state.get('ai_judge_provider', 'Авто: OpenRouter → Groq')) if st.session_state.get('ai_judge_provider', 'Авто: OpenRouter → Groq') in provider_options[1:-1] else 0,
                key='settings_ai_judge_provider',
                help='Сопоставляет одно атомарное требование с небольшим адресным evidence packet.',
            )
        with c_critic:
            critic_provider = st.selectbox(
                'AI Critic — независимая проверка',
                provider_options[1:-1],
                index=provider_options[1:-1].index(st.session_state.get('ai_critic_provider', 'Groq')) if st.session_state.get('ai_critic_provider', 'Groq') in provider_options[1:-1] else 1,
                key='settings_ai_critic_provider',
                help='Ищет подмену объекта, показателя, единицы, модальности и квалификаторов. Должен фактически отличаться от Judge.',
            )
        reviewer_provider = critic_provider
        st.radio(
            'Режим передачи данных',
            ['Только ограниченные evidence packets; полные PDF не передаются'],
            disabled=True,
            key='settings_ai_transfer_mode',
        )
        ai_level = st.selectbox(
            'Уровень участия AI в проверке',
            ['Отключён', 'Умный автоматический', 'Помощник', 'Расширенный', 'Максимальный'],
            index=['Отключён', 'Умный автоматический', 'Помощник', 'Расширенный', 'Максимальный'].index(st.session_state.get('ai_pipeline_level', 'Умный автоматический')) if st.session_state.get('ai_pipeline_level', 'Умный автоматический') in ['Отключён', 'Умный автоматический', 'Помощник', 'Расширенный', 'Максимальный'] else 1,
            help='Умный автоматический — AI вызывается только для результатов со средней/низкой уверенностью; Помощник — только неоднозначные объекты; Расширенный — дополнительно проверка привязки ТЭП и смысловых пунктов чек-листов; Максимальный — также расширенные рекомендации к результатам.',
            key='settings_ai_pipeline_level',
        )
        assisted = st.checkbox(
            'Использовать внешний AI для неоднозначных объектов и пунктов чек-листов',
            value=bool(st.session_state.get('ai_assisted_extraction', True)),
            help='AI анализирует только ограниченные адресные фрагменты: имена файлов заменяются псевдонимами, контакты и служебные шифры маскируются. В режиме «Расширенный» он автоматически проверяет неоднозначные объекты, привязку ТЭП и смысловые пункты чек-листов. Окончательный реестр подтверждает пользователь.',
            key='settings_ai_assisted_extraction',
        )
        st.caption('Во внешний AI передаются только ограниченные evidence packets; имена документов псевдонимизируются, контакты и служебные шифры маскируются. Ключи сохраняются в Streamlit Secrets, а не в GitHub. Для OpenRouter: OPENROUTER_API_KEY и OPENROUTER_MODEL. Для Groq: GROQ_API_KEY; GROQ_MODEL можно указать как auto. Для DeepSeek: DEEPSEEK_API_KEY и DEEPSEEK_MODEL для автоматического выбора разрешённой модели. Режим «Авто» переключается на резервного провайдера при временной недоступности или исчерпании лимита.')
        if st.button('Сохранить AI-настройки', width='content'):
            st.session_state.external_ai_provider = provider
            st.session_state.ai_extraction_provider = extraction_provider
            st.session_state.ai_judge_provider = judge_provider
            st.session_state.ai_critic_provider = critic_provider
            st.session_state.ai_reviewer_provider = reviewer_provider
            st.session_state.ai_assisted_extraction = assisted
            st.session_state.ai_pipeline_level = ai_level
            st.success('Настройки AI сохранены для текущей сессии.')
        if st.button('Проверить агентный контур Extraction → Judge → Critic', width='content'):
            from core.ai_gateway import diagnostic_message, provider_for_role
            selected_state = dict(st.session_state)
            selected_state.update({
                'ai_extraction_provider': extraction_provider,
                'ai_judge_provider': judge_provider,
                'ai_critic_provider': critic_provider,
            })
            role_rows=[]
            actual={}
            with st.spinner('Проверяем три AI-роли на коротком обезличенном запросе...'):
                for role,label in (('extraction','Извлечение'),('judge','Оценка доказательства'),('critic','Независимая критика')):
                    role_provider=provider_for_role(role,selected_state,st.secrets)
                    result=role_provider.test_connection() if role_provider else None
                    ok=bool(result and result.ok)
                    actual[role]=str(getattr(result,'provider','') or '') if result else ''
                    role_rows.append({
                        'Роль':label,
                        'Настройка':selected_state.get(f'ai_{role}_provider',''),
                        'Фактический провайдер':actual[role] or '—',
                        'Модель':str(getattr(result,'model','') or '—') if result else '—',
                        'Результат':'Подключение работает' if ok else 'Ошибка подключения',
                        'Диагностика':diagnostic_message(result) if result else 'Провайдер не настроен.',
                    })
            st.dataframe(role_rows,hide_index=True,width='stretch')
            if actual.get('judge') and actual.get('critic') and actual['judge'] != actual['critic']:
                st.success('Judge и Critic фактически обслуживаются разными провайдерами: независимый консенсус L5 доступен.')
            elif actual.get('judge') and actual.get('critic'):
                st.warning('Judge и Critic фактически ответили через одного провайдера. Judge будет работать консультативно: сформирует адресные вопросы, но смысловые выводы останутся на L4 до независимой проверки.')
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
        st.info('Рекомендуемая схема: «Умный автоматический»; Extraction — Groq; Judge — OpenRouter (или DeepSeek, если доступен); Critic — Groq. При одном доступном провайдере Judge работает консультативно и не создаёт L5. Категоричный смысловой вывод разрешается только когда Judge и Critic фактически ответили через разных провайдеров. Для Groq рекомендуется GROQ_MODEL = "auto".')
        st.warning('Не передавайте конфиденциальные документы в бесплатные внешние сервисы без согласования с владельцем информации.')

    with tabs[6]:
        section('Core', 'Служебные параметры инженерного ядра.')
        if st.session_state.expert_mode:
            st.code(ctx.version)
            st.write(f'Каталог конфигурации: {ctx.config_dir}')
            st.caption('Диагностические параметры доступны только в режиме разработчика.')
        else:
            st.info('Включите режим разработчика в боковом меню, чтобы увидеть технические сведения Core.')
