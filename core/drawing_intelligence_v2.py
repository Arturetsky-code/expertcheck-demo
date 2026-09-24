from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Callable

from .normalization import normalize_text
from .checklist_routing import canonical_section

try:
    import fitz  # PyMuPDF
except Exception:  # optional runtime dependency
    fitz = None


_CODE_RE = re.compile(r"([A-ZА-Я0-9][A-ZА-Я0-9._-]{5,}-\d+(?:\.\d+)*-АР\d*)", re.I)
_POSITION_RE = re.compile(r"-(\d+(?:\.\d+)*)-АР\d*$", re.I)
_TITLE_CODE_RE = re.compile(r"([A-ZА-Я0-9][A-ZА-Я0-9._-]{5,}-\d+(?:\.\d+)*-(?:АР|КР)\d*)", re.I)
_TITLE_POSITION_RE = re.compile(r"-(\d+(?:\.\d+)*)-(?:АР|КР)\d*$", re.I)
_AREA_RE = re.compile(r"^([+-]?\d+(?:[.,]\d+)?)\s*(?:м[²2])?$", re.I)
_CATEGORY_RE = re.compile(r"^[А-ЕA-EВГД]\s*\d?[а-яa-z]?$", re.I)
_PERMISSION_RE = re.compile(r"\b\d{2,4}/\d{2}\b")

_SKIP_OBJECT_LINES = {
    "разраб.", "пров.", "нач. отд.", "н. контр.", "гип", "п", "фасады",
    "план 1 этажа", "план кровли", "разрез 1-1",
}


def _clean_lines(text: str) -> list[str]:
    out=[]
    for raw in str(text or "").splitlines():
        line=re.sub(r"\s+", " ", raw.replace("\u00ad", "").replace("\u00a0", " ")).strip()
        if line:
            out.append(line)
    return out


def _float(token: str) -> float | None:
    m=_AREA_RE.match(str(token or "").strip())
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _position(code: str) -> str:
    m=_POSITION_RE.search(str(code or ""))
    return m.group(1) if m else ""


def _drawing_kinds(text: str) -> list[str]:
    low=normalize_text(text)
    kinds=[]
    tests=(
        ("room_explication", "экспликация помещений"),
        ("floor_plan", "план 1 этажа"),
        ("floor_plan", "план на отм"),
        ("roof_plan", "план кровли"),
        ("section_view", "разрез"),
        ("facade", "фасад"),
        ("specification", "спецификац"),
        ("finish_schedule", "ведомость отделки фасада"),
        ("revision", "содержание изменения"),
        ("drawing_index", "ведомость документов графической части"),
    )
    for kind, token in tests:
        if token in low and kind not in kinds:
            kinds.append(kind)
    return kinds or ["drawing"]


_SHEET_TITLE_MARKERS = (
    "фасад", "разрез", "план ", "план.", "схема ", "схемы ",
    "узел ", "узлы ", "ведомость ", "экспликация ", "спецификация ",
)


def _owner_candidate(line: str, *, allow_sheet_title: bool = False) -> str:
    candidate=str(line or "").strip(" .;:-")
    low=normalize_text(candidate)
    if not candidate or low in _SKIP_OBJECT_LINES:
        return ""
    if any(x in low for x in (
        "разраб", "провер", "нач. отд", "н. контр", "главный инженер проекта", "гип",
        "ооо ", "ао ", "пао ", "объект строительства",
    )):
        return ""
    if re.fullmatch(r"\d+",candidate) or _PERMISSION_RE.fullmatch(candidate):
        return ""
    if len(candidate) < 3:
        return ""
    if not allow_sheet_title and any(low.startswith(marker) for marker in _SHEET_TITLE_MARKERS):
        return ""
    return candidate


