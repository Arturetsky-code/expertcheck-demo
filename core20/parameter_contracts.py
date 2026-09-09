from __future__ import annotations

from dataclasses import dataclass
from math import isclose
import re
from typing import Any


def norm(value: Any) -> str:
    return " ".join(str(value or "").replace("ё","е").casefold().replace("\xa0"," ").split())


def unit(value: Any) -> str:
    text=norm(value).replace(" ","").replace("²","2").replace("^2","2").replace("³","3")
    annual=text.replace("тонны","тонн").replace("тонна","тонн")
    if re.fullmatch(r"тыс\.?т(?:онн)?(?:/|в)?год",annual):
        return "kt/y"
    if re.fullmatch(r"млн\.?т(?:онн)?(?:/|в)?год",annual):
        return "mt/y"
    if re.fullmatch(r"т(?:онн)?(?:/|в)?год",annual):
        return "t/y"
    aliases={
        "м2":"m2","м.кв.":"m2","кв.м":"m2","m2":"m2",
        "м3":"m3","m3":"m3",
        "мм":"mm","mm":"mm","см":"cm","cm":"cm","м":"m","m":"m","км":"km","km":"km",
        "квт":"kw","kw":"kw","мвт":"mw","mw":"mw","ква":"kva","kva":"kva",
        "па":"pa","кпа":"kpa","мпа":"mpa","mpa":"mpa","bar":"bar","бар":"bar",
        "в":"v","v":"v","кв":"kv","kv":"kv",
        "т/ч":"t/h","тч":"t/h","t/h":"t/h",
        "м3/ч":"m3/h","m3/h":"m3/h","л/с":"l/s",
        "шт":"pcs","шт.":"pcs","pcs":"pcs",
        "чел":"person","чел.":"person",
        "ч":"h","час":"h","часа":"h","часов":"h",
    }
    return aliases.get(text,text)


@dataclass(frozen=True)
class ParameterContract:
    code: str
    anchors: tuple[str,...]
    unit_family: tuple[str,...]
    evidence_kinds: tuple[str,...]=()
    entity_terms: tuple[str,...]=()
    semantic_level_required: bool=False


CONTRACTS: dict[str,ParameterContract] = {
    "BODY_VOLUME":ParameterContract(
        "BODY_VOLUME",("объем кузова","объемом кузова"),("m3",),
        entity_terms=("самосвал","автосамосвал","truck"),
    ),
    "BUCKET_VOLUME":ParameterContract(
        "BUCKET_VOLUME",("объем ковша","объемом ковша"),("m3",),
        entity_terms=("погрузчик","экскаватор","ковш"),
    ),
    "CAPACITY":ParameterContract(
        "CAPACITY",("производительность","проектная мощность","производственная мощность","мощность"),("t/h","m3/h","t/y","kt/y","mt/y"),
        evidence_kinds=("TECHNOLOGY_CAPACITY_TOPOLOGY",),semantic_level_required=True,
    ),
    "POWER_INSTALLED":ParameterContract(
        "POWER_INSTALLED",("установленная мощность","мощность"),("kw","mw","kva"),
    ),
    "POWER_INST":ParameterContract(
        "POWER_INST",("установленная мощность","мощность"),("kw","mw","kva"),
    ),
    "POWER_KTP":ParameterContract(
        "POWER_KTP",("мощность ктп","мощность трансформатора","мощность"),("kva","kw"),
        entity_terms=("ктп","трансформатор"),
    ),
    "PRESSURE":ParameterContract(
        "PRESSURE",("давление","рабочее давление","расчетное давление","расчётное давление"),("pa","kpa","mpa","bar"),
    ),
    "VOLTAGE":ParameterContract(
        "VOLTAGE",("напряжение","номинальное напряжение"),("v","kv"),
    ),
    "FLOW_RATE":ParameterContract(
        "FLOW_RATE",("расход","подача"),("m3/h","l/s"),
    ),
    "HEIGHT_BUILD":ParameterContract(
        "HEIGHT_BUILD",("высота","высотой"),("m","mm"),
    ),
    "LENGTH":ParameterContract(
        "LENGTH",("длина","протяженность"),("m","km"),
    ),
    "AREA_BUILD":ParameterContract(
        "AREA_BUILD",("площадь застройки",),("m2",),
    ),
    "AREA_TOTAL":ParameterContract(
        "AREA_TOTAL",("общая площадь",),("m2",),
    ),
    "RES_VOLUME":ParameterContract(
        "RES_VOLUME",("объем резервуара","объемом резервуара","вместимость резервуара"),("m3",),
        entity_terms=("резервуар",),
    ),
    "VOLUME":ParameterContract(
        "VOLUME",("объем","вместимость"),("m3",),
    ),
    "QUANTITY":ParameterContract(
        "QUANTITY",("количество",),("pcs",),
    ),
    "EQUIPMENT_COUNT":ParameterContract(
        "EQUIPMENT_COUNT",("количество",),("pcs",),
    ),
    "LINE_COUNT":ParameterContract(
        "LINE_COUNT",("количество линий","число линий"),("pcs",),
        entity_terms=("линия",),
    ),
}


