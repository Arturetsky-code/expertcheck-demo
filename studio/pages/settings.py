from __future__ import annotations

import json
import time
import streamlit as st

from studio.components import hero, section, status_badge


def _reset_project() -> None:
    st.session_state.result = None
    st.session_state.analysis_time = None
    st.session_state.project_name = 'Новый проект'
    st.session_state.completeness_user_confirmed = False
    st.session_state.completeness_decisions = {}
    st.session_state['_navigate_to'] = 'Проект'


def _apply_qualified_scheme(winner: str, reserve: str) -> None:
    """Apply benchmark routing before Streamlit instantiates role widgets."""
    for key in ('ai_extraction_provider', 'settings_ai_extraction_provider',
                'ai_judge_provider', 'settings_ai_judge_provider'):
        st.session_state[key] = winner
    if reserve:
        for key in ('ai_critic_provider', 'settings_ai_critic_provider', 'ai_reviewer_provider'):
            st.session_state[key] = reserve
        st.session_state._provider_scheme_notice = (
            'success', f'Применено: Judge — {winner}; независимый Critic — {reserve}.'
        )
    else:
        st.session_state._provider_scheme_notice = (
            'warning',
            f'Judge переключён на {winner}. Второй независимый провайдер ещё не квалифицирован; '
            'смысловые результаты останутся L4 до его успешной проверки.',
        )
    st.session_state._verified_core_ai_migrated = True


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
        direct_provider_options = ['Groq', 'Gemini', 'DeepSeek', 'OpenRouter']
        automatic_provider_options = ['Авто: Groq → Gemini', 'Авто: Gemini → Groq']
        provider_options = ['Отключён', *direct_provider_options, *automatic_provider_options]
        role_provider_options = [*direct_provider_options, *automatic_provider_options]
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
                role_provider_options,
                index=role_provider_options.index(st.session_state.get('ai_extraction_provider', 'Groq')) if st.session_state.get('ai_extraction_provider', 'Groq') in role_provider_options else 0,
                key='settings_ai_extraction_provider',
                help='Быстро извлекает объекты, показатели и спорные смысловые кандидаты. Рекомендуется Groq.',
            )
        with c_judge:
            judge_provider = st.selectbox(
                'AI Judge — оценка доказательства',
                role_provider_options,
                index=role_provider_options.index(st.session_state.get('ai_judge_provider', 'Groq')) if st.session_state.get('ai_judge_provider', 'Groq') in role_provider_options else 0,
                key='settings_ai_judge_provider',
                help='Сопоставляет одно атомарное требование с небольшим адресным evidence packet.',
            )
        with c_critic:
            critic_provider = st.selectbox(
                'AI Critic — независимая проверка',
                role_provider_options,
                index=role_provider_options.index(st.session_state.get('ai_critic_provider', 'Gemini')) if st.session_state.get('ai_critic_provider', 'Gemini') in role_provider_options else 1,
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
        st.caption('Во внешний AI передаются только ограниченные evidence packets; имена документов псевдонимизируются, контакты и служебные шифры маскируются. Ключи сохраняются в Streamlit Secrets. Бесплатная базовая схема 18.2: GROQ_API_KEY + GROQ_MODEL=`openai/gpt-oss-120b`; GEMINI_API_KEY + GEMINI_MODEL=`auto` (рекомендуется). Если GEMINI_MODEL не задан или устарел, ExpertCheck запрашивает список реально доступных моделей и выбирает рабочую Flash/Flash-Lite автоматически.')
        st.info('18.2 не привязан к конкретной Gemini-модели. Фактическая модель показывается в проверке агентного контура и в квалификационном стенде.')
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
            from core.ai_gateway import provider_for_role
            from core.semantic_evidence_engine import preflight_provider
            selected_state = dict(st.session_state)
            selected_state.update({
                'ai_extraction_provider': extraction_provider,
                'ai_judge_provider': judge_provider,
                'ai_critic_provider': critic_provider,
            })
            role_rows=[]
            actual={}
            role_ok={}
            with st.spinner('Проверяем подключение и рабочие JSON-контракты ролей...'):
                for role,label in (('extraction','Извлечение'),('judge','Оценка доказательства'),('critic','Независимая критика')):
                    role_provider=provider_for_role(role,selected_state,st.secrets)
                    probe=preflight_provider(role_provider,role.upper(),structured=role != 'extraction')
                    ok=bool(probe.get('ok'))
                    role_ok[role]=ok
                    actual[role]=str(probe.get('actual_provider') or '') if ok else ''
                    role_rows.append({
                        'Роль':label,
                        'Настройка':selected_state.get(f'ai_{role}_provider',''),
                        'Фактический провайдер':actual[role] or '—',
                        'Модель':str(probe.get('model') or '—'),
                        'Результат':('Рабочий JSON-контракт' if role != 'extraction' else 'Подключение работает') if ok else 'Проверка не пройдена',
                        'Диагностика':('Строгий контракт подтверждён.' if role != 'extraction' else 'Короткий запрос выполнен.') if ok else str(probe.get('error') or 'Провайдер не настроен.'),
                    })
            st.dataframe(role_rows,hide_index=True,width='stretch')
            from core.provider_benchmark import BENCHMARK_VERSION
            benchmark_results = dict(st.session_state.get('provider_benchmark_results') or {})
            judge_benchmark = benchmark_results.get(actual.get('judge')) or {}
            critic_benchmark = benchmark_results.get(actual.get('critic')) or {}
            judge_qualified = bool(judge_benchmark.get('qualified') and judge_benchmark.get('completed') and judge_benchmark.get('version') == BENCHMARK_VERSION)
            critic_qualified = bool(critic_benchmark.get('qualified') and critic_benchmark.get('completed') and critic_benchmark.get('version') == BENCHMARK_VERSION)
            if role_ok.get('judge') and role_ok.get('critic') and actual.get('judge') != actual.get('critic') and judge_qualified and critic_qualified:
                st.success('Judge и Critic прошли рабочий JSON-контракт и полный стенд у разных провайдеров: независимый консенсус L5 доступен.')
            elif role_ok.get('judge') and role_ok.get('critic') and actual.get('judge') != actual.get('critic'):
                st.info('Обе роли технически работают через разных провайдеров. До завершения квалификационного стенда их смысловые решения остаются на L4.')
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
        st.divider()
        section(
            'Квалификация AI-провайдера',
            '30 синтетических инженерных пакетов × 3 повтора. Выполняется возобновляемыми порциями с учётом бесплатных лимитов; проектные документы не передаются.',
        )
        benchmark_candidate = st.selectbox(
            'Кандидат для проверки', ['Groq', 'Gemini'], key='provider_benchmark_candidate',
            help='Проверяйте кандидатов по очереди. Стенд сохраняет прогресс после каждой порции и не считает временный HTTP 429 смысловой ошибкой модели.',
        )
        benchmark_runs = dict(st.session_state.get('provider_benchmark_runs') or {})
        active_run = dict(benchmark_runs.get(benchmark_candidate) or {})
        if active_run and not active_run.get('completed'):
            completed_calls = int(active_run.get('next_call_index') or 0)
            total_calls = int(active_run.get('total_calls') or 18)
            st.progress(completed_calls / max(1,total_calls), text=f'Выполнено пакетных вызовов: {completed_calls} из {total_calls}')
            remaining = max(0, int(float(active_run.get('cooldown_until') or 0)-time.time()+0.999))
            if remaining:
                st.info(f'Прогресс сохранён. Следующую порцию можно запустить примерно через {remaining} с — это защита бесплатной квоты.')
            if active_run.get('last_transport_error') and st.session_state.expert_mode:
                st.caption('Последнее транспортное событие: '+str(active_run.get('last_transport_error')))
        run_label = 'Начать квалификационный стенд' if not active_run or active_run.get('completed') else 'Продолжить квалификационный стенд'
        if st.button(run_label, width='content'):
            from core.ai_gateway import provider_from_settings
            from core.provider_benchmark import advance_provider_benchmark, start_provider_benchmark
            candidate_provider = provider_from_settings(benchmark_candidate, st.secrets)
            if not candidate_provider or not getattr(candidate_provider,'api_key',''):
                st.error(f'API-ключ {benchmark_candidate} не найден в Streamlit Secrets.')
            else:
                if not active_run or active_run.get('completed'):
                    active_run=start_provider_benchmark(candidate_provider,repeats=3,batch_size=5)
                with st.spinner('Обрабатываем следующую безопасную порцию и сохраняем прогресс...'):
                    active_run=advance_provider_benchmark(candidate_provider,active_run,max_calls=3)
                benchmark_runs[benchmark_candidate]=active_run
                st.session_state.provider_benchmark_runs=benchmark_runs
                benchmark=dict(active_run.get('summary') or {})
                if active_run.get('completed'):
                    stored = dict(st.session_state.get('provider_benchmark_results') or {})
                    stored[benchmark_candidate] = benchmark
                    st.session_state.provider_benchmark_results = stored
                    if benchmark.get('qualified'):
                        st.success(f'{benchmark_candidate} прошёл квалификационный барьер.')
                    else:
                        st.error(f'{benchmark_candidate} завершил стенд, но не прошёл квалификационный барьер.')
                elif active_run.get('blocked'):
                    st.error(f'{benchmark_candidate}: провайдер заблокировал продолжение. Проверьте ключ, модель и доступ проекта.')
                else:
                    done=int(active_run.get('next_call_index') or 0)
                    st.success(f'Прогресс сохранён: {done} из {active_run.get("total_calls",18)} пакетных вызовов.')
        benchmark_results = dict(st.session_state.get('provider_benchmark_results') or {})
        if benchmark_results:
            from core.provider_benchmark import comparison_rows, qualified_ranking
            st.dataframe(comparison_rows(benchmark_results), hide_index=True, width='stretch')
            for label, result in benchmark_results.items():
                failures = result.get('gate_failures') or []
                if failures:
                    st.caption(f"{label}: " + '; '.join(failures))
            st.download_button(
                'Скачать протокол квалификации JSON',
                data=json.dumps(benchmark_results, ensure_ascii=False, indent=2),
                file_name='ExpertCheck_AI_Provider_Qualification.json',
                mime='application/json',
                width='content',
            )
            ranking = qualified_ranking(benchmark_results)
            if ranking:
                winner = ranking[0]
                reserve = ranking[1] if len(ranking) > 1 else ''
                st.button(
                    'Применить квалифицированную схему', type='primary', width='content',
                    on_click=_apply_qualified_scheme, args=(winner, reserve),
                )
                notice = st.session_state.pop('_provider_scheme_notice', None)
                if notice:
                    getattr(st, notice[0])(notice[1])
                if len(ranking) == 1:
                    st.caption('Для автоматического L5 квалифицируйте второй независимый провайдер.')
        st.info('Базовая бесплатная схема 18.2: Extraction/Judge — Groq `openai/gpt-oss-120b`; Critic — Gemini с автоматическим выбором доступной Flash/Flash-Lite модели. После квалификации роли могут быть переставлены по результатам стенда, но Judge и Critic должны фактически обслуживаться разными провайдерами. До независимой квалификации смысловые решения остаются консультативными L4.')
        st.warning('Бесплатный тариф Gemini может использовать переданное содержимое для улучшения продуктов Google. Передавайте только ограниченные обезличенные evidence packets и не передавайте полные конфиденциальные PDF.')

    with tabs[6]:
        section('Core', 'Служебные параметры инженерного ядра.')
        if st.session_state.expert_mode:
            st.code(ctx.version)
            st.write(f'Каталог конфигурации: {ctx.config_dir}')
            st.caption('Диагностические параметры доступны только в режиме разработчика.')
        else:
            st.info('Включите режим разработчика в боковом меню, чтобы увидеть технические сведения Core.')
