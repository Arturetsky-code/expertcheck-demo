from __future__ import annotations
from typing import Any, Iterable
from .normalization import normalize_text

# Current PP 87 structure has separate sections for capital objects and linear
# objects plus special appendices. The profile detector is conservative and
# returns evidence rather than a legal conclusion.
APPENDIX_PROFILES = [
    ('PP87-APP-01','Приложение №1 · Метрополитен',('метрополитен','станция метрополитена')),
    ('PP87-APP-02','Приложение №2 · Автомобильные дороги',('автомобильная дорога','автодорога','дорога общего пользования')),
    ('PP87-APP-03','Приложение №3 · Железные дороги',('железная дорога','железнодорожн')),
    ('PP87-APP-04','Приложение №4 · Линии связи',('линия связи','волс','волоконно-оптическ')),
    ('PP87-APP-05','Приложение №5 · Магистральные трубопроводы',('магистральный трубопровод','магистральн нефтепровод','магистральн газопровод')),
    ('PP87-APP-06','Приложение №6 · Инженерная защита и подготовка территории автомобильных дорог',('инженерная защита','подготовка территории строительства автомобильн')),
    ('PP87-APP-07','Приложение №7 · Добыча и первичная переработка твердых полезных ископаемых',('горнодобывающ','горноперерабатывающ','добыч','карьер','хвостохранилищ','кучн выщелачив','дробильно-сортировоч')),
    ('PP87-APP-08','Приложение №8 · ГТС, образующие водохранилища',('гидротехническ сооружен','водохранилищ','плотина')),
    ('PP87-APP-09','Приложение №9 · Атомные станции',('атомная станция','аэс')),
    ('PP87-APP-10','Приложение №10 · Сети газораспределения/газопотребления до 1,2 МПа',('газораспределен','газопотреблен','газопровод')),
]

LINEAR_TOKENS=('линейный объект','автомобильная дорога','железная дорога','трубопровод','линия связи','линия электропередач','водовод','канализационн коллектор')
PRODUCTION_TOKENS=('производственного назначения','промышленн','горнодобывающ','горноперерабатывающ','технологическ комплекс','цех','завод','фабрик')
NONPRODUCTION_TOKENS=('непроизводственного назначения','жилое','общественное здание','административное здание','образовательн','медицинск')


def detect_pp87_profile(findings: Iterable[dict[str,Any]], documents: Iterable[dict[str,Any]] = ()) -> dict[str,Any]:
    blob = normalize_text(' '.join(
        ' '.join(str(x.get(k) or '') for k in ('value_text','object_hint','context','section_title','table_title','parameter_name','document_type'))
        for x in findings
    ) + ' ' + ' '.join(' '.join(str(d.get(k) or '') for k in ('Файл','Раздел','Тип документа')) for d in documents))
    linear_hits=[t for t in LINEAR_TOKENS if t in blob]
    prod_hits=[t for t in PRODUCTION_TOKENS if t in blob]
    nonprod_hits=[t for t in NONPRODUCTION_TOKENS if t in blob]
    if linear_hits and len(linear_hits) >= max(1, len(prod_hits)):
        profile='Линейный объект'
    elif nonprod_hits and not prod_hits:
        profile='Объект непроизводственного назначения'
    else:
        profile='Объект производственного назначения' if prod_hits else 'Тип требует подтверждения'
    appendices=[]
    for code,title,tokens in APPENDIX_PROFILES:
        hits=[t for t in tokens if t in blob]
        if hits:
            appendices.append({'code':code,'title':title,'evidence':hits[:5]})
    return {'profile':profile,'linear_evidence':linear_hits[:8],'production_evidence':prod_hits[:8],'nonproduction_evidence':nonprod_hits[:8],'appendices':appendices}
