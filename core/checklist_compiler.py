from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

from .normalization import normalize_text

@dataclass(frozen=True)
class CompiledChecklistRule:
    rule_type: str
    subject: str
    evidence_terms: tuple[str, ...]
    parameter_codes: tuple[str, ...]
    requires_semantic_review: bool
    rationale: str
    automation_class: str = "SEMANTIC"
    required_section_roles: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

PARAMETERS = {
    'AREA_BUILD': ('площадь застройки',), 'AREA_TOTAL': ('общая площадь',),
    'VOLUME_BUILD': ('строительный объем', 'строительный объём'), 'HEIGHT_BUILD': ('высота',),
    'FLOORS': ('этажность', 'этажей'), 'POWER_INSTALLED': ('установленная мощность', 'мощность'),
    'CAPACITY': ('производительность', 'пропускная способность'), 'PRESSURE': ('давление',),
    'FLOW_RATE': ('расход',), 'DIAMETER': ('диаметр',), 'LENGTH': ('длина', 'протяженность', 'протяжённость'),
    'VOLUME': ('объем', 'объём', 'вместимость'), 'QUANTITY': ('количество',),
    'ILLUMINATION': ('освещенность','освещённость','освещенности','освещённости'), 'RESPONSIBILITY_LEVEL': ('уровень ответственности',),
    'FIRE_RESISTANCE': ('степень огнестойкости',), 'FIRE_CLASS': ('класс функциональной пожарной опасности',),
    'ROAD_CATEGORY': ('категория дороги',), 'LANE_COUNT': ('количество полос',), 'SLOPE': ('уклон',),
    'LAND_AREA': ('площадь земельного участка','площадь участка'), 'STORAGE_CAPACITY': ('вместимость склада',),
}
SEMANTIC = ('обоснован', 'достаточн', 'рациональн', 'соответств', 'увязан', 'учтен', 'учтён', 'предусмотрен', 'обеспечен')
PRESENCE = ('наличие', 'представлен', 'приведен', 'приведён', 'указан', 'отражен', 'отражён', 'содержит')
STOP = {'проверить','проверка','соответствие','наличие','раздел','проектной','документации','должен','должна','должны','требования'}


def compile_item(item: dict[str, Any]) -> CompiledChecklistRule:
    question = normalize_text(item.get('question') or '')
    codes=[]
    for code,tokens in PARAMETERS.items():
        if any(token in question for token in tokens): codes.append(code)
    terms=tuple(dict.fromkeys(w for w in re.findall(r'[а-яa-z0-9-]{4,}', question) if w not in STOP))[:12]
    if codes and any(x in question for x in ('свер', 'соответств', 'совпад')):
        return CompiledChecklistRule('numeric_crosscheck','parameter',terms,tuple(codes),False,'Числовая межраздельная проверка.','CALC',('PROFILE_OWNER','DEPENDENT'))
    if any(x in question for x in PRESENCE):
        return CompiledChecklistRule('presence','document_content',terms,tuple(codes),False,'Проверка наличия требуемых сведений.','AUTO',('SELECTED_SECTION',))
    if any(x in question for x in SEMANTIC):
        return CompiledChecklistRule('semantic_review','engineering_solution',terms,tuple(codes),True,'Требуется смысловой анализ проектного решения.','SEMANTIC',('SELECTED_SECTION','RELATED_SECTIONS'))
    if codes:
        return CompiledChecklistRule('parameter_evidence','parameter',terms,tuple(codes),False,'Проверка наличия структурированных параметров.','AUTO',('SELECTED_SECTION',))
    return CompiledChecklistRule('semantic_review','general',terms,(),True,'Пункт требует аналитической оценки содержания.','EXPERT',('SELECTED_SECTION','RELATED_SECTIONS'))
