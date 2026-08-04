"""Backward-compatible facade for ExpertCheck UI."""
from __future__ import annotations

try:
    from legacy_analyzer import Finding, load_json, compare_findings
    from core.pipeline import analyze_uploaded_core
except ModuleNotFoundError as exc:
    missing = getattr(exc, "name", "неизвестный модуль")
    raise ModuleNotFoundError(
        f"Не загружен обязательный компонент ExpertCheck Core 2.0: {missing}. "
        "Убедитесь, что папки core и knowledge находятся в корне GitHub-репозитория рядом с app.py."
    ) from exc

def analyze_uploaded(files, config_dir):
    return analyze_uploaded_core(files, config_dir)

__all__ = ["Finding", "load_json", "compare_findings", "analyze_uploaded"]
