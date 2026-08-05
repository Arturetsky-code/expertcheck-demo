from core.project_assembly import build_assembly_rows, selected_keys, filter_comparisons_by_keys
from core.checklist_engine import ChecklistEngine


def test_manual_assembly_excludes_file_candidate():
    rows=build_assembly_rows(
        [{'Позиция по ГП':'1','Наименование объекта':'Насосная станция'}],
        [{'Наименование объекта':'Раздел ПД № 3_АР2.pdf'}],
    )
    assert rows[0]['Включить'] is True
    assert rows[1]['Включить'] is False


def test_comparisons_only_for_confirmed_objects():
    rows=build_assembly_rows([
        {'Позиция по ГП':'1','Наименование объекта':'Насосная станция'},
        {'Позиция по ГП':'2','Наименование объекта':'КТП'},
    ],[])
    rows[1]['Включить']=False
    out=filter_comparisons_by_keys([
        {'object':'Насосная станция','parameter_name':'Мощность'},
        {'object':'КТП','parameter_name':'Мощность'},
    ],rows,selected_keys(rows))
    assert len(out)==1 and out[0]['object']=='Насосная станция'


def test_checklist_selection_by_section(tmp_path):
    p=tmp_path/'c.json'
    p.write_text('[{"source_file":"GP.xlsx","document_types":["ПЗУ"],"automation_level":"C","question":"Проверить"},{"source_file":"AR.xlsx","document_types":["АР"],"automation_level":"C","question":"Проверить"}]',encoding='utf-8')
    e=ChecklistEngine(p)
    assert e.checklist_files('ПЗУ')==['GP.xlsx']
    assert len(e.evaluate([{'Раздел':'ПЗУ'}],[],[],source_file='GP.xlsx',section='ПЗУ'))==1