EQUIPMENT_CLASSES: dict[str,tuple[str,...]] = {
    "dump_truck":("автосамосвал","самосвал","карьерный самосвал","dump truck"),
    "loader":("погрузчик","фронтальный погрузчик","loader"),
    "excavator":("экскаватор","excavator"),
    "pump":("насос","насосный агрегат"),
    "fan":("вентилятор",),
    "compressor":("компрессор",),
    "transformer":("трансформатор","ктп"),
    "crusher":("дробилка","дробильный"),
    "screen":("грохот",),
    "conveyor":("конвейер",),
    "reservoir":("резервуар",),
    "hopper":("бункер",),
    "line":("линия",),
    "unit":("агрегат","установка"),
}


def equipment_terms(text: str) -> set[str]:
    low=norm(text)
    classes=set()
    for canonical,aliases in EQUIPMENT_CLASSES.items():
        if any(alias in low for alias in aliases):
            classes.add(canonical)
    return classes



def canonical_contract(code: str) -> ParameterContract | None:
    key=str(code or "").upper()
    if key in CONTRACTS:
        return CONTRACTS[key]
    if "PRESSURE" in key:
        return CONTRACTS["PRESSURE"]
    if "VOLTAGE" in key:
        return CONTRACTS["VOLTAGE"]
    if "POWER" in key:
        return CONTRACTS["POWER_INSTALLED"]
    if "COUNT" in key or "QUANTITY" in key:
        return CONTRACTS["EQUIPMENT_COUNT"]
    return None


