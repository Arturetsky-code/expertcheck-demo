from pathlib import Path
from core.xml_engine import XmlEngine

ROOT = Path(__file__).resolve().parent

def test_0106():
    p = Path('/mnt/data/Раздел ПД №1_ПЗ.xml')
    if not p.exists(): return
    r = XmlEngine().parse_bytes(p.read_bytes(), p.name)
    assert r.document['XML версия'] == '01.06'
    assert r.document['Шифр']
    assert r.findings

def test_0107():
    p = Path('/mnt/data/97932.xml')
    if not p.exists(): return
    r = XmlEngine().parse_bytes(p.read_bytes(), p.name)
    assert r.document['XML версия'] == '01.07'
    assert 'Крутова' in r.document['ГИП']
    assert r.document['xml_summary']['tei_count'] > 0
