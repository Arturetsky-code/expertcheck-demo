from __future__ import annotations
from typing import Any
from .finding_qualification import qualify_comparison, qualify_checklist


def _text(row:dict[str,Any],*keys:str)->str:
    for k in keys:
        v=row.get(k)
        if v not in (None,'',[],{}): return str(v)
    return ''


def classify_finding(row:dict[str,Any], *, source_kind:str='comparison')->dict[str,Any]:
    """Single admission gate before any user-facing finding.

    Engines may emit diagnostics, but only this classifier decides whether a row is
    a project finding, a specialist review question, a system limitation or info.
    """
    explicit=str(row.get('finding_type') or '').upper().strip()
    if explicit in {'PROJECT_FINDING','REVIEW_QUESTION','SYSTEM_LIMITATION','INFORMATIONAL','PROJECT_STATUS'}:
        return {
            'finding_type':explicit,
            'user_status':row.get('user_status') or {
                'PROJECT_FINDING':'Проблема проекта','REVIEW_QUESTION':'Вопрос специалисту',
                'SYSTEM_LIMITATION':'Ограничение автоматической проверки','INFORMATIONAL':'Информация',
                'PROJECT_STATUS':'Проверено',
            }.get(explicit,'Информация'),
            'report_eligible':explicit in {'PROJECT_FINDING','REVIEW_QUESTION'},
            'action_eligible':explicit in {'PROJECT_FINDING','REVIEW_QUESTION'},
            'risk_eligible':explicit=='PROJECT_FINDING' or bool(row.get('risk_eligible') and explicit=='REVIEW_QUESTION'),
            'reason':row.get('finding_qualification_reason') or row.get('qualification_reason') or 'Тип вывода задан источником.',
        }
    blob=' '.join([
        _text(row,'parameter_name','parameter','Параметр'), _text(row,'status','result','Результат'),
        _text(row,'explanation','Пояснение','evidence','Обоснование'), _text(row,'recommendation')
    ]).lower()
    code=str(row.get('parameter_code') or '').upper()
    # Known diagnostic-only checks: inability of automation to verify a drawing field,
    # failed OCR/retrieval, missing second source without proven applicability.
    limitation_markers=(
        'независимое подтверждение на поле чертежа не получено','автоматически не найден',
        'автоматический анализ не подтвердил','не удалось подтвердить','не удалось проверить',
        'достаточные доказательства автоматически не выявлены','система не поддерживает',
        'ограничение автоматической проверки',
    )
    if code=='GP_EXPLICATION_FIELD' and 'совпад' not in blob:
        return {'finding_type':'SYSTEM_LIMITATION','user_status':'Ограничение автоматической проверки','report_eligible':False,'action_eligible':False,'risk_eligible':False,'reason':'Экспликация найдена, но поле чертежа не подтверждено автоматическим алгоритмом; это не доказывает дефект ПД.'}
    if any(x in blob for x in limitation_markers):
        return {'finding_type':'SYSTEM_LIMITATION','user_status':'Ограничение автоматической проверки','report_eligible':False,'action_eligible':False,'risk_eligible':False,'reason':'Алгоритм не смог завершить проверку; отсутствие автоматического подтверждения не является проблемой проекта.'}
    if source_kind=='checklist':
        q=qualify_checklist(row)
    else:
        q=qualify_comparison(row)
    ftype=q.get('finding_type') or 'INFORMATIONAL'
    applicability=bool(row.get('applicability_proven') or row.get('cross_section_required') or row.get('required_confirmation'))
    # Missing evidence may become a specialist question only when the engine has
    # independently proved that a second confirmation is required by the check contract.
    if ftype=='SYSTEM_LIMITATION' and applicability and any(x in blob for x in ('недостат','нет данных','не подтвержд','отсутств')):
        return {'finding_type':'REVIEW_QUESTION','user_status':'Вопрос специалисту','report_eligible':True,'action_eligible':True,'risk_eligible':False,'reason':'Не получено достаточного доказательства для проверки, при этом необходимость подтверждения установлена контрактом проверки.'}
    # Review questions require a proven reason why specialist review is needed.
    if ftype=='REVIEW_QUESTION':
        mismatch_signal=any(x in blob for x in ('расхожд','конфликт','не совпад'))
        applicable=bool(row.get('applicability_proven') or row.get('cross_section_required') or row.get('required_confirmation') or row.get('verified_negative') or row.get('explicit_contradiction'))
        # An explicit value conflict is itself a legitimate reason for specialist review.
        # Pure missing-evidence diagnostics still require proven applicability.
        if not applicable and not mismatch_signal:
            ftype='SYSTEM_LIMITATION'
            return {'finding_type':ftype,'user_status':'Ограничение автоматической проверки','report_eligible':False,'action_eligible':False,'risk_eligible':False,'reason':'Не доказана применимость требования дополнительного подтверждения; запись остаётся диагностикой.'}
    return {
        'finding_type':ftype,
        'user_status':q.get('user_status') or ('Проблема проекта' if ftype=='PROJECT_FINDING' else 'Вопрос специалисту'),
        'report_eligible':ftype in {'PROJECT_FINDING','REVIEW_QUESTION'},
        'action_eligible':ftype in {'PROJECT_FINDING','REVIEW_QUESTION'},
        'risk_eligible':bool(q.get('risk_eligible')) and ftype in {'PROJECT_FINDING','REVIEW_QUESTION'},
        'reason':q.get('reason') or '',
    }


def apply_finding_gate(rows:list[dict[str,Any]], *, source_kind:str='comparison')->list[dict[str,Any]]:
    out=[]
    for row in rows or []:
        item=dict(row)
        gate=classify_finding(item,source_kind=source_kind)
        item.update({
            'finding_type':gate['finding_type'],'user_status':gate['user_status'],
            'global_finding_reason':gate['reason'],'report_eligible':gate['report_eligible'],
            'action_eligible':gate['action_eligible'],'risk_eligible_global':gate['risk_eligible'],
        })
        out.append(item)
    return out
