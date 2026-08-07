from __future__ import annotations
from typing import Any
from .normalization import normalize_text

# Baseline content map used as an internal pre-expertise control matrix.
# It is deliberately conservative: absence creates a review flag, not a legal conclusion.
PP87_BASELINE: dict[str, list[dict[str, Any]]] = {
    'ПЗ': [
        {'id':'PP87-PZ-01','question':'Сведения о составе проектируемого объекта и основных проектных решениях','terms':['состав','объект','проектируем']},
        {'id':'PP87-PZ-02','question':'Основные технико-экономические показатели','terms':['технико-эконом','показател']},
        {'id':'PP87-PZ-03','question':'Исходные данные и условия для подготовки проектной документации','terms':['исходн данн','техническ услов','задани']},
    ],
    'ПЗУ': [
        {'id':'PP87-PZU-01','question':'Экспликация проектируемых зданий и сооружений / состав объектов на плане','terms':['экспликац','проектируем','сооружен']},
        {'id':'PP87-PZU-02','question':'Обоснование планировочной организации и размещения объектов','terms':['планировоч','размещен','обоснован']},
        {'id':'PP87-PZU-03','question':'Организация рельефа, водоотвод и решения по территории','terms':['рельеф','водоотвод','поверхностн сток']},
    ],
    'АР': [
        {'id':'PP87-AR-01','question':'Объемно-планировочные и архитектурные решения','terms':['объемно-планиров','архитектурн решен']},
        {'id':'PP87-AR-02','question':'Основные характеристики зданий: площади, высота, этажность','terms':['площад','высот','этаж']},
    ],
    'КР': [
        {'id':'PP87-KR-01','question':'Конструктивная схема и обоснование принятых конструктивных решений','terms':['конструктивн схем','конструктивн решен','обоснован']},
    ],
    'ТХ': [
        {'id':'PP87-TH-01','question':'Описание технологического процесса и основных решений','terms':['технологическ процесс','технологическ решен']},
        {'id':'PP87-TH-02','question':'Производительность, мощность и состав основного оборудования','terms':['производительн','мощност','оборудован']},
        {'id':'PP87-TH-03','question':'Технологические связи и материальные потоки','terms':['технологическ связ','поток','сырь','продукц']},
    ],
    'ПОС': [
        {'id':'PP87-POS-01','question':'Организационно-технологическая последовательность строительства','terms':['последовательн','строительств','организац']},
    ],
    'ПБ': [
        {'id':'PP87-PB-01','question':'Мероприятия по обеспечению пожарной безопасности','terms':['пожарн безопасност','противопожар']},
    ],
    'ООС': [
        {'id':'PP87-OOS-01','question':'Мероприятия по охране окружающей среды','terms':['охрана окружающей среды','воздейств','мероприят']},
    ],
}

def rules_for_section(section: str) -> list[dict[str, Any]]:
    sec=str(section or '').upper()
    if sec.startswith('ИОС'):
        return [{'id':'PP87-IOS-01','question':'Сведения об инженерном оборудовании, сетях и системах и принятых решениях','terms':['инженерн','сеть','систем','оборудован']}]
    return PP87_BASELINE.get(sec, [])

def evaluate_pp87(section: str, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blob=normalize_text(' '.join(' '.join(str(f.get(k) or '') for k in ('context','section_title','table_title','value_text','parameter_name')) for f in findings))
    rows=[]
    for rule in rules_for_section(section):
        matched=[t for t in rule['terms'] if normalize_text(t) in blob]
        # PP87 baseline is deliberately not auto-passed on one weak keyword.
        status='Да' if len(matched)>=min(2,len(rule['terms'])) else ('Требует проверки' if matched else 'Нет')
        rows.append({'item_no':rule['id'],'question':'ПП №87 · '+rule['question'],'status':status,
                     'evidence':'Найдены признаки: '+', '.join(matched) if matched else 'Релевантные сведения автоматически не найдены.',
                     'automation_level':'B','is_heading':False,'source_file':'Контрольная матрица ПП №87','document_types':[section],
                     'compiled_rule':{'rule_type':'pp87_baseline','evidence_terms':rule['terms'],'requires_semantic_review':True}})
    return rows
