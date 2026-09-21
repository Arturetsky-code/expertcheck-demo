from __future__ import annotations

import ast
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[2] / "app.py"


def _tree() -> ast.Module:
    return ast.parse(APP_PATH.read_text(encoding="utf-8"))


def test_studio_context_declares_workspace_store_and_all_constructors_supply_it():
    tree = _tree()
    studio_context = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "StudioContext"
    )
    fields = {
        node.target.id
        for node in studio_context.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert {"workspace_store", "config_dir", "analyze"} <= fields

    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "StudioContext"
    ]
    assert calls
    for call in calls:
        keywords = {kw.arg for kw in call.keywords if kw.arg}
        assert {"workspace_store", "config_dir", "analyze"} <= keywords


def test_autosave_uses_workspace_store_save_project_contract_explicitly():
    tree = _tree()
    autosave = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_autosave_current_project"
    )
    calls = [
        node for node in ast.walk(autosave)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "save_project"
    ]
    assert len(calls) == 1
    keywords = {kw.arg for kw in calls[0].keywords if kw.arg}
    assert {"owner_id", "project_id", "name", "payload", "app_version"} <= keywords


def test_fresh_project_routes_to_upload_before_dataframe_empty_access():
    project_path = Path(__file__).resolve().parents[2] / "studio" / "pages" / "project.py"
    source = project_path.read_text(encoding="utf-8")
    assert "if docs is None or docs.empty:" in source


def test_project_page_runtime_contract_is_satisfied_by_studio_context():
    project_path = Path(__file__).resolve().parents[2] / "studio" / "pages" / "project.py"
    project_source = project_path.read_text(encoding="utf-8")
    tree = _tree()
    studio_context = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "StudioContext"
    )
    fields = {
        node.target.id
        for node in studio_context.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert "ctx.analyze" in project_source
    assert "ctx.config_dir" in project_source
    assert {"analyze", "config_dir"} <= fields
