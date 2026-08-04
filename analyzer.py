"""Backward-compatible facade for ExpertCheck UI."""
from legacy_analyzer import Finding, load_json, compare_findings
from core.pipeline import analyze_uploaded_core

def analyze_uploaded(files, config_dir):
    return analyze_uploaded_core(files, config_dir)

__all__ = ["Finding", "load_json", "compare_findings", "analyze_uploaded"]