def parse_title_block(text: str) -> dict[str, Any]:
    """Resolve drawing-sheet ownership from the title block.

    Some CAD/PDF exports place the object name after the designation, while
    others place the sheet title after it and the object name immediately
    before the project/site/company lines.  Sheet titles such as "Фасады",
    "Разрез", "План" and "Схема" must never be promoted to object owners.
    Ambiguous bindings remain withheld.
    """
    lines=_clean_lines(text)
    code_hits=[]
    for i,line in enumerate(lines):
        for m in _TITLE_CODE_RE.finditer(line):
            code_hits.append((i,m.group(1)))
    if not code_hits:
        return {"resolved":False,"reason":"обозначение листа АР не найдено"}

    i,code=code_hits[-1]

    # Preferred layout: designation -> exact object name. If the first
    # semantic row is a drawing title (Scheme/Facade/Plan/Section), do not skip
    # into its wrapped continuation and accidentally bind that as an owner.
    after=[]
    after_is_sheet_title=False
    for j in range(i+1,min(len(lines),i+7)):
        raw_candidate=_owner_candidate(lines[j], allow_sheet_title=True)
        if not raw_candidate:
            continue
        low_candidate=normalize_text(raw_candidate)
        if any(low_candidate.startswith(marker) for marker in _SHEET_TITLE_MARKERS):
            after_is_sheet_title=True
            break
        candidate=_owner_candidate(lines[j])
        if candidate:
            after.append(candidate)
            break
    if len(after)==1 and not after_is_sheet_title:
        owner=after[0]
        method="TITLE_BLOCK_AFTER_DESIGNATION"

    else:
        # Alternate layout seen in CAD title blocks:
        # object -> project/site -> company -> designation -> sheet title.
        # Anchor on the organisation row instead of project-specific wording.
        organisation_index=None
        for j in range(i-1,max(-1,i-7),-1):
            low=normalize_text(lines[j])
            if any(low.startswith(prefix) for prefix in ("ооо ", "ао ", "пао ")):
                organisation_index=j
                break

        owner=""
        if organisation_index is not None and organisation_index-2 >= 0:
            owner=_owner_candidate(lines[organisation_index-2])
        if not owner:
            before=[]
            for j in range(i-1,max(-1,i-10),-1):
                candidate=_owner_candidate(lines[j])
                if candidate:
                    before.append(candidate)
                    break
            owner=before[0] if len(before)==1 else ""

        if not owner:
            return {
                "resolved":False,
                "designation":code,
                "position":(_TITLE_POSITION_RE.search(code).group(1) if _TITLE_POSITION_RE.search(code) else ""),
                "reason":"наименование владельца листа не разрешено однозначно",
            }
        method="TITLE_BLOCK_BEFORE_DESIGNATION"

    return {
        "resolved":True,
        "designation":code,
        "position":(_TITLE_POSITION_RE.search(code).group(1) if _TITLE_POSITION_RE.search(code) else ""),
        "object_name":owner,
        "binding_method":method,
    }


_REQ_POSITION_RE = re.compile(r"(?:поз(?:иция)?\.?\s*)(\d+(?:\.\d+)*)", re.I)
_FACADE_VIEW_RE = re.compile(r"\bфасад\s+([0-9A-ZА-ЯЁ]+\s*[-–—]\s*[0-9A-ZА-ЯЁ]+(?:\s*[;/]\s*[0-9A-ZА-ЯЁ]+\s*[-–—]\s*[0-9A-ZА-ЯЁ]+)?)", re.I)
_ENCLOSURE_MARKERS = (
    "стеновая панель", "панель типа сэндвич", 'панель типа "сэндвич"',
    "сэндвич-панель", "сэндвич панель", "наружная стена", "обшивка стен",
)


