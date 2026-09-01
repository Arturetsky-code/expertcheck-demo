from __future__ import annotations

import re
from typing import Any, Iterable

from .normalization import normalize_text
from .page_evidence_store import canonical_section, is_assignment_source, section_matches
from .requirement_contracts import build_contract
from .semantic_slot_gate import evaluate_semantic_slots


RESOLVER_VERSION = "16.0-clause-and-semantic-slot-evidence"
DESIGN_MARKERS = (
    "предусмотр", "предусматр", "проектом принят", "проектом выполн",
    "запроектирован", "оборудуется", "ограждается", "осуществляется",
    "применяется", "устанавливается", "прокладывается", "выполняется",
    "обеспечивается", "принят", "применен", "применён",
    "учтен", "учтён", "учитывается",
)
CALCULATION_MARKERS = (
    "расчет", "расчёт", "исходные данные", "результат расчета",
    "результат расчёта", "определено расчетом", "определено расчётом",
)
DRAWING_NAME_RE = re.compile(r"(?:пзу|ар|кр|тх)\s*[-_.]?\s*2(?:\D|$)", re.I)


def _norm(value: Any) -> str:
    return normalize_text(value).lower().replace("ё", "е")


def _split_clauses(text: str) -> list[str]:
    clean = re.sub(r"(?<=[A-Za-zА-Яа-яЁё])[-‐]\s+(?=[A-Za-zА-Яа-яЁё])", "", str(text or ""))
    clean = re.sub(r"[ \t]+", " ", clean)
    parts = re.split(r"(?<=[.;!?])\s+|\n+|\s+[•●▪◦]\s+", clean)
    result: list[str] = []
    for part in parts:
        part = re.sub(r"\s+", " ", part).strip(" ;")
        if 12 <= len(part) <= 1800:
            result.append(part)
    return result


def infer_source_modality(passage: dict[str, Any], clause: str = "") -> str:
    document = str(passage.get("document") or passage.get("source_document") or "")
    text = _norm(clause or passage.get("text") or "")
    explicit = str(passage.get("source_modality") or passage.get("modality") or "").upper()
    if explicit in {"DRAWING", "CALCULATION", "DOCUMENT", "TEXT_OR_TABLE"}:
        return explicit
    if DRAWING_NAME_RE.search(document) or any(token in text for token in ("графическая часть", "экспликация помещений", "условные обозначения", "основная надпись")):
        return "DRAWING"
    if any(marker in text for marker in CALCULATION_MARKERS):
        return "CALCULATION"
    if passage.get("document_identity") or str(passage.get("kind") or "").upper() == "DOCUMENT_IDENTITY":
        return "DOCUMENT"
    return "TEXT_OR_TABLE"


def _modality_matches(required: str, actual: str) -> bool:
    required = str(required or "TEXT_OR_TABLE").upper()
    actual = str(actual or "TEXT_OR_TABLE").upper()
    if required == "TEXT_OR_TABLE":
        return actual in {"TEXT_OR_TABLE", "CALCULATION"}
    return required == actual


def _groups_present(clause: str, groups: Iterable[Iterable[str]]) -> list[list[str]]:
    low = _norm(clause)
    words = set(re.findall(r"[a-zа-яё0-9-]{4,}", low, re.I))

    def present(token: str) -> bool:
        value = _norm(token)
        if value in low:
            return True
        # Conservative Russian inflection tolerance for artefact titles:
        # «наличие плана» must match the title «План организации рельефа».
        stem = value[:max(4, len(value) - 2)]
        return len(stem) >= 4 and any(word.startswith(stem) for word in words)

    return [list(group) for group in groups or [] if all(present(token) for token in group)]


