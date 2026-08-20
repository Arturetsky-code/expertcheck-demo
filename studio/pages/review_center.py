from __future__ import annotations
import pandas as pd
import streamlit as st
from studio.components import hero,card,empty,section
from core.display_localization import status_label
from core.global_finding_gate import apply_finding_gate
from . import objects, checklists, checks


def _first_doc(docs):
    if hasattr(docs,'empty') and not docs.empty:
        return docs.iloc[0].to_dict()
    return {}


def render(ctx):
    docs, findings, comparisons, registry, passports, metrics, eng = ctx.data
    hero('Центр проверки','Один рабочий маршрут: подтвердить состав, проверить требования и выполнить инженерные сверки.','В рабочем режиме технические детали скрыты; они остаются доступны в режиме разработчика.')
    if docs.empty:
        return empty('Сначала загрузите и обработайте комплект проекта.')
    first=_first_doc(docs)
    assignment=list(first.get('assignment_compliance') or [])
    a_summary=dict(first.get('assignment_compliance_summary') or {})
    n_summary=dict(first.get('normative_compliance_summary') or {})
    gated=apply_finding_gate(comparisons.to_dict('records') if not comparisons.empty else [])
    c1,c2,c3,c4=st.columns(4)
    with c1: card('Состав проекта',len(st.session_state.get('object_assembly_rows') or []),'Объекты и сооружения')
    with c2: card('Задание',a_summary.get('compliant',0),f"Подтверждено из {a_summary.get('total',len(assignment))}")
    with c3: card('НТД',n_summary.get('verified_clause',0),f"Верифицированных пунктов · покрытие {n_summary.get('verified_coverage_pct',0)}%")
    with c4: card('Выводы',sum(1 for x in gated if x.get('finding_type')=='PROJECT_FINDING'), 'Доказанные проблемы проекта')

    tabs=st.tabs(['1. Состав объектов','2. Задание','3. НТД','4. Чек-листы','5. Сверки'])
    with tabs[0]:
        objects.render(ctx)
    with tabs[1]:
        section('Проверка Задания на проектирование','Показываются требования и результат доказательной проверки. Технические кандидаты скрыты в рабочем режиме.')
        if not assignment:
            empty('Задание на проектирование не обнаружено или не разобрано.')
        else:
            rows=[]
            for r in assignment:
                rows.append({
                    '№':r.get('row_no') or r.get('requirement_no') or '',
                    'Требование':r.get('requirement_text') or r.get('requirement') or '',
                    'Тип проверки':status_label(r.get('check_type') or r.get('requirement_type') or ''),
                    'Результат':r.get('status') or r.get('result') or 'Не проверено системой',
                    'Доказательство':r.get('evidence_summary') or r.get('evidence') or '',
                })
            st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    with tabs[2]:
        section('Нормативная проверка','В рабочем режиме показывается только фактическое покрытие верифицированными требованиями, а не все найденные упоминания НТД.')
        c1,c2,c3=st.columns(3)
        c1.metric('Структурированных требований',n_summary.get('requirements',0))
        c2.metric('Верифицированных пунктов',n_summary.get('verified_clause',0))
        c3.metric('Покрытие',f"{n_summary.get('verified_coverage_pct',0)}%")
        rows=list(first.get('normative_compliance_audit') or [])
        if rows:
            compact=[]
            for r in rows:
                compact.append({
                    'НТД':r.get('reference') or r.get('document_id') or '',
                    'Пункт':r.get('clause') or r.get('clause_id') or '—',
                    'Требование':r.get('requirement') or r.get('requirement_text') or '',
                    'Результат':r.get('status') or r.get('result') or 'Не покрыто нормативной базой ExpertCheck',
                })
            st.dataframe(pd.DataFrame(compact),hide_index=True,width='stretch')
        else:
            st.info('Пока нет нормативных требований, допущенных к доказательной проверке. Реестр упоминаний НТД доступен только в техническом приложении.')
    with tabs[3]:
        checklists.render(ctx)
    with tabs[4]:
        checks.render(ctx)
