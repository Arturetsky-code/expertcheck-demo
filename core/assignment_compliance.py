from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code, is_parameter_entity_name
from .entity_property_binding import stable_object_id
from .requirement_contracts import build_contract, evidence_packet, SCOPE_PROJECT, SCOPE_SITE, SCOPE_SYSTEM, SCOPE_DOCUMENT, SCOPE_OBJECT, SCOPE_EQUIPMENT
from .object_hierarchy import build_hierarchy, group_is_satisfied
from .directed_evidence import units_compatible
from .evidence_semantics import promote_candidates
from .assignment_verification_kernel import verify_assignment_requirement

ASSIGNMENT_TYPES=("задание на проектирование","техническое задание","тз на проектирование","знп")
REQ_VERBS=("предусмотреть","предусматривается","должен","должна","должны","необходимо","требуется","обеспечить","принять","выполнить","разработать","представить","определить")
PARAMETERS=[
 ("AREA_BUILD",("площадь застройки",),("м²","м2")),
 ("AREA_TOTAL",("общая площадь",),("м²","м2")),
 ("CAPACITY",("производительность","проектная мощность","производственная мощность"),("т/ч","т/год","тыс. т/год","тыс. тонн в год","тыс.тонн/год","м3/ч","м³/ч")),
 ("POWER_INSTALLED",("установленная мощность","мощность","мощностью"),("квт","мвт","ква")),
 ("BODY_VOLUME",("объемом кузова","объёмом кузова","объем кузова","объём кузова"),("м3","м³")),
 ("BUCKET_VOLUME",("объемом ковша","объёмом ковша","объем ковша","объём ковша"),("м3","м³")),
 ("VOLUME",("объем","объём","вместимость"),("м3","м³")),
 ("HEIGHT_BUILD",("высота",),("м",)),
 ("LENGTH",("длина","протяженность","протяжённость"),("м","км")),
 ("FLOW_RATE",("расход",),("м3/ч","м³/ч","л/с")),
 ("QUANTITY",("количество",),("шт","шт.")),
 ("SHIFT_DURATION",("продолжительность смены",),("час","часа","часов","ч")),
]
OBJECT_HINTS=("ктп","кпп","насосная","резервуар","дск","склад","здание","сооружение","дорога","трубопровод","водовод","дамба","хвостохранилище","карта кучного выщелачивания","цех","абк","навес","бункер","ограждение","проезд")

TYPE_VALUE="VALUE_COMPARISON"
TYPE_SET="SET_COMPARISON"
TYPE_TRACE="CROSS_DOCUMENT_TRACE"
TYPE_PRESENCE="PRESENCE_REQUIREMENT"
TYPE_NORMATIVE="NORMATIVE_COMPLIANCE"
TYPE_PROHIBITION="PROHIBITION_OR_NOT_REQUIRED"
TYPE_CALCULATION="CALCULATION_PRESENCE"
TYPE_DRAWING="DRAWING_REQUIREMENT"
TYPE_DESIGN="DESIGN_DETERMINED"
TYPE_SEMANTIC="SEMANTIC_ENGINEERING"


def _assignment_file(name:str,doc_type:str="")->bool:
    blob=normalize_text(name+" "+doc_type)
    return any(x in blob for x in ASSIGNMENT_TYPES)


def _sentences(text:str)->list[str]:
    text=re.sub(r"\s+"," ",str(text or "")).strip()
    parts=re.split(r"(?<=[!?;])\s+|(?<=[а-яА-Я])\.\s+(?=[А-Я])",text)
    return [x.strip() for x in parts if len(x.strip())>=18]


def _plain_atomic_fragments(text:str)->list[dict[str,str]]:
    raw=str(text or "").replace("\r","\n")
    raw=re.sub(r"[ \t]+"," ",raw)
    marked=re.sub(r"(?<!\d)(\d{1,3})[.)]\s+(?=[А-ЯA-Z])",r"\n@@ROW:\1@@ ",raw)
    chunks=[x.strip() for x in re.split(r"\n+",marked) if x.strip()]
    out=[]
    for chunk in chunks:
        m=re.match(r"@@ROW:(\d+)@@\s*(.*)",chunk,re.S)
        row_no=m.group(1) if m else ""
        body=(m.group(2) if m else chunk).strip()
        if len(body)<10: continue
        for part in _split_requirement_atoms(body):
            out.append({"row_no":row_no,"row_title":"","text":part})
    if not out:
        out=[{"row_no":"","row_title":"","text":x} for x in _sentences(raw)]
    return out


