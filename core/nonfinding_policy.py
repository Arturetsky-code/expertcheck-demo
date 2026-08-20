from __future__ import annotations
from typing import Any

NOT_FOUND_TOKENS=(
 'не найден','не найдены','не найдено','не подтвержден','не подтверждена','не подтверждено',
 'автоматический анализ не подтвердил','отсутствие найденного','недостаточно данных','нет данных'
)

def is_nonfinding_only(status:Any='', basis:Any='', evidence:Any='')->bool:
    blob=' '.join(str(x or '') for x in (status,basis,evidence)).lower()
    return any(t in blob for t in NOT_FOUND_TOKENS)

def can_create_negative_finding(*, status:Any='', basis:Any='', evidence:Any='', explicit_contradiction:bool=False)->bool:
    if explicit_contradiction:
        return bool(str(evidence or '').strip())
    if is_nonfinding_only(status,basis,evidence):
        return False
    return bool(str(evidence or '').strip()) and any(x in str(status or '').lower() for x in ('не соответствует','отклонение','расхожд','наруш'))

def diagnostic_status(reason:str='')->dict[str,Any]:
    return {
      'status':'Не проверено системой',
      'finding_class':'UNVERIFIED_BY_SYSTEM',
      'risk_eligible':False,
      'reason':reason or 'Автоматический поиск не дал достаточного доказательства; отрицательный вывод запрещён.',
    }
