from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path
import streamlit as st
BASE_DIR=Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
try:
    from analyzer import analyze_uploaded
    from studio.design import apply_design
    from studio.components import header,sidebar_brand,sidebar_group,sidebar_project
    from studio.data import frames,registry,passports,metrics,engineer_findings,assembly_rows,apply_project_assembly
    from studio.pages import PAGES
    from studio.auth import auth_screen
    from core.workspace_store import get_store, session_snapshot, snapshot_signature
    from core20.dual_run import build_dual_run_manifest
    from core.free_ai_patch import install as install_free_ai_patch
    from core.gemini_runtime_preference import install as install_gemini_runtime_preference
    from core.quality_gates_patch import install as install_quality_gates
    from core.gemini_model_tracking_patch import install as install_gemini_model_tracking
except Exception as startup_error:
    st.set_page_config(page_title='ExpertCheck Studio — ошибка запуска',layout='wide')
    st.error('ExpertCheck не смог загрузить обязательные модули.')
    st.code(f'{type(startup_error).__name__}: {startup_error}')
    st.stop()
install_free_ai_patch()
install_gemini_runtime_preference()
install_quality_gates()
install_gemini_model_tracking()
CONFIG_DIR=BASE_DIR/'config' if (BASE_DIR/'config').exists() else BASE_DIR
VERSION='ExpertCheck 20.0 Alpha 5 · Assignment Verification Expansion · Dual Run'
st.set_page_config(page_title='ExpertCheck Studio',page_icon='EC',layout='wide',initial_sidebar_state='expanded')
apply_design()
WORKSPACE_STORE=get_store(st.secrets, base_dir=BASE_DIR/'.expertcheck_data')
if not st.session_state.get('auth_user'):
    auth_screen(WORKSPACE_STORE)
    st.stop()
for k,v in {'project_name':'Новый проект','result':None,'analysis_time':None,'page':'Проект','expert_mode':False,'completeness_profile':'Капитальный объект','completeness_forming':True,'completeness_user_confirmed':False,'completeness_decisions':{},'object_registry_confirmed':False,'object_assembly_rows':[],'checklist_run':None,'checklist_user_results':{},'external_ai_provider':'Отключён','ai_extraction_provider':'Groq','ai_judge_provider':'Groq','ai_critic_provider':'Gemini','ai_reviewer_provider':'Gemini','ai_assisted_extraction':True,'ai_pipeline_level':'Умный автоматический','ai_object_reviews':{},'ai_checklist_reviews':{},'risk_user_decisions':{},'object_learning_examples':[],'semantic_execution_checkpoint':{},'provider_benchmark_results':{},'provider_benchmark_runs':{},'active_project_id':None}.items():
    st.session_state.setdefault(k,v)
if not st.session_state.get('_verified_core_ai_migrated'):
    if st.session_state.get('ai_judge_provider') == 'Авто: OpenRouter → Groq':
        st.session_state.ai_judge_provider = 'Groq'
    if st.session_state.get('ai_critic_provider') == 'Groq':
        st.session_state.ai_critic_provider = 'OpenRouter'
    st.session_state.ai_reviewer_provider = st.session_state.ai_critic_provider
    st.session_state._verified_core_ai_migrated = True
if not st.session_state.get('_resilient_free_ai_181_migrated'):
    if st.session_state.get('ai_critic_provider') == 'OpenRouter':
        st.session_state.ai_critic_provider = 'Gemini'
    if st.session_state.get('ai_reviewer_provider') == 'OpenRouter':
        st.session_state.ai_reviewer_provider = 'Gemini'
    if st.session_state.get('external_ai_provider') == 'OpenRouter':
        st.session_state.external_ai_provider = 'Отключён'
    st.session_state._resilient_free_ai_181_migrated = True
if not st.session_state.get('_quality_gates_183_migrated'):
    st.session_state.provider_benchmark_results = {}
    st.session_state.provider_benchmark_runs = {}
    st.session_state.semantic_execution_checkpoint = {}
    st.session_state._quality_gates_183_migrated = True
if not st.session_state.get('_verification_runtime_184_migrated'):
    # 18.4 changes queue semantics and Critic participation. Reuse of an old
    # partial 18.3 semantic checkpoint would make the control run incomparable.
    st.session_state.semantic_execution_checkpoint = {}
    st.session_state._verification_runtime_184_migrated = True
_pending_page = st.session_state.pop('_navigate_to', None)
if _pending_page:
    st.session_state['page'] = _pending_page
