from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


_ALLOWLIST_PATH = Path(__file__).resolve().parent / "golden" / "legacy_diagnostics.json"


def _load_allowlist() -> dict[str, tuple[str, ...]]:
    raw = json.loads(_ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return {
        "fixture_bound": tuple(str(x) for x in raw.get("fixture_bound", ())),
        "obsolete": tuple(str(x) for x in raw.get("obsolete", ())),
    }


def classify_failed_nodeids(failures: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Classify known legacy diagnostics and fail closed for every unknown nodeid."""
    allowlist = _load_allowlist()
    fixture = set(allowlist["fixture_bound"])
    obsolete = set(allowlist["obsolete"])

    classified = {"fixture_bound": [], "obsolete": [], "blockers": []}
    for raw in failures:
        nodeid = str(raw).strip()
        if nodeid in fixture:
            classified["fixture_bound"].append(nodeid)
        elif nodeid in obsolete:
            classified["obsolete"].append(nodeid)
        else:
            classified["blockers"].append(nodeid)

    return {key: tuple(values) for key, values in classified.items()}