def _lines_from_words(words:list[tuple])->list[dict[str,Any]]:
    """Rebuild stable text lines from PyMuPDF words with coordinates."""
    groups=[]
    for w in sorted(words,key=lambda z:(round(z[1],1),z[0])):
        x0,y0,x1,y1,text,*_=w
        target=None
        for g in groups[-4:]:
            if abs(g["y"]-y0)<=1.8:
                target=g; break
        if target is None:
            target={"y":float(y0),"words":[]};groups.append(target)
        target["words"].append((float(x0),float(y0),float(x1),float(y1),str(text)))
    out=[]
    for g in groups:
        ws=sorted(g["words"],key=lambda z:z[0])
        out.append({"y":g["y"],"text":" ".join(w[4] for w in ws),"words":ws})
    return out


def _join_column(lines:list[dict[str,Any]],x_min:float,x_max:float,y0:float,y1:float)->str:
    parts=[]
    for line in lines:
        if line["y"] < y0-1 or line["y"] >= y1-1:
            continue
        words=[w[4] for w in line["words"] if w[0]>=x_min and w[0]<x_max]
        if words: parts.append(" ".join(words))
    return re.sub(r"\s+"," "," ".join(parts)).strip()




def _table_cells_from_pdf(data:bytes)->list[dict[str,Any]]:
    """Primary Assignment parser: recover real table cells with PyMuPDF find_tables().

    Section divider rows and table headers are kept out of requirement cells. Empty-number
    continuation rows are merged only when they contain right-column content, preventing
    labels such as «Состав объекта» from leaking into the previous requirement.
    """
    try:
        import fitz
        doc=fitz.open(stream=data,filetype="pdf")
    except Exception:
        return []
    result=[]; active=None; section_title=""
    for pidx,page in enumerate(doc):
        low=normalize_text(page.get_text("text") or "")
        if pidx>1 and "приложение 1 к заданию" in low:
            break
        try:
            tables=page.find_tables().tables
        except Exception:
            tables=[]
        for table in tables:
            if getattr(table,'col_count',0) < 3:
                continue
            for raw in table.extract() or []:
                cells=[re.sub(r"\s+"," ",str(x or "")).strip() for x in (list(raw)+["",""])[:3]]
                no,title,content=cells
                nmatch=re.fullmatch(r"\d{1,3}",no)
                # Repeated page header.
                if normalize_text(no).startswith("№") or "перечень данных" in normalize_text(title):
                    continue
                if nmatch:
                    row={"row_no":int(no),"row_title":title,"content":content,"page":pidx+1,"section_title":section_title,"cell_reconstruction":"TABLE_CELL_LOCKED"}
                    result.append(row); active=row
                    continue
                # A one-cell divider such as «Состав объекта» / «Требования к проектным решениям».
                nonempty=[x for x in cells if x]
                if len(nonempty)==1 and not content:
                    section_title=nonempty[0]
                    active=None
                    continue
                # Continuation of a row split across a page: only right-column text is merged.
                if active and content and not no and not title:
                    active["content"]=(active.get("content","")+" "+content).strip()
                elif active and content and not no and title and len(title)<8:
                    active["content"]=(active.get("content","")+" "+content).strip()
    # De-duplicate by row number + normalized cells, preserving page continuations.
    out=[]; seen=set()
    for r in result:
        key=(r['row_no'],normalize_text(r.get('row_title')),normalize_text(r.get('content')))
        if key in seen: continue
        seen.add(key); out.append(r)
    return out