def numeric(value: Any) -> float | None:
    if isinstance(value,(int,float)):
        return float(value)
    text=str(value or "").replace("\xa0"," ").replace(",",".")
    text=re.sub(r"(?<=\d)\s+(?=\d)","",text)
    match=re.search(r"[-+]?\d+(?:\.\d+)?",text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def entity_binding_ok(requirement_text: str, evidence_text: str, contract: ParameterContract | None) -> bool:
    req=equipment_terms(requirement_text)
    ev=equipment_terms(evidence_text)
    if req:
        return bool(req & ev)
    if contract and contract.entity_terms:
        wanted={term for term in contract.entity_terms if term in norm(requirement_text)}
        if wanted and not any(term in norm(evidence_text) for term in wanted):
            return False
    return True


_UNIT_PATTERN = (
    r"тыс\.?\s*(?:т|тонн)\s*(?:/\s*|в\s+)?год|"
    r"млн\.?\s*(?:т|тонн)\s*(?:/\s*|в\s+)?год|"
    r"(?:т|тонн)\s*(?:/\s*|в\s+)?год|"
    r"м\s*[²2]|м\s*[³3]|квт|мвт|ква|мпа|кпа|па|бар|bar|кв|в|"
    r"т\s*/\s*ч|м\s*[³3]\s*/\s*ч|л\s*/\s*с|км|мм|см|м|шт\.?"
)


def _extract_near_anchor(text: str, anchors: tuple[str,...], allowed_units: tuple[str,...]) -> list[dict[str,Any]]:
    low=norm(text)
    results=[]
    for anchor in anchors:
        start=0
        a=norm(anchor)
        while True:
            pos=low.find(a,start)
            if pos<0:
                break
            window=low[pos:pos+180]
            for m in re.finditer(rf"(?<!\d)(\d[\d\s]*(?:[.,]\d+)?)\s*({_UNIT_PATTERN})\b",window,re.I):
                value=numeric(m.group(1))
                u=unit(m.group(2))
                if value is None or (allowed_units and u not in allowed_units):
                    continue
                results.append({
                    "value":value,"unit":u,"anchor":anchor,
                    "offset":pos+m.start(),"source":"fragment_anchor",
                })
            start=pos+len(a)
    return results


def capacity_semantic_level(*values: Any) -> str:
    text=norm(" ".join(str(v or "") for v in values))
    compact=text.replace(" ","")
    if any(x in text for x in (
        "производительность одной линии","производительность линии","мощность линии","на одну линию",
    )):
        return "SINGLE_LINE_CAPACITY"
    if any(x in text for x in (
        "суммарная производительность","общая производительность","номинальная производительность",
        "установленная производительность",
    )):
        return "NOMINAL_TOTAL_CAPACITY"
    if any(x in text for x in (
        "часовая производительность отделения","производительность отделения",
        "эксплуатационная производительность","среднечасовая производительность","технологический режим",
    )):
        return "OPERATING_SECTION_THROUGHPUT"
    if any(x in text for x in (
        "проектная производительность","проектная мощность","производительность проекта",
        "производственная мощность","годовая производительность","годовая мощность",
    )) or any(x in compact for x in (
        "тыс.т/год","тыс.тонн/год","тыс.тоннвгод","тыс.твгод",
        "млн.т/год","млн.тонн/год","млн.тоннвгод","млн.твгод",
        "т/год","тонн/год","тоннвгод",
    )):
        return "PROJECT_DESIGN_CAPACITY"
    return ""


def structured_values(
    *,
    parameter_code: str,
    requirement_text: str,
    required_unit: str,
    evidence_fragment: str,
    evidence_meta: dict[str,Any],
) -> list[dict[str,Any]]:
    code=str(parameter_code or "").upper()
    contract=canonical_contract(code)
    ru=unit(required_unit)
    fragment=str(evidence_fragment or "")
    if not entity_binding_ok(requirement_text,fragment,contract):
        return []

    results=[]

    explicit_code=str(
        evidence_meta.get("observed_parameter_code")
        or evidence_meta.get("project_parameter_code")
        or evidence_meta.get("typed_parameter_code")
        or ""
    ).upper()
    if explicit_code and explicit_code==code:
        semantic_ok=True
        semantic_level=""
        if contract and contract.semantic_level_required:
            required_level=capacity_semantic_level(requirement_text)
            semantic_level=str(evidence_meta.get("capacity_observed_level") or "") or capacity_semantic_level(fragment)
            if required_level:
                semantic_ok=bool(semantic_level and semantic_level==required_level)
        if semantic_ok:
            for key in ("project_value","observed_value","value"):
                val=numeric(evidence_meta.get(key))
                if val is None:
                    continue
                eu=unit(
                    evidence_meta.get("project_unit")
                    or evidence_meta.get("observed_unit")
                    or evidence_meta.get("unit")
                )
                if ru and eu!=ru:
                    continue
                row={"value":val,"unit":eu,"source":key,"binding":"EXPLICIT_PARAMETER_CODE"}
                if semantic_level:
                    row["semantic_level"]=semantic_level
                results.append(row)

    kind=str(evidence_meta.get("evidence_kind") or "").upper()
    if contract and kind in contract.evidence_kinds:
        if code=="CAPACITY":
            vals=list(evidence_meta.get("summary_hourly_values") or [])
            observed_level=str(evidence_meta.get("capacity_observed_level") or "")
            required_level=capacity_semantic_level(requirement_text)
            if required_level and observed_level and required_level!=observed_level:
                vals=[]
            for raw in vals:
                val=numeric(raw)
                if val is not None and (not ru or ru=="t/h"):
                    results.append({
                        "value":val,"unit":"t/h","source":"typed_evidence_kind",
                        "binding":"TECHNOLOGY_CAPACITY_TOPOLOGY",
                        "semantic_level":observed_level,
                    })

    if contract:
        for fact in _extract_near_anchor(fragment,contract.anchors,contract.unit_family):
            if ru and fact["unit"]!=ru:
                continue
            if contract.semantic_level_required:
                required_level=capacity_semantic_level(requirement_text)
                observed_level=capacity_semantic_level(fragment)
                if required_level or observed_level:
                    if not (required_level and observed_level and required_level==observed_level):
                        continue
                fact["semantic_level"]=observed_level
            fact["binding"]="PARAMETER_ANCHOR"
            results.append(fact)

    if (ru=="pcs" or code in {"QUANTITY","EQUIPMENT_COUNT","LINE_COUNT"}) and entity_binding_ok(requirement_text,fragment,contract):
        q=numeric(evidence_meta.get("project_quantity"))
        if q is not None:
            results.append({"value":q,"unit":"pcs","source":"project_quantity","binding":"COUNT_ONLY"})
        low=norm(fragment)
        for m in re.finditer(r"(?<!\d)(\d{1,3})\s*шт\.?",low):
            results.append({"value":float(m.group(1)),"unit":"pcs","source":"fragment_count","binding":"COUNT_ONLY"})

    dedup=[]
    seen=set()
    for row in results:
        key=(round(float(row["value"]),9),row.get("unit"),row.get("binding"),row.get("semantic_level",""))
        if key in seen:
            continue
        seen.add(key);dedup.append(row)
    return dedup


def reserve_topology(text: str) -> tuple[int,int] | None:
    low=norm(text)
    working=None
    reserve=None
    patterns=(
        (r"(\d{1,2})\s*(?:шт\.?\s*)?(?:рабоч\w*|в\s+работе)", "working"),
        (r"(\d{1,2})\s*(?:шт\.?\s*)?(?:резерв\w*)", "reserve"),
        (r"(?:рабоч\w*|в\s+работе)\D{0,18}(\d{1,2})", "working"),
        (r"(?:резерв\w*)\D{0,18}(\d{1,2})", "reserve"),
    )
    for pattern,kind in patterns:
        m=re.search(pattern,low,re.I)
        if not m:
            continue
        value=int(m.group(1))
        if kind=="working":
            working=value
        else:
            reserve=value
    if working is None or reserve is None:
        return None
    return working,reserve


def compare_values(values: list[float], required: float) -> tuple[str,float]:
    if not values:
        return "NONE",0.0
    anchor=values[0]
    if not all(isclose(v,anchor,rel_tol=1e-9,abs_tol=1e-6) for v in values[1:]):
        return "CONFLICT",anchor
    return ("MATCH" if isclose(anchor,required,rel_tol=1e-9,abs_tol=1e-6) else "MISMATCH"),anchor
