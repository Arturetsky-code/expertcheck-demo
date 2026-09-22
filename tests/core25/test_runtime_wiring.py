from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _parse(path: str) -> ast.Module:
    return ast.parse((ROOT / path).read_text(encoding="utf-8"))


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_real_pipeline_invokes_core25_runtime_bridge_and_persists_public_payload():
    source = _source("core/pipeline.py")
    assert "from core25.runtime_bridge import run_assignment_runtime" in source
    assert "run_assignment_runtime(" in source
    assert 'doc["assignment_core25_compliance"]' in source
    assert 'doc["assignment_core25_summary"]' in source
    assert 'doc["assignment_core25_runtime"]' in source


def test_streamlit_build_identifies_25_alpha1_and_assignment_surfaces_use_core25_selector():
    app = _source("app.py")
    project = _source("studio/pages/project.py")
    data = _source("studio/data.py")
    results = _source("studio/pages/results_center.py")

    assert "ExpertCheck 25.2 Alpha 1" in app
    assert "Coverage Breakthrough" in app
    assert "public_assignment_payload" in project
    assert "public_assignment_payload" in data
    assert "public_assignment_payload" in results