def _layout_rows_from_pdf(data:bytes)->list[dict[str,Any]]:
    """Recover the actual 3-column structure of typical Russian design assignments.

    The previous parser operated on flattened page text. That caused row titles and
    right-column content from adjacent rows to merge. This parser treats the left
    row number as a geometric anchor and reads title/content from their own columns.
    """
    try:
        import fitz
        doc=fitz.open(stream=data,filetype="pdf")
    except Exception:
        return []
    rows=[]
    active=None
    for pidx,page in enumerate(doc):
        page_text=page.get_text("text") or ""
        if pidx>1 and "приложение 1 к заданию" in normalize_text(page_text):
            break
        lines=_lines_from_words(page.get_text("words") or [])
        width=float(page.rect.width)
        split=width*0.46
        number_limit=width*0.17
        starts=[]
        for line in lines:
            nums=[w for w in line["words"] if w[0]<number_limit and re.fullmatch(r"\d{1,3}",w[4])]
            if not nums: continue
            n=min(nums,key=lambda w:w[0])
            # Main table row numbers are on the far left; page numbers/footer are not.
            if n[0] > width*0.18: continue
            no=int(n[4])
            if not 1<=no<=200: continue
            starts.append((float(n[1]),str(no)))
        starts=sorted({(round(y,1),n) for y,n in starts})
        # Continuation before the first numbered row belongs to the previous row.
        if active and starts:
            cont=_join_column(lines,split,width,0,starts[0][0]-3.5)
            if cont:
                active["content"]=(active.get("content","")+" "+cont).strip()
        elif active and not starts:
            cont=_join_column(lines,split,width,0,float(page.rect.height))
            if cont:
                active["content"]=(active.get("content","")+" "+cont).strip()
        for i,(y,no) in enumerate(starts):
            ystart=max(0,y-3.5)
            y1=(starts[i+1][0]-3.5) if i+1<len(starts) else float(page.rect.height)-18
            title=_join_column(lines,number_limit,split,ystart,y1)
            content=_join_column(lines,split,width,ystart,y1)
            # Some row titles begin to the left of number_limit; recover text after the number.
            line_at=min(lines,key=lambda l:abs(l["y"]-y)) if lines else None
            if line_at:
                after=[w[4] for w in line_at["words"] if w[0]>=number_limit and w[0]<split]
                if after and not title: title=" ".join(after)
            row={"row_no":no,"row_title":re.sub(r"\s+"," ",title).strip(),"content":re.sub(r"\s+"," ",content).strip(),"page":pidx+1}
            rows.append(row); active=row
    # Deduplicate impossible duplicates from revisions/headers.
    clean=[]; seen=set()
    for r in rows:
        key=(r["page"],r["row_no"],normalize_text(r["row_title"]),normalize_text(r["content"]))
        if key in seen: continue
        seen.add(key);clean.append(r)
    return clean


def _split_requirement_atoms(text:str)->list[str]:
    body=re.sub(r"\s+"," ",str(text or "")).strip(" ;:")
    if not body:return []
    # Main numbered subclauses in the content column.
    body=re.sub(r"(?<![A-Za-zА-Яа-я0-9])(\d{1,2})\.\s+(?=[А-ЯA-Z])",r"\n@@SUB:\1@@ ",body)
    body=re.sub(r"(?<=[.!?])\s+(?=(?:предусмотреть|предусматривается|выполнить|принять|разработать|обеспечить|определить|должен|должна|должны|необходимо|требуется)\b)","\n",body,flags=re.I)
    # Explicit bullet dashes after colon/semicolon or at the beginning.
    body=re.sub(r"(?:(?<=:)|(?<=;)|^)\s*[-–—]\s+(?=[А-Яа-яA-Za-z])",r"\n@@BULLET@@ ",body)
    pieces=[p.strip() for p in body.split("\n") if p.strip()]
    out=[]
    for piece in pieces:
        piece=re.sub(r"^@@(?:SUB:\d+|BULLET)@@\s*","",piece).strip(" ;:-")
        # Semicolon is a safe atom boundary when both sides are full obligations.
        semi=re.split(r";\s+(?=(?:предусмотреть|выполнить|принять|разработать|обеспечить|определить|не требуется|требования отсутствуют)\b)",piece,flags=re.I)
        for s in semi:
            s=re.sub(r"\s+"," ",s).strip(" .;:-")
            if len(s)>=8: out.append(s)
    return out or [body]


def _object_name(sentence:str,parent_title:str="")->str:
    low=normalize_text(sentence)
    # Preserve explicit equipment subjects so numeric values are not compared with
    # unrelated project-wide VOLUME/CAPACITY facts.
    explicit=(
        (r"автосамосвал(?:ами|ы|а)?\s+([A-Za-zА-Яа-я0-9-]+)","Автосамосвал {}"),
        (r"погрузчик(?:ами|и|а)?\s+([A-Za-zА-Яа-я0-9-]+(?:\s+[A-Za-zА-Яа-я0-9-Сс-]+)?)","Погрузчик {}"),
    )
    for pat,fmt in explicit:
        m=re.search(pat,sentence,re.I)
        if m:return fmt.format(m.group(1)).strip()
    if "дробильно-сортировоч" in low or re.search(r"\bдск\b",low): return "ДСК"
    for token in sorted(OBJECT_HINTS,key=len,reverse=True):
        if token in low:
            return token.upper() if token in {"ктп","кпп","дск","абк"} else token.capitalize()
    parent=normalize_text(parent_title)
    if "технологическ" in parent and any(x in low for x in ("производительност","дробильн")): return "ДСК"
    return ""


