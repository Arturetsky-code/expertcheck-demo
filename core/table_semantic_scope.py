from __future__ import annotations
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code, classify_object


def assess_table_semantic_scope(finding:dict[str,Any])->dict[str,Any]:
    """Conservative table-scope guard.

    Prevent project/site-level TEP rows from being promoted to child equipment merely
    because the equipment name is the nearest object anchor in the page text.
    """
    code=canonical_parameter_code(finding.get('parameter_code'))
    obj=str(finding.get('semantic_anchor_name') or finding.get('object_hint') or '')
    blob=normalize_text(' '.join(str(finding.get(k) or '') for k in ('context','table_title','table_evidence','row_text','structural_zone')))
    binding=str(finding.get('binding_status') or finding.get('property_binding_status') or '').upper()
    decision='ALLOW'; reasons=[]; scope='OBJECT'
    if any(x in blob for x in ('площадь территории','площадь земельного участка','площадь площадки','технико экономические показатели площадки','технико-экономические показатели площадки')):
        scope='SITE'
    if any(x in blob for x in ('основные технико экономические показатели проекта','основные технико-экономические показатели проекта')):
        scope='PROJECT'
    try: otype=classify_object(obj).code
    except Exception: otype=''
    if code in {'AREA_BUILD','AREA_TOTAL','CAPACITY','QUANTITY'} and scope in {'SITE','PROJECT'} and otype in {'TECHNOLOGICAL_COMPLEX','BUILDING','PUMP_STATION','TRANSFORMER_STATION','RESERVOIR','LINEAR_STRUCTURE'}:
        if binding not in {'ROW_LOCKED','POSITION_LOCKED','EXACT_OBJECT'}:
            decision='HOLD'; reasons.append('показатель относится к уровню площадки/проекта, а привязка к дочернему объекту не подтверждена строкой таблицы')
    if code=='AREA_BUILD' and ('оборудован' in normalize_text(obj) or otype=='TECHNOLOGICAL_COMPLEX') and binding not in {'ROW_LOCKED','POSITION_LOCKED','EXACT_OBJECT'}:
        if any(x in blob for x in ('площадь территории','площадь площадки')):
            decision='HOLD'; reasons.append('площадь площадки не может автоматически наследоваться оборудованием/дочерним комплексом')
    return {'table_semantic_scope':scope,'table_semantic_scope_decision':decision,'table_semantic_scope_reasons':reasons}


def annotate_table_semantic_scope(findings:list[dict[str,Any]])->dict[str,int]:
    stats={'allow':0,'hold':0}
    for f in findings or []:
        r=assess_table_semantic_scope(f); f.update(r)
        stats['hold' if r['table_semantic_scope_decision']=='HOLD' else 'allow']+=1
    return stats
