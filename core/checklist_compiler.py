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
    evidence_types: tuple[str, ...] = ()
    negative_result_policy: str = 'CONSERVATIVE'
    typed_check: str = 'SPECIALIST_REVIEW'

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
    'RESERVOIR_COUNT': ('количество резервуаров','число резервуаров'),
    'FIRE_WATER_RESERVE': ('противопожарный запас воды','запас воды'),
    'PUMP_HEAD': ('напор насосной станции','напор'),
    'SEISMICITY': ('сейсмичность','сейсмический'),
    'SANITARY_ZONE': ('санитарно-защитная зона','сзз'),
    'ROAD_LENGTH': ('протяженность дороги','протяжённость дороги'),
    'ROAD_WIDTH': ('ширина проезжей части','ширина дороги'),
}

MANDATORY_DOCUMENT = ('справк','договор аренды','гпзу','градостроительный план','технические условия','задание на проектирование','окн','объект культурного наследия','оопт','особо охраняем')
SECTION_STRUCTURE = ('постановлен', '№87', '87', 'обязательн', 'состав раздела', 'содержание раздела')
SEMANTIC = ('обоснован', 'достаточн', 'рациональн', 'соответств', 'увязан', 'учтен', 'учтён', 'предусмотрен', 'обеспечен')
PRESENCE = ('наличие', 'представлен', 'приведен', 'приведён', 'указан', 'отражен', 'отражён', 'содержит')
STOP = {'проверить','проверка','соответствие','наличие','раздел','проектной','документации','должен','должна','должны','требования'}


def compile_item(item: dict[str, Any]) -> CompiledChecklistRule:
    question = normalize_text(item.get('question') or '')
    codes=[]
    for code,tokens in PARAMETERS.items():
        if any(token in question for token in tokens): codes.append(code)
    terms=tuple(dict.fromkeys(w for w in re.findall(r'[а-яa-z0-9-]{4,}', question) if w not in STOP))[:12]
    if any(x in question for x in MANDATORY_DOCUMENT):
        return CompiledChecklistRule('mandatory_document','source_document',terms,tuple(codes),False,'Проверка наличия обязательного/исходно-разрешительного документа.','AUTO',('PROJECT_SET',),('DOCUMENT_IDENTITY','PAGE_REFERENCE'),'CONSERVATIVE','DOCUMENT_CONTENT_PRESENCE')
    if any(x in question for x in SECTION_STRUCTURE):
        return CompiledChecklistRule('section_structure','pp87_requirement',terms,tuple(codes),True,'Проверка структуры и обязательного содержания раздела ПД.','SEMANTIC',('SELECTED_SECTION',),('NORMATIVE_CONTEXT','RELEVANT_FRAGMENT','PAGE_REFERENCE'),'AI_WITH_EVIDENCE','NORMATIVE_CONTENT_REVIEW')
    if codes and any(x in question for x in ('свер', 'соответств', 'совпад')):
        return CompiledChecklistRule('numeric_crosscheck','parameter',terms,tuple(codes),False,'Числовая межраздельная проверка.','CALC',('PROFILE_OWNER','DEPENDENT'),('STRUCTURED_VALUE','SOURCE_SECTION'),'STRICT','ENGINEERING_VALUE_CROSSCHECK')
    if any(x in question for x in PRESENCE):
        return CompiledChecklistRule('presence','document_content',terms,tuple(codes),False,'Проверка наличия требуемых сведений.','AUTO',('SELECTED_SECTION',),('TEXT_OR_TABLE','PAGE_REFERENCE'),'CONSERVATIVE','DRAWING_PRESENCE_CHECK' if any(x in question for x in ('план','чертеж','чертёж','разрез','фасад','схем')) else 'DOCUMENT_CONTENT_PRESENCE')
    if any(x in question for x in SEMANTIC):
        return CompiledChecklistRule('semantic_review','engineering_solution',terms,tuple(codes),True,'Требуется смысловой анализ проектного решения.','SEMANTIC',('SELECTED_SECTION','RELATED_SECTIONS'),('RELEVANT_FRAGMENT','NORMATIVE_CONTEXT','REMARK_ANALOG'),'AI_WITH_EVIDENCE','ENGINEERING_SEMANTIC_REVIEW')
    if codes:
        return CompiledChecklistRule('parameter_evidence','parameter',terms,tuple(codes),False,'Проверка наличия структурированных параметров.','AUTO',('SELECTED_SECTION',),('STRUCTURED_VALUE','PAGE_REFERENCE'),'CONSERVATIVE','ENGINEERING_PARAMETER_PRESENCE')
    return CompiledChecklistRule('semantic_review','general',terms,(),True,'Пункт требует аналитической оценки содержания.','EXPERT',('SELECTED_SECTION','RELATED_SECTIONS'),('ENGINEERING_EVIDENCE','SPECIALIST_REVIEW'),'SPECIALIST','DRAWING_TITLE_BLOCK_CHECK' if any(x in question for x in ('основн надпис','штамп','основная надпись')) else 'SPECIALIST_REVIEW')
