from __future__ import annotations

from typing import Any

from .requirement_contracts import coverage_archetype


FACTORY_VERSION = "16.0-specialist-checker-factory"


def checker_profile(atom: dict[str, Any], recipe: dict[str, Any] | None = None) -> dict[str, Any]:
    """Select the narrowest checker family that can safely handle an atom.

    The factory does not execute a check and cannot promote a verdict.  It is a
    routing contract shared by deterministic checkers and the Semantic Evidence
    Engine.  Unsupported normative/application questions remain specialist-only.
    """
    recipe = dict(recipe or {})
    kind = str(atom.get("atomic_kind") or "").upper()
    method = str(recipe.get("check_method") or "").upper()
    modality = str(
        (atom.get("evidence_contract_v2") or {}).get("required_modality")
        or recipe.get("required_modality") or "TEXT_OR_TABLE"
    ).upper()
    archetype = coverage_archetype(atom, recipe)

    if kind == "VALUE_COMPARISON" or method in {"VALUE_COMPARISON", "ENGINEERING_VALUE_CROSSCHECK", "STRUCTURED_COMPARISON"}:
        family, mode = "NUMERIC_VALUE_COMPARISON", "DETERMINISTIC"
    elif kind == "EQUIPMENT_IDENTITY" or "IDENTITY" in method:
        family, mode = "EQUIPMENT_IDENTITY", "DETERMINISTIC"
    elif kind == "PROHIBITION" or "PROHIBITION" in method:
        family, mode = "EXPLICIT_PROHIBITION", "DETERMINISTIC"
    elif kind in {"TRACEABILITY", "DOCUMENT_DELIVERABLE"} or "SET_COMPARISON" in method:
        family, mode = "DOCUMENT_TRACEABILITY", "CONSENSUS"
    elif kind == "NORMATIVE_CLAUSE" or "NORMATIVE" in method or "CLAUSE" in method:
        family, mode = "NORMATIVE_CLAUSE", "SPECIALIST"
    elif kind == "APPLICABILITY_DECLARATION":
        family, mode = "APPLICABILITY", "SPECIALIST"
    elif method in {"ENGINEERING_PARAMETER_PRESENCE", "DOCUMENT_CONTENT_PRESENCE"}:
        family, mode = "FEATURE_PRESENCE", "DETERMINISTIC"
    elif method == "DRAWING_PRESENCE_CHECK" or modality == "DRAWING":
        family, mode = "DRAWING_EVIDENCE", "CONSENSUS"
    elif method == "CALCULATION_PRESENCE" or modality == "CALCULATION":
        family, mode = "CALCULATION_EVIDENCE", "CONSENSUS"
    else:
        family, mode = "SEMANTIC_PROJECT_DECISION", "CONSENSUS"

    consensus_eligible = mode == "CONSENSUS"
    return {
        "factory_version": FACTORY_VERSION,
        "checker_family": family,
        "checker_mode": mode,
        "coverage_archetype": archetype,
        "required_modality": modality,
        "consensus_eligible": consensus_eligible,
        "mandatory_gates": [
            "ENTITY_BINDING", "PROPERTY_BINDING", "MODALITY", "CRITICAL_QUALIFIERS",
            "SEMANTIC_SLOTS", "ADVERSARIAL_REVIEW",
        ],
        "categorical_policy": (
            "SPECIALIZED_DETERMINISTIC_CHECKER"
            if mode == "DETERMINISTIC"
            else "INDEPENDENT_AI_CONSENSUS_PLUS_CODE_GATE"
            if mode == "CONSENSUS"
            else "SPECIALIST_DECISION_REQUIRED"
        ),
    }
