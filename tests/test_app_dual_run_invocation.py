from __future__ import annotations

import ast
from pathlib import Path


def test_app_calls_dual_run_manifest_with_keyword_contract():
    source=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
    tree=ast.parse(source)
    calls=[
        node for node in ast.walk(tree)
        if isinstance(node,ast.Call)
        and isinstance(node.func,ast.Name)
        and node.func.id=="build_dual_run_manifest"
    ]
    assert len(calls)==1
    call=calls[0]
    assert not call.args
    keywords={item.arg for item in call.keywords}
    assert {"project_name","documents","findings","comparisons","assembly_rows"} <= keywords
