from pathlib import Path
from core.normative_validity import NormativeValidityChecker
from core.normative_verification import NormativeVerificationEngine
ROOT=Path(__file__).parent/'knowledge'

def test_gost_21101_2020_is_replaced_after_april_2026():
    e=NormativeValidityChecker(ROOT)
    x=e.check('ГОСТ Р 21.101-2020',as_of_date='2026-08-19')
    assert x['status']=='Заменён'
    assert x['replacement']=='ГОСТ Р 21.101-2026'
    assert x['edition_assessment']['edition_outdated'] is True
    assert x['edition_assessment']['current_reference']=='ГОСТ Р 21.101-2026'

def test_gost_21101_2026_is_current():
    e=NormativeValidityChecker(ROOT)
    x=e.check('ГОСТ Р 21.101-2026',as_of_date='2026-08-19')
    assert x['status']=='Действует'
    assert x['edition_assessment']['edition_outdated'] is False

def test_sp48_has_change_history():
    e=NormativeValidityChecker(ROOT)
    x=e.check('СП 48.13330.2019')
    assert x['status']=='Действует с изменениями'
    assert len(x.get('changes') or [])>=2

def test_verification_queue_prioritises_pending_p1():
    e=NormativeVerificationEngine(ROOT)
    rows=e.queue(pending_only=True,limit=50)
    assert rows
    assert 'P1' in [x['priority'] for x in rows[:5]]

def test_freshness_is_exposed():
    e=NormativeValidityChecker(ROOT)
    x=e.check('СП 47.13330.2016')
    assert x['verification_freshness']['needs_refresh'] is False