def _parameter(sentence:str):
    low=normalize_text(sentence)
    unit_re=r"м²|м2|м³|м3|квт|мвт|ква|т/ч|т/год|тыс\.?\s*т(?:онн)?(?:/|\s+в\s+)год|м3/ч|м³/ч|л/с|км|м|шт\.?|час(?:а|ов)?|ч"
    for code,aliases,units in PARAMETERS:
        if not any(a in low for a in aliases): continue
        # Prefer a value following the matched metric phrase, not any number in the sentence.
        positions=[low.find(a) for a in aliases if a in low]
        start=min(p for p in positions if p>=0)
        tail=low[start:start+180]
        m=re.search(rf"(?<!\d)(\d[\d ]*(?:[.,]\d+)?)\s*({unit_re})\b",tail,re.I)
        if m:
            value=float(m.group(1).replace(" ","").replace(",","."))
            return code,value,m.group(2)
        return code,None,""
    m=re.search(r"(?<!\d)(\d[\d ]*(?:[.,]\d+)?)\s*(т/ч|тыс\.?\s*т(?:онн)?(?:/|\s+в\s+)год)\b",low,re.I)
    if m and ("дск" in low or "дробильно-сортировоч" in low):
        return "CAPACITY",float(m.group(1).replace(" ","").replace(",",".")),m.group(2)
    return "",None,""


def _requirement_type(text:str,row_title:str,code:str,value:float|None)->str:
    low=normalize_text(text); title=normalize_text(row_title)
    both=f"{title} {low}"
    if ("состав объект" in both and "приложен" in low) or ("идентификацион" in title and "приложен" in low): return TYPE_SET
    if "инженерн" in low and ("изыскан" in low or "согласно" in low): return TYPE_TRACE
    if any(x in low for x in ("не требуется","требования отсутствуют","не предусматривать")): return TYPE_PROHIBITION
    if "расчет" in low or "расчёт" in low: return TYPE_CALCULATION
    if any(x in low for x in ("графическ","на чертеже","нанести","показать на")): return TYPE_DRAWING
    if re.search(r"\b(?:сп|гост|снип|фз|постановлен)\b",low) or "нормативн" in low: return TYPE_NORMATIVE
    if code and value is not None: return TYPE_VALUE
    if "определить проект" in low: return TYPE_DESIGN
    if any(v in low for v in REQ_VERBS): return TYPE_PRESENCE
    return TYPE_SEMANTIC


def _extract_appendix_objects(data:bytes)->list[dict[str,Any]]:
    """Extract expected object names from Appendix 1 when its table is present."""
    try:
        import fitz
        doc=fitz.open(stream=data,filetype="pdf")
    except Exception:return []
    result=[];seen=set(); appendix=False
    for i,page in enumerate(doc):
        text=page.get_text("text") or ""
        low=normalize_text(text)
        if "приложение 1" in low and ("идентификацион" in low or "позиция по генплану" in low): appendix=True
        if not appendix: continue
        # Use words/lines: GP position is normally followed by the object name in the table.
        lines=[re.sub(r"\s+"," ",x).strip() for x in text.splitlines() if x.strip()]
        for idx,line in enumerate(lines):
            m=re.fullmatch(r"(\d{1,3}(?:\.\d{1,3}){1,4})",line)
            if not m: continue
            pos=m.group(1); name=""
            for cand in lines[idx+1:idx+7]:
                cl=normalize_text(cand)
                if re.match(r"^\d{2}\.\d{2}\.\d{3}",cand): break
                if len(cand)>=4 and not re.fullmatch(r"\d+",cand):
                    name=cand;break
            if name:
                key=(pos,normalize_text(name))
                if key not in seen:
                    seen.add(key);result.append({"position":pos,"name":name,"page":i+1})
    return result


