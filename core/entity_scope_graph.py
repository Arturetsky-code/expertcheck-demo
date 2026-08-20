from __future__ import annotations
from typing import Any
from .normalization import normalize_text

LEVELS=('PROJECT','SITE','COMPLEX','OBJECT','EQUIPMENT','ROOM')
LABELS={'PROJECT':'Проект','SITE':'Площадка','COMPLEX':'Комплекс','OBJECT':'Объект/сооружение','EQUIPMENT':'Оборудование','ROOM':'Помещение'}

def infer_entity_level(name:Any, position:Any='', context:Any='')->str:
    text=normalize_text(' '.join(map(str,(name or '',context or ''))))
    if any(x in text for x in ('помещение','венткамера','тамбур','коридор','уборная')): return 'ROOM'
    if any(x in text for x in ('оборудование','дробилка','конвейер','грохот','насос ','вентилятор')): return 'EQUIPMENT'
    if any(x in text for x in ('комплекс','дск','завод','установка кучного')): return 'COMPLEX'
    if any(x in text for x in ('площадка','территория','земельного участка')): return 'SITE'
    if any(x in text for x in ('здание','сооружение','станция','резервуар','склад','кпп','эстакада','стена')): return 'OBJECT'
    return 'PROJECT' if not str(position or '').strip() else 'OBJECT'

def metric_scope_compatible(metric_scope:Any, entity_level:Any)->bool:
    ms=normalize_text(metric_scope);el=str(entity_level or '').upper()
    if not ms or ms in {'default','основной показатель'}: return True
    if 'room' in ms or 'помещ' in ms: return el=='ROOM'
    if 'site' in ms or 'площадк' in ms or 'территор' in ms: return el in {'SITE','PROJECT'}
    if 'building' in ms or 'здан' in ms or 'footprint' in ms: return el in {'OBJECT','COMPLEX'}
    if 'equipment' in ms or 'оборуд' in ms: return el=='EQUIPMENT'
    return True

def scope_label(level:Any)->str:
    return LABELS.get(str(level or '').upper(),str(level or 'Не определён'))
