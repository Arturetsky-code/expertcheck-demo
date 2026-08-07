from core.engineering_intelligence import looks_like_toc_entry, apply_structure_guards, audit_mandatory_documents
from core.checklist_engine import ChecklistEngine
from core.pp87_matrix import evaluate_pp87


def test_toc_heading_is_blocked():
    ok, reason = looks_like_toc_entry('1.1 Введение')
    assert ok and 'заголовок' in reason


def test_structure_guard_blocks_toc_object_candidate():
    rows=[{'parameter_code':'OBJECT_CANDIDATE','value_text':'1.1 Введение','document':'ПЗ.pdf','page':2}]
    audit=apply_structure_guards(rows)
    assert audit['blocked_toc'] == 1
    assert rows[0]['object_intelligence_decision'] == 'blocked'
    assert rows[0]['trusted_zone'] == 'DOCUMENT_SERVICE'


def test_real_position_is_not_blocked_by_toc_guard():
    ok,_=looks_like_toc_entry('4.13 Здание проборазделки')
    assert not ok


def test_mandatory_document_audit_detects_ocn():
    out=audit_mandatory_documents([{'Файл':'Справка ОКН.pdf','Раздел':'Прочее'}],[])
    assert next(x for x in out if x['code']=='IRD-OCN')['status']=='Найдено'


def test_pp87_baseline_for_pzu():
    rows=evaluate_pp87('ПЗУ',[{'context':'Экспликация проектируемых зданий и сооружений. Организация рельефа и поверхностного стока.'}])
    assert rows
    assert any(x['item_no']=='PP87-PZU-01' for x in rows)
