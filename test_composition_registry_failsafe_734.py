from pathlib import Path
from core.general_plan_engine import GeneralPlanRegisterEngine
from core.composition_registry import build_composition_baseline
from core.project_assembly import build_assembly_rows
from core.evidence_registry import build_evidence_index
from core.object_intelligence import build_object_decisions
from core.pz_complex_object_register import extract_pz_complex_object_register_from_uploaded

class Upload:
    def __init__(self,path):
        import io
        self.path=Path(path); self.name=self.path.name; self._buf=io.BytesIO(self.path.read_bytes())
    def getvalue(self): return self.path.read_bytes()
    def read(self,*a,**k): return self._buf.read(*a,**k)
    def seek(self,*a,**k): return self._buf.seek(*a,**k)


def gp_findings(path):
    data=Path(path).read_bytes(); name=Path(path).name
    entries,_=GeneralPlanRegisterEngine().extract_pdf(data,name)
    return [e.to_finding(name) for e in entries]


def test_gp_explication_is_official_object_evidence():
    findings=gp_findings('/mnt/data/2(1).pdf')
    row=next(x for x in findings if x.get('genplan_position')=='2.1.1')
    assert row['trusted_zone']=='OBJECT_REGISTER'
    assert row['object_lifecycle_status']=='Проектируемый'


def test_composition_baseline_keeps_real_gp_objects_even_if_intelligence_blocks():
    findings=gp_findings('/mnt/data/2(1).pdf')
    base,audit=build_composition_baseline([],findings)
    assert audit['baseline_positions'] >= 10
    assert any(r['Позиция по ГП']=='2.1.1' and 'Насосная станция' in r['Наименование объекта'] for r in base)
    fake_intel={f"{r['Позиция по ГП']}|{r['Наименование объекта'].lower()}":{'decision':'blocked','confidence':0,'reason':'fake'} for r in base}
    rows=build_assembly_rows(base,[],{},fake_intel)
    assert len(rows)==len(base)
    assert any(r['Позиция по ГП']=='2.1.1' and r['Включить'] for r in rows)


def test_four_general_plans_build_nonempty_primary_baselines():
    expected_min={'/mnt/data/1(1).pdf':25,'/mnt/data/2(1).pdf':10,'/mnt/data/3(1).pdf':20,'/mnt/data/4(1).pdf':10}
    for path,minimum in expected_min.items():
        f=gp_findings(path)
        base,audit=build_composition_baseline([],f)
        assert len(base)>=minimum,(path,len(base))


def test_pz_and_gp_are_merged_by_position_without_erasing_gp_only_rows():
    pz_path='/mnt/data/Раздел ПД №1_ПЗ(8).pdf'
    pz,audit=extract_pz_complex_object_register_from_uploaded([Upload(pz_path)],{Path(pz_path).name:'ПЗ'})
    gp=gp_findings('/mnt/data/1(1).pdf')
    base,summary=build_composition_baseline(pz,gp)
    assert summary['pz_positions'] >= 30
    assert summary['general_plan_positions'] >= 25
    assert any(r['Позиция по ГП']=='4.13' and r['Наименование объекта']=='Здание проборазделки' for r in base)
    assert any(r['Позиция по ГП']=='4.24' for r in base)  # GP-only equipment remains visible for review/composition decision


def test_generic_text_does_not_need_to_enter_primary_baseline():
    gp=gp_findings('/mnt/data/1(1).pdf')
    base,_=build_composition_baseline([],gp)
    names={r['Наименование объекта'] for r in base}
    assert 'Площадь участка в границах проектирования всего, в т.ч.:' not in names
    assert 'Площадь застройки, всего, в т.ч.:' not in names