with st.sidebar:
    sidebar_brand()
    if st.button('＋ Новый проект', type='primary', width='stretch', key='sidebar_new_check'):
        user=st.session_state.get('auth_user') or {}
        pid=WORKSPACE_STORE.create_project(user.get('id'),'Новый проект')
        st.session_state.active_project_id=pid
        st.session_state.result=None
        st.session_state.analysis_time=None
        st.session_state.project_name='Новый проект'
        st.session_state.object_registry_confirmed=False
        st.session_state.object_assembly_rows=[]
        st.session_state.checklist_run=None
        st.session_state.checklist_user_results={}
        st.session_state.risk_user_decisions={}
        st.session_state.ai_checklist_batch_reviews={}
        st.session_state.semantic_execution_checkpoint={}
        st.session_state.page='Проект'
        st.rerun()
    sidebar_group('Этапы проверки')
    has_result = bool(st.session_state.result)
    object_gate = bool(st.session_state.get('object_registry_confirmed'))
    if st.session_state.get('expert_mode'):
        guided_pages = ['Мои проекты', 'Проект']
        if has_result:
            guided_pages.extend(['Состав объектов', 'Чек-листы'])
        if object_gate:
            guided_pages.extend(['Межраздельная сверка', 'Риски экспертизы', 'Отчёт'])
        guided_pages.append('Настройки')
    else:
        guided_pages=['Мои проекты','Проект']
        if has_result:
            guided_pages.extend(['Подтверждение','Проверка','Чек-листы','Результаты','Отчёт'])
        guided_pages.append('Настройки')
    if st.session_state.get('page') not in guided_pages:
        st.session_state.page = ('Проверка' if has_result and not st.session_state.get('expert_mode') else 'Состав объектов') if has_result else 'Мои проекты'
    page=st.radio('Раздел',guided_pages,label_visibility='collapsed',key='page')
    if not has_result:
        st.caption('Следующий этап откроется после загрузки проекта.')
    elif not object_gate:
        st.caption('Результаты до подтверждения состава считаются предварительными.')
    else:
        st.caption('Все основные этапы доступны.')
    user=st.session_state.get('auth_user') or {}
    st.caption(f"Пользователь: {user.get('display_name') or user.get('email','')}")
    if st.button('Выйти', width='stretch', key='sidebar_logout'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    status='Проект открыт' if st.session_state.result else 'Комплект не загружен'
    sidebar_project(st.session_state.project_name,status)
    if not has_result:
        st.info('Следующий шаг: загрузить комплект проектной документации.')
    elif not object_gate:
        st.info('Следующий шаг: проверить и подтвердить состав проектируемых объектов.')
    else:
        st.info('Следующий шаг: на странице «Проект» завершить AI-очередь, если она ещё не закрыта; затем разобрать подтверждённые замечания и инженерные вопросы.')
    sidebar_group('Режим интерфейса')
    st.session_state.expert_mode=st.toggle(
        'Режим разработчика',
        value=st.session_state.expert_mode,
        help='Включает служебные сведения, причины сопоставления и диагностику Core.',
        key='interface_mode_toggle',
    )
    st.caption('Рабочий режим' if not st.session_state.expert_mode else 'Отображаются технические данные')
    if not st.session_state.expert_mode:
        with st.expander('Дополнительно', expanded=False):
            st.caption('История проектов и расширенные настройки доступны в режиме разработчика.')
    st.caption(VERSION)
header(VERSION)
docs,findings,raw_comparisons=frames(st.session_state.result)
if st.session_state.result and not st.session_state.object_assembly_rows:
    st.session_state.object_assembly_rows=assembly_rows(docs,findings)
raw_passports=passports(docs)
filtered_registry,filtered_passports,comparisons=apply_project_assembly(docs,raw_passports,raw_comparisons,st.session_state.object_assembly_rows,st.session_state.object_registry_confirmed)

# 20.0 Alpha 5 expands typed Assignment verification and canonical evidence routing
# beside the accepted 18.7.3 result. It is observational only: no legacy verdict,
# report or user decision is changed here.
canonical_manifest=None
if st.session_state.result:
    try:
        canonical_manifest=build_dual_run_manifest(
            project_name=st.session_state.get('project_name') or 'Проект',
            documents=docs.to_dict('records'),
            findings=findings.to_dict('records'),
            comparisons=raw_comparisons.to_dict('records'),
            assembly_rows=st.session_state.get('object_assembly_rows') or [],
        )
        st.session_state['canonical_core_20_manifest']=canonical_manifest
    except Exception as canonical_error:
        canonical_manifest={
            'version':'20.0-alpha5-assignment-expansion',
            'legacy_results_unchanged':True,
            'error':f'{type(canonical_error).__name__}: {canonical_error}',
        }
        st.session_state['canonical_core_20_manifest']=canonical_manifest
        if st.session_state.get('expert_mode'):
            st.warning(f'Canonical Core 20.0 не построен: {canonical_manifest["error"]}')

if st.session_state.get('expert_mode'):
    with st.sidebar:
        with st.expander('20.0 · Canonical Core', expanded=False):
            if not canonical_manifest:
                st.caption('Состояние: ожидание проекта')
                st.caption('Откройте проект для построения canonical model.')
            elif canonical_manifest.get('error'):
                st.error('Dual-run: ошибка миграции')
                st.caption(canonical_manifest.get('error'))
            else:
                stats=canonical_manifest.get('stats') or {}
                st.caption(
                    f"Объекты {stats.get('objects',0)} / кандидаты {stats.get('object_candidates',0)} · "
                    f"показатели {stats.get('properties',0)} · evidence {stats.get('evidence',0)}"
                )
                st.caption(
                    f"Golden cases: {'OK' if canonical_manifest.get('golden_passed') else 'НЕ ПРОЙДЕНЫ'} · "
                    f"ошибки ссылок: {canonical_manifest.get('validation_errors',0)}"
                )
                verification=canonical_manifest.get('verification_engine') or {}
                st.caption(
                    f"Verification 2.0: {verification.get('decisions',0)} решений · "
                    f"авто {verification.get('automatic_verdict_eligible',0)} "
                    f"({verification.get('automatic_coverage_pct',0)}%) · "
                    f"ошибки контрактов {verification.get('contract_errors',0)}"
                )
                st.caption(
                    f"Межраздельно пересчитано: {verification.get('canonical_proofs_recomputed',0)} · "
                    f"Задание пересчитано: {verification.get('assignment_proofs_recomputed',0)}"
                )
                st.caption(
                    f"Typed Assignment: {verification.get('typed_assignment_auto',0)} · "
                    f"резервирование: {verification.get('reserve_topology_auto',0)} · "
                    f"router evidence: {verification.get('canonical_routed_evidence',0)}"
                )
                st.caption(
                    f"Binding blocked: {verification.get('parameter_binding_blocked',0)} · "
                    f"НТД fail-closed: {verification.get('normative_checks_guarded',0)} · "
                    f"расхождений с legacy: {verification.get('legacy_disagreements',0)}"
                )
                counts=verification.get('counts') or {}
                st.caption(
                    f"OK {counts.get('VERIFIED_OK',0)} · замечания {counts.get('PROJECT_FINDING',0)} · "
                    f"на проверку {counts.get('REVIEW_QUESTION',0)} · "
                    f"ограничения {counts.get('SYSTEM_LIMITATION',0)}"
                )
                st.caption('Legacy verdicts: без изменений')

if st.session_state.get('expert_mode') and canonical_manifest and not canonical_manifest.get('error'):
    verification=canonical_manifest.get('verification_engine') or {}
    audit_rows=list(verification.get('audit_rows') or [])
    with st.expander('20.0 · Canonical Verification Audit', expanded=False):
        if not audit_rows:
            st.caption('Автоматические канонические решения пока отсутствуют.')
        else:
            st.caption(
                'Показываются только автоматические канонические решения, PROJECT_FINDING и расхождения с legacy. '
                'Это диагностический слой; пользовательские legacy-вердикты пока не меняются.'
            )
            display_rows=[]
            for row in audit_rows:
                display_rows.append({
                    'Контур': row.get('domain') or '',
                    'Результат': row.get('kind') or '',
                    'Объект': row.get('object') or '',
                    'Проверка': row.get('check') or '',
                    'Код параметра': row.get('parameter_code') or '',
                    'Требуется': row.get('required_value'),
                    'В проекте': row.get('project_value'),
                    'Ед.': row.get('unit') or '',
                    'Код основания': row.get('reason_code') or '',
                    'Typed facts': row.get('typed_fact_count') or 0,
                    'Требуемая схема': str(row.get('required_topology') or ''),
                    'Схема в ПД': str(row.get('project_topology') or ''),
                    'Основание': row.get('reason') or '',
                    'Evidence': row.get('evidence') or '',
                    'Фрагмент evidence': row.get('evidence_fragment') or '',
                    'Trace ID': row.get('trace_id') or '',
                })
            st.dataframe(display_rows, hide_index=True, width='stretch')

data=(docs,findings,comparisons,filtered_registry,filtered_passports,metrics(comparisons),engineer_findings(findings))
@dataclass
class Context:
    data:tuple
    version:str
    config_dir:Path
    analyze:object
    workspace_store:object
    current_user:dict
ctx=Context(data,VERSION,CONFIG_DIR,analyze_uploaded,WORKSPACE_STORE,st.session_state.get('auth_user') or {})
PAGES[page](ctx)

_active=st.session_state.get('active_project_id')
_user=st.session_state.get('auth_user') or {}
if _active and _user.get('id') and st.session_state.get('result') is not None:
    try:
        _snapshot=session_snapshot(st.session_state)
        _signature=snapshot_signature(_snapshot)
        if st.session_state.get('_workspace_saved_signature') != _signature:
            WORKSPACE_STORE.save_project(
                _user['id'],_active,st.session_state.get('project_name') or 'Проект',
                _snapshot,status='analyzed',app_version=VERSION
            )
            st.session_state['_workspace_saved_signature']=_signature
    except PermissionError:
        st.error('Доступ к выбранному проекту запрещён.')
    except Exception as workspace_error:
        if st.session_state.get('expert_mode'):
            st.warning(f'Не удалось сохранить проект: {type(workspace_error).__name__}: {workspace_error}')