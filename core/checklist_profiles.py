from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROFILE_ALIASES = {
    "ПД": "PD",
    "PD": "PD",
    "PROJECT": "PD",
    "PROJECT_DOCUMENTATION": "PD",
    "РД": "RD",
    "RD": "RD",
    "WORKING": "RD",
    "WORKING_DOCUMENTATION": "RD",
}

PROFILE_FILES = {
    "PD": "pd.json",
    "RD": "rd.json",
}


def normalize_profile_code(value: Any) -> str:
    raw = str(value or "").strip().upper()
    return PROFILE_ALIASES.get(raw, raw)


class ChecklistProfileRegistry:
    """Loads stage-specific RAM checklist profiles without touching the legacy catalog."""

    def __init__(self, knowledge_root: str | Path):
        root = Path(knowledge_root)
        self.root = root / "checklist_profiles"

    def available(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for code in PROFILE_FILES:
            try:
                payload = self._load_payload(code)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            result.append({
                "profile_code": code,
                "stage": payload.get("stage") or code,
                "title": payload.get("title") or "",
                "question_count": int(payload.get("question_count") or 0),
                "discipline_count": int(payload.get("discipline_count") or 0),
            })
        return result

    def load(self, profile_code: str) -> list[dict[str, Any]]:
        code = normalize_profile_code(profile_code)
        payload = self._load_payload(code)
        questions = payload.get("questions")
        if not isinstance(questions, list):
            raise ValueError(f"Checklist profile {code} has no questions list")

        normalized: list[dict[str, Any]] = []
        seen: set[int] = set()
        for index, raw in enumerate(questions, 1):
            if not isinstance(raw, dict):
                raise ValueError(f"Checklist profile {code}: row {index} is not an object")
            source_id = raw.get("source_question_id", raw.get("id"))
            try:
                source_id = int(source_id)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Checklist profile {code}: invalid question id at row {index}") from exc
            if source_id <= 0 or source_id in seen:
                raise ValueError(f"Checklist profile {code}: duplicate/invalid question id {source_id}")
            seen.add(source_id)

            priority = int(raw.get("priority") or 0)
            if priority not in {1, 2, 3}:
                raise ValueError(f"Checklist profile {code}: invalid priority for question {source_id}")

            question = str(raw.get("question") or "").strip()
            discipline = str(raw.get("discipline") or "").strip()
            criteria = str(raw.get("criteria") or "").strip()
            if not question or not discipline:
                raise ValueError(f"Checklist profile {code}: incomplete question {source_id}")

            expected_sections = raw.get("expected_sections") or []
            if isinstance(expected_sections, str):
                expected_sections = [expected_sections]
            expected_sections = list(dict.fromkeys(
                str(value).strip() for value in expected_sections if str(value or "").strip()
            ))

            row = {
                **raw,
                "id": source_id,
                "source_question_id": source_id,
                "checklist_item_id": source_id,
                "checklist_profile": code,
                "source_file": f"RAM_CHECKLIST_{code}",
                "sheet": payload.get("stage") or code,
                "item_no": str(source_id),
                "section": discipline,
                "discipline": discipline,
                "priority": priority,
                "question": question,
                "criteria": criteria,
                "expected_sections": expected_sections,
            }
            normalized.append(row)

        expected_count = int(payload.get("question_count") or len(normalized))
        if expected_count != len(normalized):
            raise ValueError(
                f"Checklist profile {code}: expected {expected_count} questions, got {len(normalized)}"
            )
        return normalized

    def summary(self, profile_code: str) -> dict[str, Any]:
        rows = self.load(profile_code)
        disciplines = sorted({str(row.get("discipline") or "") for row in rows})
        priorities = {
            priority: sum(int(row.get("priority") or 0) == priority for row in rows)
            for priority in (1, 2, 3)
        }
        return {
            "profile_code": normalize_profile_code(profile_code),
            "question_count": len(rows),
            "discipline_count": len(disciplines),
            "disciplines": disciplines,
            "priorities": priorities,
        }

    def _load_payload(self, profile_code: str) -> dict[str, Any]:
        code = normalize_profile_code(profile_code)
        filename = PROFILE_FILES.get(code)
        if not filename:
            raise ValueError(f"Unknown checklist profile: {profile_code}")
        path = self.root / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Checklist profile {code} must be a JSON object")
        stored_code = normalize_profile_code(payload.get("profile_code"))
        if stored_code != code:
            raise ValueError(f"Checklist profile mismatch: requested {code}, stored {stored_code}")
        return payload
