from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .normalization import normalize_text
from .verification_recipe_critic import critique_recipe
from .verification_regression_gate import regression_gate


COMPILER_VERSION = "2.0-atomic-recipes"


def _norm(value: Any) -> str:
    return normalize_text(value).lower().replace("ё", "е")


def _groups_present(text: str, groups: Iterable[Iterable[str]]) -> list[list[str]]:
    low = _norm(text)
    return [list(group) for group in groups or [] if all(_norm(token) in low for token in group)]


class VerificationRecipeCompilerV2:
    """Compile one executable and fail-closed recipe per atomic condition.

    The compiler is universal: project profiles may add patterns, but they do
    not change the evidence gate.  A recipe that fails critic or regression
    testing remains experimental and cannot produce a categorical verdict.
    """

    def __init__(self, knowledge_root: str | Path):
        root = Path(knowledge_root)
        path = root / "atomic_verification_patterns_v1.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"patterns": []}
        self.pattern_version = str(payload.get("version") or "")
        self.patterns = list(payload.get("patterns") or [])

    def _pattern(self, text: str) -> dict[str, Any] | None:
        ranked: list[tuple[int, dict[str, Any]]] = []
        for pattern in self.patterns:
            hits = _groups_present(text, pattern.get("triggers") or [])
            if hits:
                ranked.append((sum(len(group) for group in hits), pattern))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return dict(ranked[0][1]) if ranked else None

    @staticmethod
    def _base(atom: dict[str, Any], pattern: dict[str, Any] | None) -> dict[str, Any]:
        kind = str(atom.get("atomic_kind") or "PRESENCE_REQUIREMENT").upper()
        contract = atom.get("evidence_contract_v2") or {}
        sections = list((pattern or {}).get("expected_sections") or atom.get("expected_sections") or contract.get("expected_sections") or [])
        title = str(atom.get("atom_text") or atom.get("requirement_text") or "").strip()
        recipe: dict[str, Any] = {
            "recipe_id": f"AR-{atom.get('atom_id') or atom.get('requirement_id')}",
            "compiler_version": COMPILER_VERSION,
            "domain": str(atom.get("domain") or "assignment"),
            "title": title,
            "atomic_kind": kind,
            "expected_sections": sections,
            "pattern_id": str((pattern or {}).get("pattern_id") or ""),
            "required_evidence_slots": ["SOURCE_DOCUMENT", "PAGE", "SECTION", "PROJECT_SCOPE"],
            "abstain_policy": "NOT_FOUND, weak semantic similarity, wrong section, missing source locator or ambiguous entity binding never prove fulfilment or violation.",
            "confidence": 0.82,
        }
        if kind == "VALUE_COMPARISON":
            recipe.update({
                "verification_level": "L2_VALUE", "check_method": "VALUE_COMPARISON",
                "required_evidence": ["STRUCTURED_VALUE", "STRUCTURED_COMPARISON"],
                "required_evidence_slots": recipe["required_evidence_slots"] + ["ENTITY_BINDING", "OBSERVED_VALUE", "UNIT"],
                "confidence": 0.91,
            })
        elif kind == "EQUIPMENT_IDENTITY":
            recipe.update({
                "verification_level": "L2_VALUE", "check_method": "EQUIPMENT_IDENTITY_COMPARISON",
                "required_evidence": ["STRUCTURED_COMPARISON"],
                "required_evidence_slots": recipe["required_evidence_slots"] + ["ENTITY_BINDING", "OBSERVED_IDENTITY"],
                "confidence": 0.9,
            })
        elif kind == "TOPOLOGY_REQUIREMENT":
            recipe.update({
                "verification_level": "L3_CROSS_CHECK", "check_method": "STRUCTURED_COMPARISON",
                "required_evidence": ["STRUCTURED_COMPARISON", "VERIFIED_ENGINEERING_EVIDENCE"],
                "required_evidence_slots": recipe["required_evidence_slots"] + ["TOPOLOGY", "OBSERVED_VALUE"],
                "confidence": 0.9,
            })
        elif kind == "PROHIBITION":
            recipe.update({
                "verification_level": "L3_CROSS_CHECK", "check_method": "PROHIBITION_EXPLICIT_CONTRADICTION",
                "required_evidence": ["STRUCTURED_COMPARISON"],
                "required_evidence_slots": recipe["required_evidence_slots"] + ["EXPLICIT_PROJECT_DECISION"],
                "evidence_groups": list((pattern or {}).get("evidence_groups") or []),
                "minimum_groups": int((pattern or {}).get("minimum_groups") or 1),
                "requires_design_marker": bool((pattern or {}).get("requires_design_marker", True)),
                "confidence": 0.86,
            })
        elif kind == "NORMATIVE_CLAUSE":
            recipe.update({
                "verification_level": "L5_ENGINEERING_COMPLIANCE", "check_method": "CLAUSE_ADDRESSED_NORMATIVE_CHECK",
                "required_evidence": ["VERIFIED_CLAUSE", "NORMATIVE_EVIDENCE"],
                "required_evidence_slots": recipe["required_evidence_slots"] + ["NTD_DOCUMENT", "NTD_CLAUSE", "CLAUSE_VALIDITY"],
                "confidence": 0.84,
            })
        elif kind in {"TRACEABILITY", "DOCUMENT_DELIVERABLE"}:
            recipe.update({
                "verification_level": "L4_COMPLETENESS", "check_method": "SET_COMPARISON",
                "required_evidence": ["VERIFIED_SET_EVIDENCE", "STRUCTURED_COMPLETENESS"],
                "required_evidence_slots": recipe["required_evidence_slots"] + ["REQUIRED_ARTIFACT", "IDENTIFIED_ARTIFACT"],
                "confidence": 0.82,
            })
        elif pattern:
            recipe.update({
                "verification_level": "L5_ENGINEERING_COMPLIANCE", "check_method": "ATOMIC_PATTERN_PRESENCE",
                "required_evidence": ["VERIFIED_ENGINEERING_EVIDENCE"],
                "required_evidence_slots": recipe["required_evidence_slots"] + ["PROJECT_ACTION_MARKER", "PATTERN_EVIDENCE_GROUPS"],
                "evidence_groups": list(pattern.get("evidence_groups") or []),
                "minimum_groups": int(pattern.get("minimum_groups") or 1),
                "requires_design_marker": bool(pattern.get("requires_design_marker", True)),
                "confidence": 0.88,
            })
        else:
            recipe.update({
                "verification_level": "L5_ENGINEERING_COMPLIANCE", "check_method": "SPECIALIST_REVIEW",
                "required_evidence": ["VERIFIED_ENGINEERING_EVIDENCE"],
                "confidence": 0.66,
            })
        return recipe

    def compile(self, atom: dict[str, Any]) -> dict[str, Any]:
        pattern = self._pattern(str(atom.get("atom_text") or atom.get("requirement_text") or ""))
        recipe = self._base(atom, pattern)
        recipe.update(critique_recipe(recipe))
        recipe.update(regression_gate(recipe))
        recipe["executable"] = bool(recipe.get("critic_pass") and recipe.get("regression_pass"))
        recipe["pattern_version"] = self.pattern_version
        return recipe

    def compile_many(self, atoms: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.compile(atom) for atom in atoms or []]
