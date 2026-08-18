
"""Import real GGE/GEE remark exports into ExpertCheck knowledge.

No external spreadsheet library is required: OOXML XLSX/DOCX is parsed read-only.
The importer never invents normative references; it stores what the source contains.
"""
from __future__ import annotations
import zipfile, xml.etree.ElementTree as ET, re, hashlib, json
from pathlib import Path

def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def _col(ref):
    m=re.match(r"([A-Z]+)",ref or ""); n=0
    for c in (m.group(1) if m else ""): n=n*26+ord(c)-64
    return n-1
def read_xlsx(path):
    ns="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rid="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(path) as z:
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(ns+"si"):
                shared.append("".join(t.text or "" for t in si.iter(ns+"t")))
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rr=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rels={r.attrib["Id"]:r.attrib["Target"] for r in rr}
        for s in wb.find(ns+"sheets"):
            target=rels[s.attrib[rid]]
            if not target.startswith("xl/"): target="xl/"+target
            root=ET.fromstring(z.read(target.replace("xl//","xl/")))
            rows=[]
            for row in root.iter(ns+"row"):
                cells={}
                for c in row.findall(ns+"c"):
                    idx=_col(c.attrib.get("r","")); typ=c.attrib.get("t"); v=c.find(ns+"v"); val=""
                    if typ=="inlineStr":
                        x=c.find(ns+"is"); val="".join(t.text or "" for t in x.iter(ns+"t")) if x is not None else ""
                    elif v is not None:
                        raw=v.text or ""
                        val=shared[int(raw)] if typ=="s" and raw.isdigit() and int(raw)<len(shared) else raw
                    cells[idx]=val
                if cells: rows.append([cells.get(i,"") for i in range(max(cells)+1)])
            yield s.attrib["name"],rows