def extract_requirements(files,reader,page_corpus:list[dict[str,Any]]|None=None)->list[dict[str,Any]]:
    """Extract Assignment requirements without rereading the whole project twice.

    The pipeline already builds a page corpus for every PDF.  Reusing it here keeps
    the Assignment stage bounded on large packages; only the actual Assignment PDF
    is reopened for its table/layout parser.
    """
    rows=[];seen=set()
    cached_pages:dict[str,list[tuple[int,str]]]={}
    for page in page_corpus or []:
        document=str(page.get("document") or "")
        text=str(page.get("text") or "")
        if document and text:
            cached_pages.setdefault(document,[]).append((page.get("page") or 0,text))
    for f in files or []:
        name=str(getattr(f,"name","")); doc_type=str(getattr(f,"declared_document_type","") or "")
        data=None
        pages=list(cached_pages.get(name) or [])
        if not pages:
            try:
                data=f.getvalue() if hasattr(f,"getvalue") else f.read()
                pages=reader(data,name)
            except Exception: continue
        first=" ".join(t for _,t in pages[:2])
        if not (_assignment_file(name,doc_type) or any(x in normalize_text(first) for x in ASSIGNMENT_TYPES)): continue
        if data is None:
            try:
                data=f.getvalue() if hasattr(f,"getvalue") else f.read()
            except Exception:
                data=b""
        structured=_table_cells_from_pdf(data) or _layout_rows_from_pdf(data)
        appendix_objects=_extract_appendix_objects(data)
        atoms=[]
        if structured:
            for sr in structured:
                for part in _split_requirement_atoms(sr.get("content") or ""):
                    atoms.append({"row_no":sr["row_no"],"row_title":sr.get("row_title","")[:350],"section_title":sr.get("section_title","")[:350],"text":part,"page":sr.get("page"),"cell_reconstruction":sr.get("cell_reconstruction","")})
        else:
            for page,text in pages:
                for atom in _plain_atomic_fragments(text): atoms.append({**atom,"page":page})
        for atom in atoms:
            sentence=atom["text"]; low=normalize_text(sentence); title=atom.get("row_title") or ""
            obj=_object_name(sentence,title); code,value,unit=_parameter(sentence)
            req_type=_requirement_type(sentence,title,code,value)
            has_requirement_verb=any(v in low for v in REQ_VERBS)
            if low in {"проектом предусмотреть","предусмотреть","выполнить","принять","необходимо выполнить"}:
                continue
            # Titles/status labels without an actual right-column requirement are excluded.
            if not (has_requirement_verb or req_type in {TYPE_VALUE,TYPE_SET,TYPE_TRACE,TYPE_PROHIBITION,TYPE_NORMATIVE,TYPE_DESIGN}):
                continue
            key=(str(atom.get("row_no") or ""),normalize_text(sentence))
            if key in seen: continue
            seen.add(key)
            rid="ASSIGN-"+hashlib.blake2b(f"{name}|{atom.get('page')}|{atom.get('row_no')}|{key}".encode(),digest_size=7).hexdigest().upper()
            item={
              "requirement_id":rid,"source_document":name,"page":atom.get("page"),"source_row":atom.get("row_no") or "",
              "source_row_title":title,"requirement_text":sentence[:1800],"object_name":obj,
              "object_id":stable_object_id(obj) if obj else "","parameter_code":canonical_parameter_code(code),
              "required_value":value,"unit":unit,"requirement_type":req_type,"atomic":True,
              "confidence":0.98 if atom.get("cell_reconstruction")=="TABLE_CELL_LOCKED" else 0.96 if structured and req_type==TYPE_VALUE else 0.92 if structured else 0.68,
              "expected_evidence":_expected_evidence(req_type,title,sentence),
              "source_section":atom.get("section_title") or "",
              "cell_reconstruction":atom.get("cell_reconstruction") or ("GEOMETRIC_ROW" if structured else "TEXT_FALLBACK"),
            }
            item["evidence_contract_v2"]=build_contract(item)
            item["requirement_scope"]=item["evidence_contract_v2"].get("scope")
            if req_type==TYPE_SET and appendix_objects:
                item["expected_objects"]=[dict(x) for x in appendix_objects]
            rows.append(item)
    return rows


def _expected_evidence(req_type:str,title:str,text:str)->str:
    if req_type==TYPE_VALUE:return "Структурированное значение того же показателя для того же объекта/сущности."
    if req_type==TYPE_SET:return "Перечень объектов проекта и перечень объектов из указанного приложения к Заданию."
    if req_type==TYPE_TRACE:return "Прослеживаемая цепочка: исходные изыскания → принятое проектное значение/решение."
    if req_type==TYPE_NORMATIVE:return "Конкретный применимый пункт НТД и проектное доказательство его выполнения."
    if req_type==TYPE_CALCULATION:return "Расчёт/отчёт с идентифицируемым результатом и исходными данными."
    if req_type==TYPE_DRAWING:return "Конкретный лист/графическое доказательство."
    if req_type==TYPE_PROHIBITION:return "Подтверждение отсутствия/неприменимости решения в требуемом контуре."
    return "Конкретное проектное решение с документом и страницей/листом."


def _semantic_tokens(text:str)->set[str]:
    stop={"предусмотреть","предусматривается","должен","должна","должны","необходимо","требуется","обеспечить","принять","выполнить","разработать","представить","проект","проектом","проектной","документации","объект","объекта","сведения","решения"}
    words=set(re.findall(r"[а-яa-z0-9-]{4,}",normalize_text(text),re.I))
    return {w for w in words if w not in stop}


