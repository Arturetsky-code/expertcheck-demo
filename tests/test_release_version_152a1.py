from __future__ import annotations

import ast
from pathlib import Path

from core import __version__ as core_version


def _app_version() -> str:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(app_path.read_text(encoding="utf-8"), filename=str(app_path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("VERSION is not defined in app.py")


def test_ui_and_core_identify_release_1524():
    assert _app_version() == "ExpertCheck 15.2.4 · AI Resilience & Verification Readiness"
    assert core_version == "15.2.4-ai-resilience-verification-readiness"


# Backward-compatible name imported by the cumulative 15.2.1–15.2.3 gates.
test_ui_and_core_identify_release_1522 = test_ui_and_core_identify_release_1524
