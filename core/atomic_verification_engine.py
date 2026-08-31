from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from .assignment_verification_kernel import verify_assignment_requirement
from .atomic_requirement_graph import atomize_requirement
from .directed_evidence import normalize_engineering_unit, units_compatible
from .normalization import normalize_text
from .page_evidence_store import canonical_section, is_assignment_source, section_matches
from .verification_core import KIND_STATES, domain_summary
from .verification_recipe_compiler_v2 import VerificationRecipeCompilerV2
from .typed_evidence_resolver import resolve_typed_evidence
from .semantic_verdict_gate import evaluate_semantic_verdict_gate
from .requirement_contracts import coverage_diagnostics
from .semantic_evidence_engine import run_semantic_evidence_engine
from .constraint_engine import (
    canonicalize_constraint,
    canonicalize_observed,
    constraint_from_atom,
    evaluate_numeric_constraint,
    requirement_text as constraint_requirement_text,
)
from .object_semantics import canonical_parameter_code
from .metric_semantics import (
    capacity_level_label,
    capacity_levels_equivalent,
    capacity_semantic_level,
)


ENGINE_VERSION = "6.1-semantic-capacity-scope"
DESIGN_MARKERS = (
    "предусмотр", "предусматр", "проектом принят", "проектом выполн", "запроектирован",
    "оборудуется", "ограждается", "осуществляется", "применяется",
    "устанавливается", "прокладывается", "выполняется", "обеспечивается",
)
STRONG_PROOFS = {
    "STRUCTURED_VALUE", "STRUCTURED_COMPARISON", "VERIFIED_ENGINEERING_EVIDENCE",
    "VERIFIED_SET_EVIDENCE", "STRUCTURED_COMPLETENESS", "VERIFIED_CLAUSE",
}


def _norm(value: Any) -> str:
    return normalize_text(value).lower().replace("ё", "е")


def _float(value: Any) -> float | None:
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _groups_present(text: str, groups: Iterable[Iterable[str]]) -> list[list[str]]:
    low = _norm(text)
    return [list(group) for group in groups or [] if all(_norm(token) in low for token in group)]


def _snippet(text: str, tokens: Iterable[str], radius: int = 430) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    low = _norm(clean)
    positions = [low.find(_norm(token)) for token in tokens if token and low.find(_norm(token)) >= 0]
    pos = min(positions) if positions else 0
    return clean[max(0, pos - radius): pos + radius * 2][:1200]


def _evidence_locator(evidence: dict[str, Any]) -> str:
    document = str(evidence.get("document") or "").strip()
    page = evidence.get("page")
    return f"{document}, стр. {page}" if document and page not in (None, "") else document