def _semantic_evidence_candidates(requirement:str,findings:list[dict[str,Any]],object_name:str="",limit:int=6)->list[dict[str,Any]]:
    q=_semantic_tokens(requirement);obj=normalize_text(object_name);ranked=[]
    for f in findings:
        blob=" ".join(str(f.get(k) or "") for k in ("context","section_title","table_title","table_evidence","value_text","parameter_name","object_hint","semantic_anchor_name"))
        overlap=q&_semantic_tokens(blob)
        if not overlap:continue
        score=len(overlap)*3;fobj=normalize_text(f.get("semantic_anchor_name") or f.get("object_hint") or "")
        if obj:
            if obj in fobj or fobj in obj:score+=7
            elif fobj and not is_parameter_entity_name(fobj):score-=2
        if f.get("page"):score+=1
        if f.get("value") is not None:score+=1
        if score>=5:ranked.append((score,f,sorted(overlap)))
    ranked.sort(key=lambda x:x[0],reverse=True)
    return [{"score":s,"document":f.get("document"),"page":f.get("page"),"object":f.get("semantic_anchor_name") or f.get("object_hint") or "","parameter":f.get("parameter_name") or "","value_text":f.get("value_text") or "","context":str(f.get("context") or f.get("table_evidence") or "")[:500],"matched_terms":terms} for s,f,terms in ranked[:limit]]


def _registry_object_matches(object_name:str,registry:list[dict[str,Any]])->list[dict[str,Any]]:
    q=normalize_text(object_name)
    if not q:return []
    qwords=_semantic_tokens(q);scored=[]
    for r in registry:
        name=str(r.get("name") or r.get("object_name") or r.get("Наименование") or r.get("Наименование объекта") or "");n=normalize_text(name)
        if not n or is_parameter_entity_name(name):continue
        if q==n:score=100
        elif q in n or n in q:score=90
        else:
            nw=_semantic_tokens(n); inter=qwords&nw;score=round(100*len(inter)/max(1,len(qwords|nw))) if inter else 0
        if score>=70:scored.append((score,r,name))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{"score":s,"name":n,"row":r} for s,r,n in scored[:5]]


def _set_compare(req:dict[str,Any],registry:list[dict[str,Any]])->tuple[str,list[str],str,float]:
    expected=req.get("expected_objects") or []
    if not expected:
        return "Не проверено системой",[],"В Задании есть ссылка на состав объектов, но приложение не удалось структурировать.",0.0
    actual=[]
    hierarchy=build_hierarchy(registry)
    for r in registry:
        name=str(r.get("Наименование объекта") or r.get("name") or r.get("object_name") or "").strip()
        pos=str(r.get("Позиция по ГП") or r.get("position") or "").strip()
        if name:actual.append((pos,name))
    missing=[];evidence=[]
    for exp in expected:
        pos=normalize_text(exp.get("position") or ""); name=str(exp.get("name") or "")
        matches=[a for a in actual if (pos and normalize_text(a[0])==pos) or normalize_text(name) in normalize_text(a[1]) or normalize_text(a[1]) in normalize_text(name)]
        if matches:
            evidence.append(f"Требуется: {exp.get('position')} {name} → найдено: {matches[0][0]} {matches[0][1]}")
        elif pos and group_is_satisfied(pos,hierarchy):
            children=(hierarchy.get('nodes') or {}).get(pos,{}).get('children') or []
            evidence.append(f"Требуется: {exp.get('position')} {name} → подтверждено дочерними позициями: {', '.join(children[:8])}")
        else:
            missing.append(f"{exp.get('position')} {name}".strip())
    if missing:
        return "Требует проверки",evidence+["Не сопоставлены: "+"; ".join(missing[:12])],"Состав объектов сопоставлен по позициям/наименованиям; часть обязательных позиций не подтверждена.",0.92
    return "Соответствует заданию",evidence[:12],"Все структурированные позиции приложения сопоставлены с реестром объектов проекта.",0.96


