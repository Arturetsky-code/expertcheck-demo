from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


_ALLOWLIST_PATH = Path(__file__).resolve().parent / "golden" / "legacy_diagnostics.json"


_FAILED_NODEID_RE = re.compile(r"^FAILED\s+([^\s]+::[^\s]+)", re.MULTILINE)


def failed_nodeids_from_pytest_output(output: str) -> tuple[str, ...]:
    """Extract failed pytest nodeids in first-seen order without duplicates."""
    seen: set[str] = set()
    nodeids: list[str] = []
    for match in _FAILED_NODEID_RE.finditer(str(output or "")):
        nodeid = match.group(1).strip()
        if nodeid and nodeid not in seen:
            seen.add(nodeid)
            nodeids.append(nodeid)
    return tuple(nodeids)


def _load_allowlist() -> dict[str, tuple[str, ...]]:
    raw = json.loads(_ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return {
        "fixture_bound": tuple(str(x) for x in raw.get("fixture_bound", ())),
        "obsolete": tuple(str(x) for x in raw.get("obsolete", ())),
        "baseline_existing": tuple(str(x) for x in raw.get("baseline_existing", ())),
    }


def classify_failed_nodeids(failures: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Classify proven legacy diagnostics and fail closed for every unknown nodeid."""
    allowlist = _load_allowlist()
    fixture = set(allowlist["fixture_bound"])
    obsolete = set(allowlist["obsolete"])
    baseline_existing = set(allowlist["baseline_existing"])

    classified = {
        "fixture_bound": [],
        "obsolete": [],
        "baseline_existing": [],
        "blockers": [],
    }
    for raw in failures:
        nodeid = str(raw).strip()
        if nodeid in fixture:
            classified["fixture_bound"].append(nodeid)
        elif nodeid in obsolete:
            classified["obsolete"].append(nodeid)
        elif nodeid in baseline_existing:
            classified["baseline_existing"].append(nodeid)
        else:
            classified["blockers"].append(nodeid)

    return {key: tuple(values) for key, values in classified.items()}