def _normalise_evidence(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw in rows or []:
        document = str(raw.get("document") or raw.get("source_document") or "").strip()
        page = raw.get("page") or raw.get("source_page") or ""
        section = canonical_section(raw.get("document_type") or raw.get("section") or document)
        if not document or page in (None, "") or not section or is_assignment_source({"document": document, "document_type": section}):
            continue
        kind = str(raw.get("kind") or raw.get("evidence_kind") or "SOURCE_PASSAGE")
        result.append({
            **raw,
            "kind": "STRUCTURED_FACT" if kind in {
                "QUALIFIED_PROJECT_PASSAGE", "TECHNOLOGY_CAPACITY_TOPOLOGY",
                "EQUIPMENT_REGISTER_ROW", "STRUCTURED_VALUE", "STRUCTURED_COMPARISON",
                "VERIFIED_PATTERN_EVIDENCE", "VERIFIED_PROHIBITION_DECISION",
            } else kind,
            "document": document,
            "page": page,
            "section": section,
            "document_type": section,
            "text": str(raw.get("text") or raw.get("context") or raw.get("source_trace") or "")[:1600],
            "source_locator": _evidence_locator({"document": document, "page": page}),
            "retrieval_score": int(raw.get("retrieval_score") or raw.get("score") or 90),
            "judge_verdict": str(raw.get("judge_verdict") or "SUPPORTS"),
        })
    return result


def _result(
    atom: dict[str, Any], recipe: dict[str, Any], kind: str, *, proof: str,
    evidence: Iterable[dict[str, Any]] = (), basis: str = "", difference: Any = None,
    recommendation: str = "", candidates: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    evidence_rows = _normalise_evidence(evidence)
    candidate_rows = _normalise_evidence(candidates) or evidence_rows
    requested_kind=kind
    categorical = kind in {"VERIFIED_OK", "PROJECT_FINDING"}
    gate_reasons: list[str] = []
    if categorical and not recipe.get("categorical_verdict_allowed"):
        gate_reasons.append(
            "Рецепт используется только для поиска кандидатов: категоричный вывод разрешён "
            "только специализированному детерминированному checker-у."
        )
    if categorical and not recipe.get("executable"):
        gate_reasons.append("Проверочный рецепт не прошёл critic/regression gate.")
    if categorical and proof not in STRONG_PROOFS:
        gate_reasons.append("Тип доказательства недостаточен для категоричного вывода.")
    if categorical and not evidence_rows:
        gate_reasons.append("Нет доказательства с документом, страницей и профильным разделом.")
    if kind == "PROJECT_FINDING" and difference in (None, "", [], {}):
        gate_reasons.append("Не зафиксировано явное противоречие или сравниваемое различие.")
    semantic_gate = evaluate_semantic_verdict_gate(
        atom, proof, evidence_rows, categorical=categorical,
    )
    if categorical and semantic_gate.get("state") == "BLOCKED":
        gate_reasons.extend(str(reason) for reason in semantic_gate.get("reasons") or [])
    if gate_reasons:
        kind = "REVIEW_QUESTION" if candidate_rows else "SYSTEM_LIMITATION"
    status = {
        "VERIFIED_OK": "Соответствует заданию",
        "PROJECT_FINDING": "Выявлено отклонение",
        "REVIEW_QUESTION": "Требует проверки",
        "SYSTEM_LIMITATION": "Не проверено системой",
    }.get(kind, KIND_STATES.get(kind, "Информация"))
    diagnostics=coverage_diagnostics(
        atom,recipe,evidence=evidence_rows,candidates=candidate_rows,
        gate_reasons=gate_reasons,final_kind=kind,
    )
    return {
        **atom,
        "status": status,
        "verification_kind": kind,
        "verification_state": KIND_STATES.get(kind, status),
        "final_verification_kind": kind,
        "final_verification_state": KIND_STATES.get(kind, status),
        "proof_kind": proof,
        "evidence_quality_state": proof,
        "evidence": [f"{_evidence_locator(row)}: {str(row.get('text') or '')[:900]}" for row in evidence_rows],
        "verification_evidence": evidence_rows,
        "evidence_candidates": candidate_rows,
        "decision_basis": "; ".join(gate_reasons) if gate_reasons else basis,
        "difference": difference,
        "recommendation": recommendation,
        "verification_recipe": recipe,
        "recipe_id": recipe.get("recipe_id"),
        "recipe_status": recipe.get("recipe_status"),
        "recipe_quality": recipe.get("regression_score"),
        "automatic_verdict_eligible": bool(recipe.get("categorical_verdict_allowed")),
        "automatic_verdict_policy": recipe.get("automatic_verdict_policy") or "CANDIDATE_EVIDENCE_ONLY",
        "candidate_evidence_only": not bool(recipe.get("categorical_verdict_allowed")),
        "specialized_checker_id": recipe.get("specialized_checker_id") or "",
        "critic_state": "PASSED" if recipe.get("critic_pass") else "BLOCKED",
        "regression_state": "PASSED" if recipe.get("regression_pass") else "BLOCKED",
        "adversarial_state": "PASSED" if categorical and not gate_reasons else ("BLOCKED" if gate_reasons else "NOT_REQUIRED"),
        "adversarial_reasons": gate_reasons,
        "semantic_gate_state": semantic_gate.get("state"),
        "semantic_gate_reasons": list(semantic_gate.get("reasons") or []),
        "semantic_gate_version": semantic_gate.get("version"),
        "evidence_contract_state": (
            "SATISFIED" if any(str(row.get("contract_state") or "").upper() == "SATISFIED" for row in evidence_rows)
            else "UNSATISFIED"
        ),
        "evidence_contract": dict(atom.get("evidence_contract_v2") or {}),
        "atomic_status": kind,
        "engine_version": ENGINE_VERSION,
        "requested_verification_kind": requested_kind,
        **diagnostics,
    }


def _owner_matches(atom: dict[str, Any], fact: dict[str, Any]) -> bool:
    expected = _norm(atom.get("object_name") or atom.get("scope_entity") or "")
    if not expected:
        return True
    observed = _norm(fact.get("owner") or fact.get("entity_name") or "")
    if not observed:
        return False
    expected_terms = {x for x in re.findall(r"[a-zа-я0-9-]{4,}", expected) if x not in {"объект", "система", "площадка"}}
    observed_terms = set(re.findall(r"[a-zа-я0-9-]{4,}", observed))
    return bool(expected_terms and expected_terms & observed_terms)


def _convert(value: float, source_unit: str, target_unit: str) -> float | None:
    """Backward-compatible safe engineering unit conversion helper."""
    source = normalize_engineering_unit(source_unit)
    target = normalize_engineering_unit(target_unit)
    if source == target:
        return value
    factors = {
        ("км", "м"): 1000.0, ("м", "км"): 0.001,
        ("м", "мм"): 1000.0, ("мм", "м"): 0.001,
        ("мвт", "квт"): 1000.0, ("квт", "мвт"): 0.001,
        ("кг/м3", "т/м3"): 0.001, ("т/м3", "кг/м3"): 1000.0,
        ("кпа", "мпа"): 0.001, ("мпа", "кпа"): 1000.0,
        ("па", "мпа"): 0.000001, ("мпа", "па"): 1_000_000.0,
        ("бар", "мпа"): 0.1, ("мпа", "бар"): 10.0,
        ("тыс.т/год", "т/год"): 1000.0, ("т/год", "тыс.т/год"): 0.001,
        ("млн.т/год", "т/год"): 1_000_000.0, ("т/год", "млн.т/год"): 0.000001,
        ("мин", "ч"): 1 / 60, ("ч", "мин"): 60.0,
    }
    factor = factors.get((source, target))
    return value * factor if factor is not None else None


def _fact_value_check(atom: dict[str, Any], recipe: dict[str, Any], fact_graph: dict[str, Any]) -> dict[str, Any] | None:
    constraint = constraint_from_atom(atom)
    code = canonical_parameter_code(atom.get("parameter_code"))
    unit = str(atom.get("unit") or "")
    if constraint is None or not code or not unit:
        return None
    constraint = canonicalize_constraint(constraint, code)
    compatible: list[tuple[float, dict[str, Any]]] = []
    semantic_mismatches: list[dict[str, Any]] = []
    required_capacity_level = capacity_semantic_level(
        atom.get("requirement_text"), atom.get("parent_requirement_text"),
        atom.get("qualifier"), atom.get("unit"),
    ) if code == "CAPACITY" else ""
    for fact in fact_graph.get("facts") or []:
        if canonical_parameter_code(fact.get("property_code")) != code or not _owner_matches(atom, fact):
            continue
        observed = canonicalize_observed(fact.get("value"), fact.get("unit"), code)
        if observed is None:
            continue
        observed_value, observed_unit = observed
        if observed_unit != constraint.unit and not units_compatible(constraint.unit, observed_unit, code):
            continue
        if code == "CAPACITY":
            observed_capacity_level = capacity_semantic_level(
                fact.get("qualifier"), fact.get("property_name"),
                fact.get("source_trace"), fact.get("unit"),
            )
            if not capacity_levels_equivalent(required_capacity_level, observed_capacity_level):
                semantic_mismatches.append({
                    **fact,
                    "kind": "STRUCTURED_VALUE",
                    "text": fact.get("source_trace") or f"{fact.get('property_name') or code}: {observed_value:g} {constraint.unit}",
                    "value": observed_value,
                    "unit": constraint.unit,
                    "retrieval_score": 94,
                    "capacity_required_level": required_capacity_level,
                    "capacity_observed_level": observed_capacity_level,
                    "unit_compatible": True,
                })
                continue
        compatible.append((observed_value, fact))
    if not compatible:
        if semantic_mismatches:
            observed_labels = sorted({
                capacity_level_label(row.get("capacity_observed_level"))
                for row in semantic_mismatches
            })
            return _result(
                atom, recipe, "REVIEW_QUESTION", proof="CANDIDATE_EVIDENCE",
                candidates=semantic_mismatches,
                basis=(
                    f"Единицы совпадают, но сравниваются разные уровни показателя: требование — "
                    f"{capacity_level_label(required_capacity_level)}; проект — {', '.join(observed_labels)}."
                ),
                recommendation="Подтвердить в одном масштабе номинальную, проектную или эксплуатационную производительность.",
            )
        return None
    values = {round(value, 7) for value, _ in compatible}
    evidence = [{
        **fact, "kind": "STRUCTURED_VALUE", "text": fact.get("source_trace") or f"{fact.get('property_name') or code}: {value:g} {constraint.unit}",
        "value": value, "unit": constraint.unit, "retrieval_score": 98,
        "constraint_operator": constraint.operator,
    } for value, fact in compatible]
    if len(values) > 1:
        return _result(atom, recipe, "REVIEW_QUESTION", proof="STRUCTURED_VALUE", candidates=evidence,
                       basis=f"В проектных источниках найдены противоречивые значения: {sorted(values)} {constraint.unit}.",
                       recommendation="Уточнить владельца показателя и выбрать авторитетный источник.")
    observed = next(iter(values))
    evaluation = evaluate_numeric_constraint(constraint, observed)
    required_text = constraint_requirement_text(constraint)
    if evaluation["satisfied"]:
        return _result(atom, recipe, "VERIFIED_OK", proof="STRUCTURED_VALUE", evidence=evidence,
                       basis=f"Структурированное значение проекта {observed:g} {constraint.unit} выполняет условие «{required_text}».",
                       difference=dict(evaluation))
    difference = dict(evaluation)
    return _result(atom, recipe, "PROJECT_FINDING", proof="STRUCTURED_COMPARISON", evidence=evidence,
                   basis=f"Требование Задания: {required_text}; в проектном источнике: {observed:g} {constraint.unit}.", difference=difference,
                   recommendation="Привести проектное решение в соответствие с Заданием либо оформить согласованное изменение.")


def _directed_value_check(atom: dict[str, Any], recipe: dict[str, Any]) -> dict[str, Any] | None:
    """Adjudicate exact requirement-directed numeric clauses.

    A page-level keyword hit is insufficient.  The candidate must carry the
    exact metric/value clause, document, page, compatible unit and owner gate
    produced by ``directed_candidates``.  Capacity additionally requires the
    same engineering semantic level.
    """
    constraint = constraint_from_atom(atom)
    code = canonical_parameter_code(atom.get("parameter_code"))
    if constraint is None or not code:
        return None
    constraint = canonicalize_constraint(constraint, code)
    required_level = capacity_semantic_level(
        atom.get("requirement_text"), atom.get("parent_requirement_text"), atom.get("unit"),
    ) if code == "CAPACITY" else ""
    accepted: list[tuple[float, dict[str, Any]]] = []
    semantic_mismatches: list[dict[str, Any]] = []
    for raw in atom.get("directed_evidence_candidates") or []:
        if str(raw.get("evidence_state") or "") != "verified_candidate":
            continue
        if canonical_parameter_code(raw.get("parameter_code")) != code:
            continue
        if not raw.get("document") or raw.get("page") in (None, ""):
            continue
        if not str(raw.get("source_trace") or raw.get("exact_clause") or "").strip():
            continue
        scope = str((atom.get("evidence_contract_v2") or {}).get("scope") or "")
        if scope in {"OBJECT_SPECIFIC", "EQUIPMENT_SPECIFIC"} and raw.get("owner_match") is not True:
            continue
        observed = canonicalize_observed(raw.get("value"), raw.get("unit"), code)
        if observed is None:
            continue
        value, observed_unit = observed
        if observed_unit != constraint.unit and not units_compatible(constraint.unit, observed_unit, code):
            continue
        evidence = {
            **raw,
            "kind": "STRUCTURED_VALUE",
            "text": str(raw.get("source_trace") or raw.get("exact_clause")),
            "value": value,
            "unit": constraint.unit,
            "admitted": True,
            "directed_evidence": True,
            "evidence_quality_decision": "VERIFIED",
            "retrieval_score": int(raw.get("score") or 95),
            "physical_trace_level": "ROW_TRACE",
            "source_locator": {
                **dict(raw.get("source_locator") or {}),
                "document": raw.get("document"), "page": raw.get("page"),
                "physical_trace_level": "ROW_TRACE",
            },
        }
        if code == "CAPACITY":
            observed_level = capacity_semantic_level(
                raw.get("source_trace"), raw.get("exact_clause"), raw.get("context"), raw.get("unit"),
            )
            evidence.update({
                "capacity_required_level": required_level,
                "capacity_observed_level": observed_level,
            })
            if not capacity_levels_equivalent(required_level, observed_level):
                semantic_mismatches.append(evidence)
                continue
        accepted.append((value, evidence))
    if not accepted:
        if semantic_mismatches:
            observed_labels = sorted({
                capacity_level_label(row.get("capacity_observed_level"))
                for row in semantic_mismatches
            })
            return _result(
                atom, recipe, "REVIEW_QUESTION", proof="CANDIDATE_EVIDENCE",
                candidates=semantic_mismatches,
                basis=(
                    f"Найден точный числовой фрагмент, но уровень мощности не совпадает: требование — "
                    f"{capacity_level_label(required_level)}; проект — {', '.join(observed_labels)}."
                ),
                recommendation="Подтвердить сравнение на одном смысловом уровне мощности.",
            )
        return None
    values = {round(value, 7) for value, _ in accepted}
    evidence_rows = [row for _, row in accepted]
    if len(values) > 1:
        return _result(
            atom, recipe, "REVIEW_QUESTION", proof="STRUCTURED_VALUE",
            candidates=evidence_rows,
            basis=f"В направленном поиске найдены противоречивые значения: {sorted(values)} {constraint.unit}.",
            recommendation="Уточнить авторитетный источник и область каждого значения.",
        )
    observed = next(iter(values))
    evaluation = evaluate_numeric_constraint(constraint, observed)
    required_text = constraint_requirement_text(constraint)
    if evaluation["satisfied"]:
        return _result(
            atom, recipe, "VERIFIED_OK", proof="STRUCTURED_VALUE", evidence=evidence_rows,
            basis=f"Точный адресный фрагмент проекта подтверждает условие «{required_text}».",
            difference=dict(evaluation),
        )
    return _result(
        atom, recipe, "PROJECT_FINDING", proof="STRUCTURED_COMPARISON", evidence=evidence_rows,
        basis=f"Требование Задания: {required_text}; в точном проектном фрагменте: {observed:g} {constraint.unit}.",
        difference=dict(evaluation),
        recommendation="Привести проектное решение в соответствие с Заданием либо оформить согласованное изменение.",
    )


def _pattern_check(atom: dict[str, Any], recipe: dict[str, Any], passages: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    if not list(recipe.get("evidence_groups") or []):
        return None
    resolved = resolve_typed_evidence(atom, recipe, passages)
    evidence = list(resolved.get("evidence") or [])
    candidates = list(resolved.get("candidates") or [])
    if not evidence and not candidates:
        return None
    if not evidence:
        return _result(atom, recipe, "REVIEW_QUESTION", proof="CANDIDATE_EVIDENCE", candidates=candidates,
                       basis="Найдены адресные кандидаты, но не выполнены все слоты доказательственного контракта: квалификаторы, модальность или проектное действие.")
    return _result(atom, recipe, "VERIFIED_OK", proof="VERIFIED_ENGINEERING_EVIDENCE", evidence=evidence,
                   basis=f"Все обязательные предикаты подтверждены в одном адресном фрагменте профильного раздела по паттерну {recipe.get('pattern_id')}.")


def _prohibition_check(atom: dict[str, Any], recipe: dict[str, Any], passages: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    raw_text = str(atom.get("atom_text") or atom.get("requirement_text") or "")
    text = _norm(raw_text)
    negation = re.search(r"\bне\s+(?:предусмотр|предусматр)\w*", text)
    if negation:
        boundary = max(text.rfind(".", 0, negation.start()), text.rfind(";", 0, negation.start()), text.rfind(":", 0, negation.start()))
        text = text[boundary + 1:negation.end()]
    stop = {
        "предусматривать", "предусмотреть", "предусматривается", "проектной",
        "документации", "выполнить", "требуется", "должен", "должна", "согласно",
    }
    terms: list[str] = []
    for word in re.findall(r"[a-zа-я0-9-]{4,}", text):
        if word in stop or word == "не":
            continue
        stem = word[: max(4, min(len(word), 8))]
        if stem not in terms:
            terms.append(stem)
    if len(terms) < 2:
        return None
    expected = list(recipe.get("expected_sections") or [])
    negative: list[dict[str, Any]] = []
    affirmative: list[dict[str, Any]] = []
    for passage in passages or []:
        if is_assignment_source(passage) or not section_matches(passage.get("section") or passage.get("document_type") or passage.get("document"), expected):
            continue
        source = re.sub(r"(?<=[A-Za-zА-Яа-яЁё])-\s+(?=[A-Za-zА-Яа-яЁё])", "", str(passage.get("text") or ""))
        clauses = [item.strip() for item in re.split(r"(?<=[.;])\s+|\n+", source) if item.strip()]
        for clause in clauses:
            low = _norm(clause)
            hits = [term for term in terms if term in low]
            if len(hits) < 2:
                continue
            negated = bool(re.search(r"\bне\s+(?:предусмотр|предусматр|проклад|выполн|треб)\w*", low))
            designed = any(marker in low for marker in DESIGN_MARKERS) or "прокладыва" in low
            # An affirmative contradiction must include the most specific tail
            # qualifier of the prohibition (here: «в земле»).  A generic phrase
            # such as «прокладка кабельных линий предусмотрена» is not enough.
            affirmative_specific = designed and terms[-1] in hits
            if not (negated or affirmative_specific):
                continue
            evidence = {
                "kind": "VERIFIED_PROHIBITION_DECISION",
                "document": passage.get("document"), "page": passage.get("page"),
                "section": passage.get("section") or passage.get("document_type"),
                "text": clause[:1200], "score": 98 if negated else 92,
                "matched_subject_terms": hits,
                "contract_state": "SATISFIED",
                "semantic_gate_state": "PASSED",
                "semantic_verdict": "SUPPORTS" if negated else "CONTRADICTS",
                "judge_verdict": "SUPPORTS" if negated else "CONTRADICTS",
                "same_clause_gate_state": "PASSED",
            }
            (negative if negated else affirmative).append(evidence)
    if negative and affirmative:
        return _result(atom, recipe, "REVIEW_QUESTION", proof="STRUCTURED_COMPARISON",
                       candidates=negative[:3] + affirmative[:3],
                       basis="В проекте найдены противоречивые локальные решения по запрещённому предмету.",
                       recommendation="Устранить противоречие и подтвердить итоговое проектное решение.")
    if negative:
        return _result(atom, recipe, "VERIFIED_OK", proof="VERIFIED_ENGINEERING_EVIDENCE", evidence=negative[:4],
                       basis="Профильный проектный источник локально и явно фиксирует, что запрещённое решение не предусматривается.")
    if affirmative:
        return _result(atom, recipe, "PROJECT_FINDING", proof="VERIFIED_ENGINEERING_EVIDENCE", evidence=affirmative[:4],
                       basis="Профильный проектный источник локально и явно предусматривает решение, запрещённое Заданием.",
                       difference={"required": "не предусматривать", "observed": "предусмотрено"},
                       recommendation="Исключить решение либо согласовать изменение Задания.")
    return None


def _kernel_check(atom: dict[str, Any], recipe: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    raw = verify_assignment_requirement(atom, page_corpus)
    if not raw:
        return None
    evidence = raw.get("verification_evidence") or raw.get("evidence_candidates") or []
    status = _norm(raw.get("status"))
    difference = raw.get("difference")
    focus = str(atom.get("focus") or atom.get("parameter_code") or "").upper()
    if "отклонен" in status or "не соответств" in status:
        difference_text = str(difference or raw.get("decision_basis") or "")
        segments = [part.strip() for part in re.split(r";\s*", difference_text) if part.strip()]
        if focus == "EQUIPMENT_IDENTITY":
            relevant = [part for part in segments if any(token in _norm(part) for token in ("марк", "модел", "изготовител", "обозначен"))]
        elif focus in {"EQUIPMENT_QUANTITY", "QUANTITY"}:
            relevant = [part for part in segments if "количеств" in _norm(part)]
        elif str(atom.get("atomic_kind") or "").upper() == "VALUE_COMPARISON" and focus not in {"CAPACITY", "PROCESS_LINE_COUNT"}:
            focus_tokens = {
                "CARRY_CAPACITY": ("грузопод",), "BODY_VOLUME": ("кузов",),
                "BUCKET_VOLUME": ("ковш",), "VOLUME": ("объем", "объём"),
            }.get(focus, (focus.lower(),))
            relevant = [part for part in segments if any(token in _norm(part) for token in focus_tokens)]
        else:
            relevant = segments
        if not relevant:
            return _result(atom, recipe, "REVIEW_QUESTION", proof="CANDIDATE_EVIDENCE", candidates=evidence,
                           basis="Найдено отклонение другого атрибута; текущее атомарное условие категорично не закрыто.")
        focused_difference = "; ".join(relevant)
        return _result(atom, recipe, "PROJECT_FINDING", proof=str(raw.get("evidence_quality_state") or "STRUCTURED_COMPARISON"),
                       evidence=evidence, basis=focused_difference, difference=focused_difference,
                       recommendation="Устранить подтверждённое отклонение либо оформить согласованное изменение Задания.")
    if "соответств" in status:
        return _result(atom, recipe, "VERIFIED_OK", proof=str(raw.get("evidence_quality_state") or "VERIFIED_ENGINEERING_EVIDENCE"),
                       evidence=evidence, basis=str(raw.get("decision_basis") or ""))
    return _result(atom, recipe, "REVIEW_QUESTION", proof=str(raw.get("evidence_quality_state") or "CANDIDATE_EVIDENCE"),
                   candidates=evidence, basis=str(raw.get("decision_basis") or "Найден кандидат в доказательства."))


def verify_atomic_requirements(
    atoms: Iterable[dict[str, Any]], *, knowledge_root: str,
    fact_graph: dict[str, Any], page_corpus: list[dict[str, Any]],
    judge_provider: Any = None, critic_provider: Any = None,
    semantic_level: str = "off", semantic_limit: int = 0,
    semantic_progress_callback: Any = None,
) -> list[dict[str, Any]]:
    compiler = VerificationRecipeCompilerV2(knowledge_root)
    rows: list[dict[str, Any]] = []
    passages = list(fact_graph.get("passages") or page_corpus or [])
    for atom in atoms or []:
        recipe = compiler.compile(atom)
        result: dict[str, Any] | None = None
        atom_kind = str(atom.get("atomic_kind") or "").upper()
        if atom_kind == "PROHIBITION":
            result = _prohibition_check(atom, recipe, passages)
        if str(atom.get("atomic_kind") or "").upper() == "VALUE_COMPARISON":
            result = _fact_value_check(atom, recipe, fact_graph)
        if result is None and str(atom.get("atomic_kind") or "").upper() == "VALUE_COMPARISON":
            result = _directed_value_check(atom, recipe)
        if result is None and atom_kind not in {"PROHIBITION", "APPLICABILITY_DECLARATION"}:
            result = _pattern_check(atom, recipe, passages)
        if result is None and atom_kind not in {"PROHIBITION", "APPLICABILITY_DECLARATION", "NORMATIVE_CLAUSE", "TRACEABILITY", "DOCUMENT_DELIVERABLE", "DESIGN_DETERMINED"}:
            result = _kernel_check(atom, recipe, page_corpus)
        if result is None:
            limitation = str(atom.get("atomic_kind") or "").upper() in {"APPLICABILITY_DECLARATION", "NORMATIVE_CLAUSE", "TRACEABILITY", "DOCUMENT_DELIVERABLE", "DESIGN_DETERMINED"} or not recipe.get("executable")
            result = _result(
                atom, recipe, "SYSTEM_LIMITATION" if limitation else "SYSTEM_LIMITATION",
                proof="NO_EVIDENCE", basis=(
                    "Декларация применимости, нормативное или комплектностное условие не имеет верифицированного адресного основания."
                    if limitation else "В профильных разделах не найдено доказательство, достаточное для категоричного вывода."
                ), recommendation="Проверить условие специалистом по указанным ожидаемым разделам.",
            )
        rows.append(result)
    semantic_audit = run_semantic_evidence_engine(
        rows,
        fact_graph=fact_graph,
        page_corpus=page_corpus,
        judge_provider=judge_provider,
        critic_provider=critic_provider,
        level=semantic_level,
        limit=semantic_limit,
        progress_callback=semantic_progress_callback,
    )
    if rows:
        rows[0]["semantic_engine_audit"] = semantic_audit
    return rows


def aggregate_atomic_results(
    parent_rows: Iterable[dict[str, Any]], atomic_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for atom in atomic_rows or []:
        by_parent[str(atom.get("parent_requirement_id") or atom.get("source_requirement_id") or "")].append(atom)
    output: list[dict[str, Any]] = []
    for parent in parent_rows or []:
        parent_id = str(parent.get("requirement_id") or parent.get("id") or "")
        atoms = by_parent.get(parent_id) or []
        if not atoms:
            output.append(dict(parent))
            continue
        counts = Counter(str(atom.get("verification_kind") or "SYSTEM_LIMITATION") for atom in atoms)
        if counts["PROJECT_FINDING"]:
            kind, status = "PROJECT_FINDING", "Выявлено отклонение"
        elif counts["VERIFIED_OK"] == len(atoms):
            kind, status = "VERIFIED_OK", "Соответствует заданию"
        elif counts["REVIEW_QUESTION"] or counts["VERIFIED_OK"]:
            kind, status = "REVIEW_QUESTION", "Частично подтверждено" if counts["VERIFIED_OK"] else "Требует проверки"
        else:
            kind, status = "SYSTEM_LIMITATION", "Не проверено системой"
        evidence = [item for atom in atoms for item in (atom.get("evidence") or [])]
        differences = [atom.get("difference") for atom in atoms if atom.get("verification_kind") == "PROJECT_FINDING" and atom.get("difference") not in (None, "")]
        level_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
        evidence_levels = [str(atom.get("evidence_level") or "L0") for atom in atoms]
        parent_level = min(evidence_levels, key=lambda value: level_order.get(value, 0)) if evidence_levels else "L0"
        evidence_ready = sum(level_order.get(value, 0) >= 3 for value in evidence_levels)
        archetypes = Counter(str(atom.get("coverage_archetype") or "UNCLASSIFIED") for atom in atoms)
        diagnostic = next((atom for atom in atoms if atom.get("verification_kind") == "REVIEW_QUESTION"), None) or next((atom for atom in atoms if atom.get("verification_kind") == "SYSTEM_LIMITATION"), None) or atoms[0]
        output.append({
            **parent,
            "status": status,
            "verification_kind": kind,
            "verification_state": KIND_STATES.get(kind, status),
            "final_verification_kind": kind,
            "final_verification_state": KIND_STATES.get(kind, status),
            "proof_kind": "ATOMIC_AGGREGATION",
            "evidence": evidence[:20],
            "difference": differences,
            "atomic_condition_count": len(atoms),
            "atomic_completed": counts["VERIFIED_OK"] + counts["PROJECT_FINDING"],
            "atomic_verified_ok": counts["VERIFIED_OK"],
            "atomic_findings": counts["PROJECT_FINDING"],
            "atomic_review": counts["REVIEW_QUESTION"],
            "atomic_limitations": counts["SYSTEM_LIMITATION"],
            "atomic_result_ids": [atom.get("atom_id") for atom in atoms],
            "evidence_level": "L5" if kind in {"VERIFIED_OK", "PROJECT_FINDING"} else parent_level,
            "evidence_level_distribution": dict(Counter(evidence_levels)),
            "evidence_ready_atomic": evidence_ready,
            "evidence_coverage_pct": round(100 * evidence_ready / max(1, len(atoms)), 1),
            "semantic_consensus_completed": sum(str(atom.get("semantic_consensus_state") or "") == "PASSED" for atom in atoms),
            "checker_family": ", ".join(dict.fromkeys(
                str(atom.get("checker_family") or "") for atom in atoms if atom.get("checker_family")
            )),
            "checker_mode": ", ".join(dict.fromkeys(
                str(atom.get("checker_mode") or "") for atom in atoms if atom.get("checker_mode")
            )),
            "coverage_archetype": archetypes.most_common(1)[0][0] if archetypes else "UNCLASSIFIED",
            "coverage_state": (
                "PROJECT_FINDING_CONFIRMED" if kind == "PROJECT_FINDING" else
                "AUTOMATED_COMPLETE" if kind == "VERIFIED_OK" else
                diagnostic.get("coverage_state") or "AUTOMATION_GAP"
            ),
            "coverage_reason_code": diagnostic.get("coverage_reason_code"),
            "coverage_reason": diagnostic.get("coverage_reason"),
            "missing_evidence_slots": list(dict.fromkeys(
                str(slot) for atom in atoms for slot in (atom.get("missing_evidence_slots") or []) if slot
            )),
            "expected_evidence_route": list(dict.fromkeys(
                str(section) for atom in atoms for section in (atom.get("expected_evidence_route") or []) if section
            )),
            "recipe_status": (
                "TRUSTED" if all(str(atom.get("recipe_status") or "") == "TRUSTED" for atom in atoms)
                else "RETRIEVAL_ONLY" if any(str(atom.get("recipe_status") or "") == "RETRIEVAL_ONLY" for atom in atoms)
                else "EXPERIMENTAL"
            ),
            "recommendation": (
                "Устранить подтверждённое отклонение либо согласовать изменение Задания."
                if kind == "PROJECT_FINDING" else
                "Дополнительное действие не требуется."
                if kind == "VERIFIED_OK" else
                "Проверить незакрытые атомарные условия и зафиксировать решение специалиста."
                if kind == "REVIEW_QUESTION" else
                "Выполнить проверку специалистом по указанным ожидаемым разделам."
            ),
            "decision_basis": (
                f"Атомарная агрегация: подтверждено {counts['VERIFIED_OK']}, отклонений {counts['PROJECT_FINDING']}, "
                f"вопросов {counts['REVIEW_QUESTION']}, ограничений {counts['SYSTEM_LIMITATION']} из {len(atoms)} условий."
            ),
        })
    return output


def atomic_summary(rows: list[dict[str, Any]], graph_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = domain_summary(rows, "assignment")
    summary.update({
        "compliant": summary["verified_ok"],
        "deviation": summary["project_findings"],
        "unconfirmed": summary["review_questions"],
        "semantic": 0,
        "not_checked": summary["system_limitations"],
        "source_requirements": int((graph_summary or {}).get("source_requirements") or 0),
        "atomic_requirements": len(rows),
        "additional_conditions": int((graph_summary or {}).get("additional_conditions") or 0),
        "scope_coverage_pct": float((graph_summary or {}).get("scope_coverage_pct") or 0),
        "by_kind": dict((graph_summary or {}).get("by_kind") or {}),
        "principle": "Метрики рассчитаны по атомарным условиям; NOT_FOUND является ограничением, а не нарушением.",
    })
    return summary


def parent_assignment_summary(
    parent_rows: list[dict[str, Any]], atomic_rows: list[dict[str, Any]],
    graph_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build public assignment metrics from source requirements, not atoms."""
    public = domain_summary(parent_rows, "assignment")
    atomic = domain_summary(atomic_rows, "assignment")
    public.update({
        "compliant": public["verified_ok"],
        "deviation": public["project_findings"],
        "unconfirmed": public["review_questions"],
        "semantic": 0,
        "not_checked": public["system_limitations"],
        "source_requirements": len(parent_rows),
        "atomic_requirements": len(atomic_rows),
        "additional_conditions": int((graph_summary or {}).get("additional_conditions") or 0),
        "scope_coverage_pct": float((graph_summary or {}).get("scope_coverage_pct") or 0),
        "by_kind": dict((graph_summary or {}).get("by_kind") or {}),
        "atomic_diagnostics": atomic,
        "principle": (
            "Публичное покрытие рассчитано по исходным требованиям Задания; "
            "атомы используются только для поиска и диагностики доказательств."
        ),
    })
    return public


def atomic_evidence_facts(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose adjudicated atomic evidence to Deep Evidence without inventing facts."""
    result: list[dict[str, Any]] = []
    for row in rows or []:
        if row.get("verification_kind") not in {"VERIFIED_OK", "PROJECT_FINDING"}:
            continue
        for evidence in row.get("verification_evidence") or []:
            evidence_requirement_id = row.get("checklist_parent_id") or row.get("atom_id")
            result.append({
                "fact_id": f"ATOM-EVD-{row.get('atom_id')}-{len(result)+1}",
                "requirement_id": evidence_requirement_id,
                "parameter_code": row.get("parameter_code") or row.get("focus") or row.get("atomic_kind"),
                "parameter_name": row.get("atom_text"),
                "value": evidence.get("value") if evidence.get("value") not in (None, "") else row.get("verification_kind"),
                "unit": row.get("unit") or evidence.get("unit") or "",
                "document": evidence.get("document"), "page": evidence.get("page"),
                "document_type": evidence.get("section") or evidence.get("document_type"),
                "source_trace": evidence.get("text"),
                "fact_admission_decision": "ADMIT", "evidence_quality_decision": "VERIFIED",
                "binding_status": "EXACT_OBJECT" if row.get("object_name") else "ROW_LOCKED",
                "object_name": row.get("object_name") or row.get("scope_entity") or "Проект",
                "directed_evidence": True,
            })
    return result


def verify_checklist_rows(
    checklist_rows: list[dict[str, Any]], *, knowledge_root: str,
    fact_graph: dict[str, Any], page_corpus: list[dict[str, Any]],
    judge_provider: Any = None, critic_provider: Any = None,
    semantic_level: str = "off", semantic_limit: int = 0,
) -> dict[str, Any]:
    """Run the same atomic evidence gate over actionable corporate checklist rows.

    Existing checklist results are only promoted when every atomic condition is
    categorically proved.  A finding likewise requires an explicit, gated
    contradiction; NOT_FOUND preserves the system limitation.
    """
    atoms: list[dict[str, Any]] = []
    row_by_parent: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(checklist_rows or [], 1):
        if row.get("is_heading"):
            continue
        parent_id = f"CHECK-{index:04d}"
        question = str(row.get("question") or row.get("Позиция по чек-листу") or "").strip()
        if not question:
            continue
        section = str(row.get("automatic_section") or row.get("section") or row.get("Раздел") or "").strip()
        requirement = {
            "requirement_id": parent_id,
            "requirement_text": question,
            "domain": "checklist",
            "source_row": row.get("item_no") or row.get("position") or index,
            "source_row_title": row.get("automatic_checklist") or row.get("source_file") or "",
            "object_name": row.get("object_name") or row.get("entity") or "",
            "compiled_rule": dict(row.get("compiled_rule") or {}),
            "typed_check": row.get("typed_check") or (row.get("compiled_rule") or {}).get("typed_check") or "",
        }
        children = atomize_requirement(requirement, domain="checklist")
        for child in children:
            if section:
                child["expected_sections"] = [section]
                contract = dict(child.get("evidence_contract_v2") or {})
                contract["expected_sections"] = [section]
                child["evidence_contract_v2"] = contract
            child["checklist_parent_id"] = parent_id
        atoms.extend(children)
        row_by_parent[parent_id] = row

    verified = verify_atomic_requirements(
        atoms, knowledge_root=knowledge_root, fact_graph=fact_graph, page_corpus=page_corpus,
        judge_provider=judge_provider, critic_provider=critic_provider,
        semantic_level=semantic_level, semantic_limit=semantic_limit,
    )
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for atom in verified:
        by_parent[str(atom.get("checklist_parent_id") or atom.get("parent_requirement_id") or "")].append(atom)

    promoted = findings = questions = 0
    for parent_id, conditions in by_parent.items():
        row = row_by_parent[parent_id]
        counts = Counter(str(item.get("verification_kind") or "SYSTEM_LIMITATION") for item in conditions)
        evidence = [value for item in conditions for value in (item.get("evidence") or [])]
        diagnostic=next((item for item in conditions if item.get("verification_kind")=="REVIEW_QUESTION"),None) or next((item for item in conditions if item.get("verification_kind")=="SYSTEM_LIMITATION"),None) or conditions[0]
        row["atomic_conditions"] = conditions
        row["atomic_condition_count"] = len(conditions)
        row["atomic_completed"] = counts["VERIFIED_OK"] + counts["PROJECT_FINDING"]
        level_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
        evidence_levels = [str(item.get("evidence_level") or "L0") for item in conditions]
        evidence_ready = sum(level_order.get(value, 0) >= 3 for value in evidence_levels)
        row["evidence_level"] = min(evidence_levels, key=lambda value: level_order.get(value, 0)) if evidence_levels else "L0"
        row["evidence_level_distribution"] = dict(Counter(evidence_levels))
        row["evidence_ready_atomic"] = evidence_ready
        row["evidence_coverage_pct"] = round(100 * evidence_ready / max(1, len(conditions)), 1)
        row["semantic_consensus_completed"] = sum(str(item.get("semantic_consensus_state") or "") == "PASSED" for item in conditions)
        row["checker_family"] = ", ".join(dict.fromkeys(
            str(item.get("checker_family") or "") for item in conditions if item.get("checker_family")
        ))
        row["checker_mode"] = ", ".join(dict.fromkeys(
            str(item.get("checker_mode") or "") for item in conditions if item.get("checker_mode")
        ))
        categorical_eligible=all(bool(item.get("automatic_verdict_eligible")) for item in conditions)
        recipe_statuses={str(item.get("recipe_status") or "") for item in conditions}
        if "RETRIEVAL_ONLY" in recipe_statuses:
            row["recipe_status"]="RETRIEVAL_ONLY"
        elif "EXPERIMENTAL" in recipe_statuses:
            row["recipe_status"]="EXPERIMENTAL"
        elif recipe_statuses:
            row["recipe_status"]=sorted(recipe_statuses)[0]
        row["automatic_verdict_eligible"]=categorical_eligible
        row["automatic_verdict_policy"]=(
            "SPECIALIZED_DETERMINISTIC_CHECKER" if categorical_eligible else "CANDIDATE_EVIDENCE_ONLY"
        )
        row["candidate_evidence_only"]=not categorical_eligible
        row.update({
            "coverage_archetype": diagnostic.get("coverage_archetype"),
            "coverage_state": (
                "PROJECT_FINDING_CONFIRMED" if counts["PROJECT_FINDING"] else
                "AUTOMATED_COMPLETE" if counts["VERIFIED_OK"] == len(conditions) else
                diagnostic.get("coverage_state") or "AUTOMATION_GAP"
            ),
            "coverage_reason_code": diagnostic.get("coverage_reason_code"),
            "coverage_reason": diagnostic.get("coverage_reason"),
            "missing_evidence_slots": list(dict.fromkeys(
                str(slot) for item in conditions for slot in (item.get("missing_evidence_slots") or []) if slot
            )),
            "expected_evidence_route": list(dict.fromkeys(
                str(section) for item in conditions for section in (item.get("expected_evidence_route") or []) if section
            )),
        })
        if counts["PROJECT_FINDING"]:
            row["evidence_level"] = "L5"
            row.update({
                "status": "Нет", "proof_kind": "STRUCTURED_COMPARISON",
                "verification_kind": "PROJECT_FINDING", "verification_state": KIND_STATES["PROJECT_FINDING"],
                "final_verification_kind": "PROJECT_FINDING", "final_verification_state": KIND_STATES["PROJECT_FINDING"],
                "evidence": evidence, "decision_basis": "Одно или несколько атомарных условий имеют подтверждённое противоречие.",
                "recommendation": "Устранить подтверждённое отклонение по атомарным условиям чек-листа.",
            })
            findings += 1
        elif counts["VERIFIED_OK"] == len(conditions):
            row["evidence_level"] = "L5"
            row.update({
                "status": "Да", "proof_kind": "VERIFIED_ENGINEERING_EVIDENCE",
                "verification_kind": "VERIFIED_OK", "verification_state": KIND_STATES["VERIFIED_OK"],
                "final_verification_kind": "VERIFIED_OK", "final_verification_state": KIND_STATES["VERIFIED_OK"],
                "evidence": evidence, "decision_basis": "Все атомарные условия пункта подтверждены профильными проектными источниками.",
                "recommendation": "Дополнительное действие не требуется.",
            })
            promoted += 1
        elif counts["REVIEW_QUESTION"] or counts["VERIFIED_OK"]:
            has_confirmed_condition = counts["VERIFIED_OK"] > 0
            has_candidates = any(item.get("evidence_candidates") for item in conditions)
            row.update({
                "status": "Требует проверки", "proof_kind": "CANDIDATE_EVIDENCE",
                "verification_kind": "REVIEW_QUESTION", "verification_state": KIND_STATES["REVIEW_QUESTION"],
                "final_verification_kind": "REVIEW_QUESTION", "final_verification_state": KIND_STATES["REVIEW_QUESTION"],
                "evidence": evidence,
                "decision_basis": (
                    "Пункт подтверждён частично; категоричный вывод удержан."
                    if has_confirmed_condition else
                    "Найдены адресные кандидаты, но ни одно атомарное условие не подтверждено категорично."
                    if has_candidates else
                    "Адресное доказательство для пункта не сформировано."
                ),
                "recommendation": (
                    "Проверить незакрытые атомарные условия специалистом."
                    if has_confirmed_condition else
                    "Проверить найденные кандидаты и подтвердить владельца, показатель и проектное решение."
                    if has_candidates else
                    "Найти доказательство в ожидаемых разделах и выполнить проверку специалистом."
                ),
            })
            questions += 1
        else:
            # Atomic adjudication is authoritative.  A lexical first-pass
            # positive must not survive when no condition has deterministic
            # categorical proof.
            row.update({
                "status": "Не проверено системой", "proof_kind": "NO_EVIDENCE",
                "verification_kind": "SYSTEM_LIMITATION", "verification_state": KIND_STATES["SYSTEM_LIMITATION"],
                "final_verification_kind": "SYSTEM_LIMITATION", "final_verification_state": KIND_STATES["SYSTEM_LIMITATION"],
                "evidence": evidence,
                "decision_basis": "Специализированный детерминированный checker не подтвердил пункт.",
                "recommendation": "Проверить пункт специалистом либо подключить специализированный checker.",
                "automatic_verdict_eligible": False,
                "automatic_verdict_policy": "CANDIDATE_EVIDENCE_ONLY",
                "candidate_evidence_only": True,
            })
    return {
        "version": ENGINE_VERSION,
        "atoms": verified,
        "semantic_engine_audit": dict((verified[0] if verified else {}).get("semantic_engine_audit") or {}),
        "summary": {
            "checklist_rows": len(row_by_parent), "atomic_conditions": len(verified),
            "promoted_verified": promoted, "project_findings": findings,
            "review_questions": questions,
        },
    }