def compare_requirements(requirements:list[dict[str,Any]],findings:list[dict[str,Any]],registry:list[dict[str,Any]]|None=None,page_corpus:list[dict[str,Any]]|None=None)->list[dict[str,Any]]:
    """Typed, conservative Assignment Compliance Engine.

    A numeric mismatch is allowed only when the requirement identifies the same
    engineering entity. Semantic resemblance can raise a review question but never
    create an automatic deviation.
    """
    registry=registry or [];out=[]
    for req in requirements:
        obj=str(req.get("object_name") or ""); obj_norm=normalize_text(obj);code=canonical_parameter_code(req.get("parameter_code"));rtype=req.get("requirement_type") or TYPE_SEMANTIC
        contract=req.get("evidence_contract_v2") or build_contract(req); scope=contract.get("scope")
        if rtype=="NUMERIC": rtype=TYPE_VALUE
        elif rtype=="OBJECT": rtype=TYPE_PRESENCE
        elif rtype=="SEMANTIC": rtype=TYPE_SEMANTIC
        status="Не проверено системой";evidence=[];candidates=[];difference=None;confidence=0.0;basis=""
        kernel_result=verify_assignment_requirement(req,page_corpus or []) if page_corpus else None
        if kernel_result:
            status=kernel_result['status'];evidence=list(kernel_result.get('evidence') or []);candidates=list(kernel_result.get('evidence_candidates') or [])
            difference=kernel_result.get('difference');confidence=float(kernel_result.get('match_confidence') or 0);basis=str(kernel_result.get('decision_basis') or '')
        elif rtype==TYPE_SET:
            status,evidence,basis,confidence=_set_compare(req,registry)
        elif rtype==TYPE_VALUE and code:
            directed=promote_candidates(req, list(req.get('directed_evidence_candidates') or []))
            # Critical quality gate: a value without an identifiable owner/subject is
            # not compared against arbitrary project facts with the same metric code.
            if not obj_norm and scope in {SCOPE_OBJECT,SCOPE_EQUIPMENT}:
                status="Требует проверки";basis="Числовое требование относится к конкретной сущности, но её владелец не установлен; автоматическое сравнение запрещено."
            else:
                numeric=[]
                verified=[]
                for d in directed:
                    if canonical_parameter_code(d.get('parameter_code'))!=code: continue
                    if str(d.get('evidence_state') or '')!='verified_candidate': continue
                    if req.get('unit') and not units_compatible(req.get('unit'),d.get('unit'),code): continue
                    try: val=float(d.get('value'))
                    except Exception: continue
                    pseudo={
                        'document':d.get('document'),'page':d.get('page'),'semantic_anchor_name':obj or ('Проект' if scope==SCOPE_PROJECT else ''),
                        'object_hint':obj,'parameter_name':code,'parameter_code':code,'unit':d.get('unit'),'context':d.get('context'),
                        'directed_evidence':True,'evidence_quality_decision':'VERIFIED','fact_admission_decision':'ADMIT'
                    }
                    numeric.append((val,pseudo)); verified.append(d)
                expected_sections=[normalize_text(x) for x in contract.get("expected_sections") or []]
                for f in findings:
                    if canonical_parameter_code(f.get("parameter_code"))!=code:continue
                    fobj=str(f.get("semantic_anchor_name") or f.get("object_hint") or "");fn=normalize_text(fobj)
                    if scope in {SCOPE_OBJECT,SCOPE_EQUIPMENT}:
                        if not fn or is_parameter_entity_name(fobj):continue
                        if not (obj_norm==fn or obj_norm in fn or fn in obj_norm):continue
                    section=normalize_text(f.get("document_type") or f.get("section_family") or f.get("section") or "")
                    if expected_sections and section and not any(x in section or section in x for x in expected_sections):continue
                    if (f.get("entity_property_binding") or {}).get("valid") is False:continue
                    if str(f.get("fact_admission_decision") or "ADMIT").upper() in {"HOLD","REJECT"}:continue
                    if req.get('unit') and f.get('unit') and not units_compatible(req.get('unit'),f.get('unit'),code):continue
                    try:val=float(str(f.get("value")).replace(",","."))
                    except Exception:continue
                    numeric.append((val,f))
                if not numeric:
                    if req.get("evidence_contract_v2"):
                        status="Не проверено системой";basis="Структурированное значение по контракту доказательств не найдено. Это является пробелом автоматического покрытия, а не доказательством невыполнения требования."
                    else:
                        status="Требование не подтверждено";basis="Для того же объекта/сущности и показателя структурированное значение в ПД не найдено. Это не доказывает невыполнение требования."
                else:
                    required=float(req["required_value"]);same=[(v,f) for v,f in numeric if math.isclose(v,required,rel_tol=.002,abs_tol=.05)]
                    if same:
                        status="Соответствует заданию";confidence=.96;basis="Совпало структурированное значение для той же инженерной сущности и показателя."
                        evidence=[f"{f.get('document')}, стр. {f.get('page')}: {f.get('semantic_anchor_name') or f.get('object_hint')} · {f.get('parameter_name')} — {v:g} {f.get('unit') or ''}" for v,f in same[:5]]
                    else:
                        status="Выявлено отклонение";confidence=.92;difference=min(abs(v-required) for v,_ in numeric);basis="Для той же инженерной сущности и показателя найдены иные числовые значения."
                        evidence=[f"{f.get('document')}, стр. {f.get('page')}: {f.get('semantic_anchor_name') or f.get('object_hint')} · {f.get('parameter_name')} — {v:g} {f.get('unit') or ''}" for v,f in numeric[:5]]
        elif rtype==TYPE_PROHIBITION:
            status="Требует проверки";basis="Отрицательное/неприменимое требование нельзя подтвердить простым отсутствием текста; требуется проверка контура применимости."
        elif rtype in {TYPE_TRACE,TYPE_NORMATIVE,TYPE_CALCULATION,TYPE_DRAWING,TYPE_PRESENCE,TYPE_DESIGN,TYPE_SEMANTIC}:
            candidates=_semantic_evidence_candidates(str(req.get("requirement_text") or ""),findings,obj,limit=6)
            if candidates:
                status="Требуется смысловая проверка";confidence=min(.72,(candidates[0]["score"] or 0)/20);basis=f"Найдены смыслово связанные фрагменты, но они не доказывают выполнение требования; требуется специализированная проверка типа {rtype}."
                evidence=[f"{x.get('document')}, стр. {x.get('page')}: {x.get('context') or x.get('value_text')}" for x in candidates[:4]]
            else:
                status="Не проверено системой";basis=f"Для типа {rtype} нет достаточного специализированного алгоритма/доказательств; отсутствие находки не считается невыполнением требования."
        if req.get('directed_evidence_candidates'):
            candidates=list(req.get('directed_evidence_candidates') or []) + list(candidates or [])
        packet=evidence_packet(req,candidates)
        evidence_quality_state=str((kernel_result or {}).get('evidence_quality_state') or ('VERIFIED_SET_EVIDENCE' if rtype==TYPE_SET and status in {'Соответствует заданию','Выявлено отклонение'} and evidence else ('VERIFIED_EVIDENCE' if status in {'Соответствует заданию','Выявлено отклонение'} and evidence else ('CANDIDATE_EVIDENCE' if candidates else 'NO_EVIDENCE'))))
        out.append({**req,"status":status,"evidence":evidence,"evidence_candidates":candidates,"evidence_packet":packet,"evidence_quality_state":evidence_quality_state,"difference":difference,"match_confidence":round(confidence,2),"decision_basis":basis,
                    "verification_evidence":list((kernel_result or {}).get('verification_evidence') or []),"verification_kernel":(kernel_result or {}).get('verification_kernel'),
                    "recommendation":"Синхронизировать проектное решение с Заданием на проектирование." if status=="Выявлено отклонение" else "Проверить требование по указанному контракту доказательств." if status in {"Требует проверки","Требует смысловой проверки","Требуется смысловая проверка"} else "Автоматическая проверка пока недоступна; проверить специалисту." if status=="Не проверено системой" else "Дополнительное действие не требуется."})
    return out


