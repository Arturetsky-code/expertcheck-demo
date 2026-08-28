from __future__ import annotations
from typing import Any

_LABELS = {
 'VERIFIED_EVIDENCE':'Подтверждённое доказательство','CANDIDATE_EVIDENCE':'Кандидат в доказательства','NO_EVIDENCE':'Доказательства не найдены',
 'PROJECT_GLOBAL':'Весь проект','SITE_SPECIFIC':'Площадка / земельный участок','OBJECT_SPECIFIC':'Конкретный объект','SYSTEM_SPECIFIC':'Инженерная система','EQUIPMENT_SPECIFIC':'Оборудование','DOCUMENT_SPECIFIC':'Документ / раздел','UNRESOLVED':'Область не определена',
 'MATERIAL_OR_PROCESS':'Материал / технологический процесс','SYSTEM_OR_EQUIPMENT':'Инженерная система / оборудование','EQUIPMENT_OR_OBJECT':'Оборудование / объект',
 'VALUE_COMPARISON':'Сверка числового значения','SET_COMPARISON':'Сверка состава / перечня','CROSS_DOCUMENT_TRACE':'Прослеживаемость между документами','PRESENCE_REQUIREMENT':'Проверка наличия','NORMATIVE_COMPLIANCE':'Проверка требования НТД','CALCULATION_PRESENCE':'Проверка наличия расчёта','DRAWING_REQUIREMENT':'Проверка графического материала','PROHIBITION_OR_NOT_REQUIRED':'Проверка запрета / неприменимости','DESIGN_DETERMINED':'Определяется проектом','SEMANTIC_ENGINEERING':'Смысловая инженерная проверка',
 'APPLICABILITY_DECLARATION':'Декларация применимости','TRACEABILITY':'Прослеживаемость источника',
 'DOCUMENT_DELIVERABLE':'Требование к комплекту документов','TOPOLOGY_REQUIREMENT':'Требование к структуре системы',
 'TRACE_CHAIN':'Прослеживаемость цепочки источников','CALCULATION_PRESENCE':'Проверка наличия расчёта','DRAWING_EVIDENCE':'Доказательство на чертеже','NORMATIVE_LINK':'Связь с верифицированным требованием НТД','APPLICABILITY_REVIEW':'Проверка применимости','AI_EVIDENCE_REVIEW':'Смысловая проверка доказательств AI',
 'KB_GAP':'Не покрыто нормативной базой ExpertCheck','EVIDENCE_GAP':'Недостаточно проектных доказательств','READY_FOR_REVIEW':'Готово к проверке по доказательствам',
 'LAW_REQUIREMENT':'Нормативное требование','ENGINEERING_RULE':'Инженерное правило ExpertCheck','EXPERT_PRACTICE_RULE':'Правило из практики экспертизы',
 'CONFIRMED_ISSUE':'Подтверждённое несоответствие','REVIEW':'Требует проверки','INSUFFICIENT_DATA':'Недостаточно данных','UNVERIFIED_BY_SYSTEM':'Не проверено системой','OK':'Проверено',
 'ROW_LOCKED':'Привязано к строке','POSITION_LOCKED':'Привязано к позиции','HOLD':'Не допущено в модель','SUPPORTED':'Подтверждено','REJECT':'Отклонено',
 'ADMIT':'Допущено в модель','VERIFIED':'Верифицировано','BLOCKED':'Заблокировано','PASSED':'Пройдено','FAILED':'Не пройдено','NOT_REQUIRED':'Не требуется',
 'TRUSTED':'Доверенный рецепт','EXPERIMENTAL':'Экспериментальный рецепт','RETRIEVAL_ONLY':'Только поиск кандидатов',
 'SATISFIED':'Выполнен','UNSATISFIED':'Не выполнен','SUPPORTS':'Подтверждает','CONTRADICTS':'Противоречит',
 'ACCEPTED':'Принято','NOT_RUN':'Не запускалось','PARTIAL':'Частичный ответ','CONFIRMED':'Подтверждено',
 'ADVISORY_ONLY':'Только консультативный вывод','COMPLETED':'Выполнено',
 'INDEPENDENT_CONSENSUS':'Независимый Judge/Critic','ADVISORY_JUDGE_ONLY':'Консультативный Judge',
 'NO_ELIGIBLE_PACKETS':'Нет подходящих пакетов','DISABLED':'Отключено',
 'CONSENSUS':'Независимый консенсус','DETERMINISTIC':'Детерминированная проверка','SPECIALIST':'Проверка специалистом',
 'SPECIALIST_REVIEW':'Проверка специалистом','ENGINEERING_SEMANTIC_REVIEW':'Смысловая инженерная проверка',
 'NORMATIVE_CONTENT_REVIEW':'Проверка нормативного содержания','FEATURE_PRESENCE':'Наличие проектного решения',
 'NORMATIVE_CLAUSE':'Требование нормативного пункта','CONFIRMED_BY_AUTHORITATIVE_ROW':'Подтверждено авторитетной строкой',
 'STRUCTURED_CONFLICT':'Структурированное противоречие','STRUCTURED_VALUE':'Структурированное значение',
 'TEXT_OR_TABLE':'Текст или таблица','DRAWING':'Чертёж','CALCULATION':'Расчёт','DOCUMENT':'Документ',
 'EXACT_OBJECT':'Точная привязка к объекту','LOGICAL_ROW_LOCKED':'Логическая привязка к строке',
 'SPECIALIZED_DETERMINISTIC_CHECKER':'Специализированная детерминированная проверка',
 'CANDIDATE_EVIDENCE_ONLY':'Только кандидат в доказательства',
 'INDEPENDENT_AI_CONSENSUS_PLUS_CODE_GATE':'Независимый AI-консенсус и программный контроль',
 'SEMANTIC_EVIDENCE_CONSENSUS_V1':'Смысловой консенсус доказательств',
 'ATOMIC_PATTERN_PRESENCE':'Проверка локального набора признаков','STRUCTURED_COMPARISON':'Структурированное сравнение',
 'PROHIBITION_EXPLICIT_CONTRADICTION':'Проверка явного нарушения запрета','CLAUSE_ADDRESSED_NORMATIVE_CHECK':'Проверка адресного нормативного пункта',
 'SPECIALIST_DECISION_REQUIRED':'Требуется решение специалиста',
 'SEMANTIC_CONSENSUS_SATISFIED':'Независимый смысловой консенсус подтверждён',
 'AI_CONSENSUS_CANDIDATE':'AI-кандидат, ожидающий независимого подтверждения',
 'OTHER_ENTITY':'Другая сущность','OTHER_METRIC':'Другой показатель','INSUFFICIENT':'Недостаточно доказательств',
 'NUMERIC_VALUE_COMPARISON':'Сверка числового значения','EQUIPMENT_IDENTITY':'Идентификация оборудования',
 'DUST_CONCENTRATION':'Концентрация пыли','FREQUENCY':'Частота','CARRY_CAPACITY':'Грузоподъёмность',
 'BUCKET_VOLUME':'Объём ковша','BODY_VOLUME':'Объём кузова','LINE_COUNT':'Количество линий',
 'EQ':'Равно (=)','NE':'Не равно (≠)','GE':'Не менее (≥)','GT':'Более (>)',
 'LE':'Не более (≤)','LT':'Менее (<)','BETWEEN':'Диапазон',
 'EXPLICIT_PROHIBITION':'Явный запрет','APPLICABILITY':'Применимость требования',
 'SEMANTIC_PROJECT_DECISION':'Смысловое проектное решение',
 'L0':'L0 — доказательство не найдено','L1':'L1 — найден кандидат','L2':'L2 — адресный кандидат',
 'L3':'L3 — частично заполнен контракт','L4':'L4 — пакет готов к независимой проверке','L5':'L5 — строгая проверка завершена',
 'VERIFIED_OK':'Соответствует','PROJECT_FINDING':'Выявлено несоответствие','REVIEW_QUESTION':'Требует проверки специалистом',
 'CELL_TABLE':'Ячейка таблицы','TABLE_CELL':'Ячейка таблицы','GEOMETRIC_FALLBACK':'Геометрическое восстановление','TEXT_FALLBACK':'Текстовое восстановление',

 'TABLE_CELL_LOCKED':'Ячейка таблицы восстановлена и зафиксирована',
 'VERIFIED_SET_EVIDENCE':'Подтверждённое доказательство состава',
 'SYSTEM_LIMITATION':'Ограничение автоматической проверки','PROJECT_FINDING':'Проблема проекта','REVIEW_QUESTION':'Вопрос специалисту','INFORMATIONAL':'Информация','PROJECT_STATUS':'Статус проекта',
 'SEMANTIC_CONTRACT_MATCH':'Смысловое сопоставление с контрактом доказательства',
 'DIRECTED_VALUE':'Направленно найденное числовое доказательство','REQUIREMENT_DIRECTED_TEXT':'Направленный поиск по требованию',
 'building_footprint':'Площадь застройки здания','room_area':'Площадь помещения','room_schedule_sum':'Сумма площадей помещений по экспликации','site_area':'Площадь площадки','equipment_metric':'Показатель оборудования',
 'MINSTROY':'Минстрой России','VERIFIED_OFFICIAL_SOURCE':'Официальный источник подтверждён','SOURCE_CURATION_REQUIRED':'Требуется проверка официального источника','CURATION_REQUIRED':'Требуется кураторская проверка пункта','VERIFIED_CLAUSE':'Пункт верифицирован',
 'coverage_status':'Статус покрытия','project_risk_applicable':'Применимость риска к проекту','canonical_id':'Канонический идентификатор','official_source':'Официальный источник','official_source_kind':'Тип официального источника','verified_on':'Дата проверки','verified_revision':'Проверенная редакция','replacement':'Заменяющий документ','effective_until':'Действует до','impact_risk':'Влияние на проект','table_title':'Наименование таблицы','table_row':'Строка таблицы','explanation':'Пояснение','reference':'Нормативная ссылка',
 'AUTOMATED_COMPLETE':'Проверено автоматически','PROJECT_FINDING_CONFIRMED':'Подтверждена проблема проекта','TARGETED_REVIEW':'Адресный вопрос специалисту','AUTOMATION_GAP':'Граница автоматизации',
 'INDEPENDENT_SEMANTIC_CONFIRMATION_REQUIRED':'Требуется независимое смысловое подтверждение',
 'EVIDENCE_CONTRACT_SATISFIED':'Контракт доказательства выполнен','EXPLICIT_CONTRADICTION_CONFIRMED':'Подтверждено явное противоречие','RECIPE_NOT_EXECUTABLE':'Нет исполняемого проверочного рецепта','NO_ADDRESSABLE_EVIDENCE':'Нет адресуемого доказательства','WRONG_EVIDENCE_MODALITY':'Доказательство найдено не в требуемой форме','CRITICAL_QUALIFIER_MISSING':'Не подтверждено существенное условие','SAME_CLAUSE_NOT_PROVED':'Условия не подтверждены одним локальным фрагментом','ENTITY_BINDING_UNRESOLVED':'Не определён владелец показателя','UNIT_INCOMPATIBLE':'Несовместимые единицы измерения','EVIDENCE_CONTRACT_UNSATISFIED':'Контракт доказательства не выполнен','ADVERSARIAL_OR_SEMANTIC_GATE_BLOCKED':'Вывод заблокирован контрольной проверкой','NEEDS_SPECIALIST_JUDGEMENT':'Требуется инженерное суждение','INDEPENDENT_SEMANTIC_CONFIRMATION':'Независимое смысловое подтверждение',
 'SOURCE_DOCUMENT':'Исходный документ','PAGE':'Страница','SECTION':'Раздел','PROJECT_SCOPE':'Область проекта','ENTITY_BINDING':'Привязка к сущности','OBSERVED_VALUE':'Наблюдаемое значение','UNIT':'Единица измерения','PROJECT_ACTION_MARKER':'Маркер проектного решения','PATTERN_EVIDENCE_GROUPS':'Группы признаков доказательства',
 'EXECUTABLE_RECIPE':'Исполняемый проверочный рецепт',
 'MATERIAL_PROCESS_SCOPE_REVIEW':'Требуется подтвердить материал и стадию процесса','UNSPECIFIED':'Причина не классифицирована',
 'BLOCKED_UNIT_SEMANTICS':'Заблокировано: единица не соответствует физическому смыслу','MATERIAL_SCOPE_RECONSTRUCTED':'Восстановлена область материала/процесса',
 'NOT_CONFIGURED':'Не настроено','SKIPPED':'Не выполнялось','PAYLOAD_TOO_LARGE':'Пакет превышает допустимый размер',
 'NUMERIC_VALUE':'Числовой показатель','PRESENCE_ARTIFACT':'Наличие документа или материала','DRAWING_CONTENT':'Содержание графической части','DRAWING_EVIDENCE':'Графическая часть','CALCULATION_ARTIFACT':'Расчёт и его исходные данные','CALCULATION_EVIDENCE':'Расчёты','CROSS_DOCUMENT_CONSISTENCY':'Междокументная согласованность','DOCUMENT_TRACEABILITY':'Прослеживаемость документов','CATEGORICAL_CLASSIFICATION':'Категориальная классификация','IDENTITY_CLASSIFICATION':'Идентификация и классификация','SEMANTIC_DECISION':'Проектное решение','SEMANTIC_PROJECT_DECISION':'Смысловые проектные решения','NORMATIVE_REQUIREMENT':'Нормативное требование','PROHIBITION_DECISION':'Запрет или неприменимость','PROHIBITION':'Запрет или неприменимость','SET_COMPLETENESS':'Полнота состава','OTHER_REQUIREMENT':'Прочее требование',
}

def ru_label(value: Any) -> str:
    if value is None: return '—'
    raw=str(value).strip()
    if not raw: return '—'
    direct=_LABELS.get(raw, _LABELS.get(raw.upper()))
    if direct is not None:return direct
    if ',' in raw:
        parts=[part.strip() for part in raw.split(',')]
        localized=[_LABELS.get(part, _LABELS.get(part.upper(), part)) for part in parts]
        if localized!=parts:return ', '.join(localized)
    return raw

def ru_join(values: Any, sep: str=', ') -> str:
    if isinstance(values,(list,tuple,set)):
        return sep.join(ru_label(x) for x in values)
    return ru_label(values)
