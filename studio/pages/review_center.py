from __future__ import annotations
import pandas as pd
import streamlit as st
from studio.components import hero,card,empty,section
from core.display_localization import status_label, scope_label
from core.project_review_planner import build_review_plan


def _first(docs):
    return docs.iloc[0].to_dict() if hasattr(docs,'empty') and not docs.empty else {}


def _domain_card(label,summary):
    total=int(summary.get('total') or 0); done=int(summary.get('completed') or 0)
    pct=float(summary.get('automatic_coverage_pct') or 0)
    card(label,f'{done}/{total}',f'Доказательно завершено · {pct:.1f}%','ok' if total and done==total else 'warn')


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero('Проверка проекта','ExpertCheck формирует план проверки под конкретный комплект и выполняет только применимые проверки.','Три главных контура: Задание · НТД · Чек-листы')
    if docs.empty:return empty('Сначала загрузите и обработайте комплект проекта.')
    first=_first(docs)
    plan=dict(first.get('project_review_plan') or {})
    if not plan:
        plan=build_review_plan(
            assignment_rows=list(first.get('assignment_compliance') or []),
            normative_rows=list(first.get('normative_compliance_audit') or []),
            checklist_review=dict(first.get('automatic_checklist_review') or {}),
            comparisons=comparisons.to_dict('records') if not comparisons.empty else [],
        )
    domains=plan.get('domains') or {}
    c1,c2,c3=st.columns(3)
    with c1:_domain_card('Задание на проектирование',domains.get('assignment') or {})
    with c2:_domain_card('Нормативные требования',domains.get('normative') or {})
    with c3:_domain_card('Корпоративные чек-листы',domains.get('checklist') or {})

    st.caption('Покрытие показывает только проверки, завершённые доказательным результатом. Ненайденные сведения и ограничения алгоритма не считаются несоответствиями проекта.')

    checklist_rows=list((first.get('automatic_checklist_review') or {}).get('results') or [])
    trusted_recipes=sum(1 for x in checklist_rows if x.get('recipe_status')=='TRUSTED')
    experimental_recipes=sum(1 for x in checklist_rows if x.get('recipe_status')=='EXPERIMENTAL')
    if trusted_recipes or experimental_recipes:
        st.caption(f'Фабрика проверок: доверенных рецептов в текущем контуре — {trusted_recipes}; экспериментальных — {experimental_recipes}. Экспериментальный рецепт не имеет права автоматически подтвердить соответствие.')
    checks=list(plan.get('checks') or [])
    if checks:
        rows=[]
        for x in checks:
            if x.get('verification_kind') not in {'PROJECT_FINDING','REVIEW_QUESTION','SYSTEM_LIMITATION'}: continue
            rows.append({
                'Контур':{'assignment':'Задание','normative':'НТД','checklist':'Чек-лист'}.get(x.get('domain'),x.get('domain')),
                'Проверка':x.get('check'),'Результат':x.get('verification_state'),
                'Область':scope_label(x.get('scope')) if x.get('scope') else '—',
            })
        if rows:
            section('Незавершённые и проблемные проверки','В рабочем режиме показывается только то, что требует решения или отражает текущее покрытие.')
            df=pd.DataFrame(rows)
            # System limitations are summarized rather than flooding the table.
            visible=df[df['Результат']!='Не проверено автоматически'].head(40)
            if not visible.empty:st.dataframe(visible,hide_index=True,width='stretch')
            limits=int((df['Результат']=='Не проверено автоматически').sum())
            if limits:st.info(f'Автоматически не завершено: {limits} проверок. Подробности доступны в техническом приложении и режиме разработчика.')

    if st.session_state.get('expert_mode'):
        with st.expander('План проверки · технические детали',expanded=False):
            st.json(plan)