def _local_windows(clause: str, groups: Iterable[Iterable[str]]) -> list[str]:
    """Create bounded evidence windows around pattern occurrences.

    PDF table pages are frequently flattened into one long line.  A project
    action near an unrelated row must not close a requirement elsewhere on the
    page, so windows are capped before semantic slots are evaluated.
    """
    if len(clause) <= 560:
        return [clause]
    low = _norm(clause)
    anchors: list[int] = []
    for group in groups or []:
        for token in group:
            token_norm = _norm(token)
            if not token_norm:
                continue
            anchors.extend(match.start() for match in re.finditer(re.escape(token_norm), low))
    windows: list[str] = []
    seen: set[tuple[int, int]] = set()
    for anchor in sorted(anchors)[:30]:
        start = max(0, anchor - 190)
        end = min(len(clause), anchor + 370)
        if start:
            boundary = clause.find(" ", start)
            start = boundary + 1 if 0 <= boundary < anchor else start
        if end < len(clause):
            boundary = clause.rfind(" ", anchor, end)
            end = boundary if boundary > anchor else end
        key = (start // 80, end // 80)
        if key in seen:
            continue
        seen.add(key)
        windows.append(clause[start:end].strip())
    return windows or [clause[:560]]


def resolve_typed_evidence(
    atom: dict[str, Any], recipe: dict[str, Any], passages: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve every proof slot inside one addressable source clause.

    Tokens found on different parts of a PDF page are deliberately not merged.
    Critical engineering qualifiers and the project-action marker must occur in
    the same clause as the subject evidence.
    """
    contract = dict(atom.get("evidence_contract_v2") or build_contract(atom))
    groups = list(recipe.get("evidence_groups") or [])
    expected = list(recipe.get("expected_sections") or contract.get("expected_sections") or [])
    qualifiers = [str(value) for value in contract.get("critical_qualifiers") or []]
    required_modality = str(recipe.get("required_modality") or contract.get("required_modality") or "TEXT_OR_TABLE")
    minimum_groups = int(recipe.get("minimum_groups") or 1)
    requires_design = bool(recipe.get("requires_design_marker", True))
    candidates: list[dict[str, Any]] = []
    satisfied: list[dict[str, Any]] = []

    for passage in passages or []:
        if is_assignment_source(passage):
            continue
        section = canonical_section(passage.get("section") or passage.get("document_type") or passage.get("document"))
        if not section_matches(section, expected):
            continue
        for clause_index, source_clause in enumerate(_split_clauses(str(passage.get("text") or "")), 1):
          for window_index, clause in enumerate(_local_windows(source_clause, groups), 1):
            matched_groups = _groups_present(clause, groups)
            if not matched_groups:
                continue
            low = _norm(clause)
            matched_qualifiers = [qualifier for qualifier in qualifiers if _norm(qualifier) in low]
            missing_qualifiers = [qualifier for qualifier in qualifiers if qualifier not in matched_qualifiers]
            design = any(marker in low for marker in DESIGN_MARKERS)
            negative_decision = bool(re.search(
                r"\bне\s+(?:предусмотр|предусматр|примен|установ|выполн|треб)\w*|"
                r"\bотсутствует\s+(?:необходимость|возможность)", low,
            ))
            modality = infer_source_modality(passage, clause)
            group_ok = len(matched_groups) >= minimum_groups
            modality_ok = _modality_matches(required_modality, modality)
            design_ok = (not requires_design or design) and not negative_decision
            qualifier_ok = not missing_qualifiers
            slot_gate = evaluate_semantic_slots(
                atom.get("atom_text") or atom.get("requirement_text") or recipe.get("title") or "",
                clause,
                minimum_coverage=float(recipe.get("minimum_semantic_slot_coverage") or 0.72),
            )
            semantic_ok = slot_gate["state"] == "PASSED"
            contract_ok = group_ok and modality_ok and design_ok and qualifier_ok and semantic_ok
            score = min(
                100,
                25 + 12 * len(matched_groups) + (12 if design else 0)
                + (12 if modality_ok else 0) + (14 if qualifier_ok else 0)
                + round(25 * float(slot_gate["coverage"])),
            )
            evidence = {
                "kind": "VERIFIED_CLAUSE_EVIDENCE" if contract_ok else "CANDIDATE_CLAUSE_EVIDENCE",
                "document": passage.get("document"),
                "page": passage.get("page"),
                "section": section,
                "text": clause[:1600],
                "exact_clause": clause[:1600],
                "clause_index": f"{clause_index}.{window_index}",
                "score": score,
                "matched_groups": matched_groups,
                "matched_critical_qualifiers": matched_qualifiers,
                "missing_critical_qualifiers": missing_qualifiers,
                "design_marker": design,
                "negative_project_decision": negative_decision,
                "source_modality": modality,
                "required_modality": required_modality,
                "modality_gate_state": "PASSED" if modality_ok else "BLOCKED",
                "same_clause_gate_state": "PASSED",
                "semantic_slot_gate_state": slot_gate["state"],
                "semantic_slot_gate_version": slot_gate["version"],
                "semantic_token_coverage": slot_gate["coverage"],
                "semantic_anchor_terms": slot_gate["anchors"],
                "matched_semantic_anchors": slot_gate["matched_anchors"],
                "missing_semantic_anchors": slot_gate["missing_anchors"],
                "semantic_slot_reasons": slot_gate["reasons"],
                "contract_state": "SATISFIED" if contract_ok else "UNSATISFIED",
                "semantic_gate_state": "PASSED" if contract_ok else "BLOCKED",
                "semantic_verdict": "SUPPORTS" if contract_ok else ("CONTRADICTS" if negative_decision else "CANDIDATE"),
                "judge_verdict": "SUPPORTS" if contract_ok else "INSUFFICIENT",
                "resolver_version": RESOLVER_VERSION,
            }
            candidates.append(evidence)
            if contract_ok:
                satisfied.append(evidence)

    candidates.sort(key=lambda row: int(row.get("score") or 0), reverse=True)
    satisfied.sort(key=lambda row: int(row.get("score") or 0), reverse=True)
    return {
        "resolver_version": RESOLVER_VERSION,
        "contract": contract,
        "contract_state": "SATISFIED" if satisfied else "UNSATISFIED",
        "semantic_gate_state": "PASSED" if satisfied else "BLOCKED",
        "evidence": satisfied[:4],
        "candidates": candidates[:8],
    }