def open_canopy_drawing_fact(
    requirement_text: str,
    page_corpus: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return a fail-closed structured drawing fact for an explicitly open canopy.

    The fact is not inferred from the word "навес" or from missing wall text.
    It requires an owner/position-bound AR facade+section sheet with multiple
    facade directions and roof material, independently corroborated by a KR
    open-frame structural sheet (columns/bracing + roof beams/purlins).
    Explicit wall/enclosure markers block the proof.
    """
    req_low=normalize_text(requirement_text)
    if "навес" not in req_low or "открыт" not in req_low:
        return None

    m=_REQ_POSITION_RE.search(str(requirement_text or ""))
    required_position=m.group(1) if m else ""
    ar_hits=[]
    kr_hits=[]

    for page in page_corpus or []:
        section=canonical_section(str(page.get("document_type") or page.get("document") or ""))
        if section not in {"АР","КР"}:
            continue
        raw=str(page.get("text") or "")
        low=normalize_text(raw)
        if "навес" not in low:
            continue
        if "ведомость документов графической части" in low:
            continue
        title=parse_title_block(raw)
        if not title.get("resolved"):
            continue
        position=str(title.get("position") or "")
        if required_position and position != required_position:
            continue
        owner=normalize_text(title.get("object_name") or "")
        if "навес" not in owner:
            continue

        if section=="АР":
            kinds=_drawing_kinds(raw)
            views=tuple(dict.fromkeys(
                re.sub(r"\s+","",x.upper().replace("–","-").replace("—","-"))
                for x in _FACADE_VIEW_RE.findall(raw)
            ))
            roof=any(x in low for x in ("профилированный настил","профнастил","план кровли"))
            conflicts=tuple(marker for marker in _ENCLOSURE_MARKERS if marker in low)
            if (
                "facade" in kinds
                and "section_view" in kinds
                and len(views) >= 3
                and roof
                and not conflicts
            ):
                ar_hits.append({
                    "page":page,
                    "title":title,
                    "facade_views":views,
                    "roof_proven":True,
                    "enclosure_conflicts":conflicts,
                })

        if section=="КР":
            frame=(
                "схема расположения колонн" in low
                and "вертикальных связей" in low
                and "балок и прогонов покрытия" in low
            )
            if frame:
                kr_hits.append({"page":page,"title":title})

    if not ar_hits or not kr_hits:
        return {
            "proven":False,
            "required_position":required_position,
            "ar_facade_semantics":bool(ar_hits),
            "kr_frame_corroboration":bool(kr_hits),
        }

    ar=ar_hits[0]
    kr=kr_hits[0]
    page=ar["page"]
    return {
        "proven":True,
        "fact_code":"OPEN_CANOPY",
        "required_position":required_position,
        "owner_name":ar["title"].get("object_name"),
        "owner_binding":ar["title"].get("binding_method"),
        "document":page.get("document"),
        "document_type":"АР",
        "page":page.get("page"),
        "facade_views":ar["facade_views"],
        "facade_view_count":len(ar["facade_views"]),
        "roof_proven":True,
        "structural_frame_corroborated":True,
        "corroborating_document":kr["page"].get("document"),
        "corroborating_page":kr["page"].get("page"),
        "enclosure_conflict":False,
        "context":"; ".join(
            line for line in _clean_lines(str(page.get("text") or ""))
            if (
                "навес" in normalize_text(line)
                or "фасад" in normalize_text(line)
                or "разрез" in normalize_text(line)
                or "профилированный настил" in normalize_text(line)
                or str(ar["title"].get("designation") or "") in line
            )
        )[:1800],
    }


def parse_room_explication(text: str) -> dict[str, Any] | None:
    lines=_clean_lines(text)
    try:
        start=next(i for i,x in enumerate(lines) if "экспликация помещений" in normalize_text(x))
    except StopIteration:
        return None
    end=next((i for i in range(start+1,len(lines)) if normalize_text(lines[i]).startswith("итого")),None)
    if end is None:
        return {"resolved":False,"rows":[],"reason":"не найдена строка Итого в экспликации помещений"}
    # Data starts after the header. Find the first row number followed later by an area.
    data_start=None
    for i in range(start+1,end):
        if re.fullmatch(r"\d{1,3}",lines[i]):
            if any(_float(lines[j]) is not None for j in range(i+1,min(end,i+8))):
                data_start=i; break
    if data_start is None:
        return {"resolved":False,"rows":[],"reason":"не распознаны строки экспликации помещений"}
    rows=[]; i=data_start
    while i < end:
        if not re.fullmatch(r"\d{1,3}",lines[i]):
            i+=1; continue
        room_no=lines[i]; i+=1
        name_parts=[]; area=None; category=""
        while i < end:
            token=lines[i]
            # Next integer after some content is the next room row.
            if re.fullmatch(r"\d{1,3}",token) and name_parts and area is not None:
                break
            num=_float(token)
            if num is not None and name_parts and area is None:
                area=num; i+=1
                if i < end and _CATEGORY_RE.fullmatch(lines[i]):
                    category=lines[i]; i+=1
                break
            # Skip repeated column headers accidentally interleaved by PDF text order.
            low=normalize_text(token)
            if not any(h in low for h in ("номер", "поме-", "площадь", "наименование", "кат. поме")):
                name_parts.append(token)
            i+=1
        if name_parts and area is not None:
            rows.append({
                "room_no":room_no,
                "room_name":" ".join(name_parts).strip(),
                "area":area,
                "unit":"м²",
                "category":category,
                "metric_code":"AREA_ROOM",
                "metric_scope":"room",
            })
        else:
            # do not invent a row if the table structure is incomplete
            i+=1
    total=None
    for j in range(end,min(len(lines),end+4)):
        num=_float(lines[j].replace("Итого:","").strip())
        if num is not None:
            total=num; break
    calc=round(sum(r["area"] for r in rows),3) if rows else None
    total_match=(total is not None and calc is not None and abs(total-calc) <= 0.11)
    return {
        "resolved":bool(rows),
        "rows":rows,
        "reported_total":total,
        "calculated_total":calc,
        "total_matches_rows":total_match,
        "total_metric_code":"AREA_ROOM_SUM",
        "total_metric_scope":"room_schedule_sum",
        "reason":"" if rows else "строки экспликации не разрешены",
    }


def parse_drawing_index(page_texts: list[tuple[int,str]]) -> list[dict[str,Any]]:
    """Build explicit object -> expected sheet mapping from the drawing index."""
    result=[]
    for page,text in page_texts:
        if "ведомость документов графической части" not in normalize_text(text):
            continue
        lines=_clean_lines(text); current=None
        for i,line in enumerate(lines):
            m=_CODE_RE.search(line)
            if m:
                code=m.group(1)
                # Ignore the index's own designation.
                if code.upper().endswith("АР2-ВДГ"):
                    current=None; continue
                name=""
                for j in range(i+1,min(i+4,len(lines))):
                    cand=lines[j].strip()
                    if cand and not cand.lower().startswith("лист ") and "изм." not in cand.lower() and not _CODE_RE.search(cand):
                        name=cand; break
                current={"designation":code,"position":_position(code),"object_name":name,"index_page":page,"expected_sheets":[]}
                result.append(current)
                continue
            if current and re.match(r"^лист\s+\d+\s*[-–—]",line,re.I):
                current["expected_sheets"].append(line)
    return result


def parse_revision_records(page_texts: list[tuple[int,str]]) -> list[dict[str,Any]]:
    result=[]
    for page,text in page_texts:
        low=normalize_text(text)
        if "содержание изменения" not in low or "разрешение" not in low:
            continue
        # PDF text often wraps document designations after a hyphen. Repair only
        # line-break hyphenation before parsing the revision table.
        repaired=re.sub(r"-\s*\n\s*", "-", str(text or ""))
        lines=_clean_lines(repaired)
        permission=next((m.group(0) for line in lines for m in [_PERMISSION_RE.search(line)] if m),"")
        for i,line in enumerate(lines):
            m=_CODE_RE.search(line)
            if not m: continue
            code=m.group(1)
            if not _position(code):
                continue
            obj=""
            for j in range(i-1,max(-1,i-7),-1):
                cand=lines[j]
                low_c=normalize_text(cand)
                if cand and not re.fullmatch(r"\d+",cand) and low_c not in {"код","примечание","содержание изменения","лист","изм."}:
                    if not _PERMISSION_RE.search(cand):
                        obj=cand; break
            change=[]
            for j in range(i+1,min(len(lines),i+10)):
                cand=lines[j]
                if _CODE_RE.search(cand): break
                # In revision tables the next object's name appears immediately
                # before its designation; do not bleed it into the prior change.
                if j+1 < len(lines) and _CODE_RE.search(lines[j+1]):
                    break
                if _PERMISSION_RE.search(cand): continue
                if re.fullmatch(r"\d+",cand): continue
                low_c=normalize_text(cand)
                if any(x in low_c for x in ("объект строительства", "архитектурно строительный отдел", "согласовано")): break
                if len(cand)>=8: change.append(cand)
            result.append({
                "page":page,"permission":permission,"designation":code,"position":_position(code),
                "object_name":obj,"change":" ".join(change[:3]).strip(),
            })
    return result


def _region_bboxes(pdf_bytes: bytes, page_no: int) -> dict[str, list[float]]:
    """Best-effort physical provenance for key drawing regions."""
    if fitz is None:
        return {}
    try:
        doc=fitz.open(stream=pdf_bytes,filetype="pdf")
        if page_no < 1 or page_no > len(doc): return {}
        page=doc[page_no-1]
        out={}
        for block in page.get_text("blocks"):
            x0,y0,x1,y1,text,*_=block
            low=normalize_text(text)
            if "экспликация помещений" in low:
                out["room_explication"]=[round(x0,1),round(y0,1),round(x1,1),round(y1,1)]
            if "стадия" in low and "лист" in low and "листов" in low:
                out.setdefault("title_block",[round(x0,1),round(y0,1),round(x1,1),round(y1,1)])
        return out
    except Exception:
        return {}


class DrawingIntelligenceV2:
    """Deterministic first layer for drawing understanding.

    AI may later orchestrate these tools, but ownership, schedule rows and
    revision provenance are resolved by explicit parsers. Ambiguous bindings are
    withheld rather than guessed.
    """
    version="2.0-alpha1"

    def extract_uploaded(self, pdf_files, document_types: dict[str,str], read_pdf: Callable) -> dict[str,Any]:
        graph={"version":self.version,"documents":[],"objects":[],"sheets":[],"room_schedules":[],"revisions":[],"withheld":[]}
        object_nodes={}
        for uploaded in pdf_files or []:
            section=canonical_section(document_types.get(uploaded.name,""))
            if section != "АР":
                continue
            try:
                data=uploaded.getvalue(); pages=read_pdf(data,uploaded.name)
            except Exception as exc:
                graph["withheld"].append({"document":getattr(uploaded,"name",""),"reason":str(exc)}); continue
            index=parse_drawing_index(pages)
            revisions=parse_revision_records(pages)
            graph["revisions"].extend([{**r,"document":uploaded.name} for r in revisions])
            graph["documents"].append({"document":uploaded.name,"section":section,"pages":len(pages),"indexed_objects":len(index)})
            for item in index:
                key=item["designation"]
                object_nodes[key]={**item,"document":uploaded.name}
            for page_no,text in pages:
                tb=parse_title_block(text)
                kinds=_drawing_kinds(text)
                if not tb.get("resolved"):
                    # Service/index/revision pages are allowed not to have a child-object owner.
                    if not any(k in kinds for k in ("drawing_index","revision")):
                        graph["withheld"].append({"document":uploaded.name,"page":page_no,"reason":tb.get("reason","владелец листа не определён")})
                    continue
                code=tb["designation"]
                owner=tb["object_name"]
                node=object_nodes.setdefault(code,{"designation":code,"position":tb.get("position",""),"object_name":owner,"document":uploaded.name,"expected_sheets":[]})
                if not node.get("object_name"): node["object_name"]=owner
                regions=_region_bboxes(data,page_no)
                sheet={
                    "document":uploaded.name,"page":page_no,"designation":code,"position":tb.get("position",""),
                    "object_name":owner,"drawing_kinds":kinds,"owner_binding":"TITLE_BLOCK_EXACT",
                    "regions":regions,
                }
                graph["sheets"].append(sheet)
                schedule=parse_room_explication(text)
                if schedule:
                    schedule={**schedule,"document":uploaded.name,"page":page_no,"designation":code,"position":tb.get("position",""),"parent_object":owner,
                              "source_region":"room_explication","bbox":regions.get("room_explication"),"owner_binding":"TITLE_BLOCK_EXACT"}
                    graph["room_schedules"].append(schedule)
            graph["objects"].extend(object_nodes.values())
        # dedupe objects caused by multi-document processing
        dedup={}
        for obj in graph["objects"]:
            dedup[(obj.get("document"),obj.get("designation"))]=obj
        graph["objects"]=list(dedup.values())
        graph["summary"]={
            "documents":len(graph["documents"]),"objects":len(graph["objects"]),"sheets":len(graph["sheets"]),
            "room_schedules":len(graph["room_schedules"]),"rooms":sum(len(x.get("rows") or []) for x in graph["room_schedules"]),
            "revision_records":len(graph["revisions"]),"withheld_bindings":len(graph["withheld"]),
            "principle":"Неоднозначная привязка чертежа или показателя не превращается в инженерный факт.",
        }
        return graph


def drawing_graph_findings(graph: dict[str,Any]) -> list[dict[str,Any]]:
    """Expose room facts as scoped evidence without promoting them to building TEPs."""
    findings=[]
    for sched in graph.get("room_schedules") or []:
        for row in sched.get("rows") or []:
            findings.append({
                "document":sched.get("document"),"page":sched.get("page"),"document_type":"АР",
                "parameter_code":"AREA_ROOM","parameter_name":"Площадь помещения","value":row.get("area"),"value_text":str(row.get("area")),"unit":"м²",
                "object_hint":row.get("room_name"),"parent_object":sched.get("parent_object"),"parent_object_position":sched.get("position"),
                "scope_entity_type":"ROOM","metric_semantic_scope":"room_area","room_no":row.get("room_no"),"room_category":row.get("category"),
                "drawing_kind":"room_explication","drawing_evidence":True,"binding_status":"ROW_LOCKED",
                "match_method":"экспликация помещений: строка таблицы","structural_zone":"Экспликация помещений",
                "source_bbox":sched.get("bbox"),"comparison_excluded":True,"comparison_exclusion_reason":"площадь помещения не является ТЭП здания",
                "confidence":0.98,
            })
        if sched.get("reported_total") is not None:
            findings.append({
                "document":sched.get("document"),"page":sched.get("page"),"document_type":"АР",
                "parameter_code":"AREA_ROOM_SUM","parameter_name":"Сумма площадей помещений по экспликации","value":sched.get("reported_total"),"value_text":str(sched.get("reported_total")),"unit":"м²",
                "object_hint":sched.get("parent_object"),"genplan_position":sched.get("position"),
                "scope_entity_type":"ROOM_SCHEDULE","metric_semantic_scope":"room_schedule_sum","drawing_kind":"room_explication","drawing_evidence":True,
                "binding_status":"ROW_LOCKED","match_method":"экспликация помещений: строка Итого","structural_zone":"Экспликация помещений",
                "source_bbox":sched.get("bbox"),"comparison_excluded":True,"comparison_exclusion_reason":"сумма площадей помещений не приравнивается к общей площади или площади застройки здания",
                "schedule_total_verified":bool(sched.get("total_matches_rows")),"confidence":0.99,
            })
    return findings