def summary(rows:list[dict[str,Any]])->dict[str,Any]:
    result={"total":len(rows),"compliant":0,"deviation":0,"unconfirmed":0,"semantic":0,"not_checked":0}
    by_type={}; by_scope={}; deterministic_ready=0; ai_ready=0
    for r in rows:
        s=r.get("status")
        if s=="Соответствует заданию":result["compliant"]+=1
        elif s=="Выявлено отклонение":result["deviation"]+=1
        elif s=="Не проверено системой":result["not_checked"]+=1
        elif s=="Требуется смысловая проверка":result["semantic"]+=1
        else:result["unconfirmed"]+=1
        typ=str(r.get("requirement_type") or "UNCLASSIFIED"); by_type[typ]=by_type.get(typ,0)+1
        scope=str(r.get("requirement_scope") or (r.get("evidence_contract_v2") or {}).get("scope") or "UNRESOLVED"); by_scope[scope]=by_scope.get(scope,0)+1
        method=str((r.get("evidence_contract_v2") or {}).get("check_method") or "")
        if method in {"VALUE_COMPARISON","SET_COMPARISON","CALCULATION_PRESENCE"}: deterministic_ready+=1
        if (r.get("evidence_contract_v2") or {}).get("ai_allowed"): ai_ready+=1
    result.update({
      "by_type":by_type,"by_scope":by_scope,"deterministic_ready":deterministic_ready,"ai_ready":ai_ready,
      "automatic_coverage_pct":round(100*(result["compliant"]+result["deviation"])/max(1,len(rows)),1),
      "structured_requirement_pct":round(100*sum(1 for r in rows if r.get("cell_reconstruction")=="TABLE_CELL_LOCKED")/max(1,len(rows)),1),
    })
    return result

# Backward-compatible helper used by the 9.8 regression suite.
def _atomic_fragments(text:str)->list[dict[str,str]]:
    return _plain_atomic_fragments(text)
