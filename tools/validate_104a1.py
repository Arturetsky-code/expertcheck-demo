#!/usr/bin/env python3
"""Reproducible end-to-end validation for ExpertCheck 10.4 Alpha 1."""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyzer import analyze_uploaded  # noqa: E402
from studio.data import structured_excel_report  # noqa: E402


VERSION = "10.4.0-alpha1-verification-kernel"


class Upload:
    """Small Streamlit-compatible wrapper around a local validation file."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self._buffer = io.BytesIO(path.read_bytes())

    def getvalue(self) -> bytes:
        return self.path.read_bytes()

    def read(self, *args, **kwargs):
        return self._buffer.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._buffer.seek(*args, **kwargs)

    def tell(self):
        return self._buffer.tell()


def _status_counts(rows: list[dict]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("status") or "") for row in rows).items()))


def _keyword_cases(rows: list[dict], keywords: tuple[str, ...]) -> list[dict]:
    result = []
    for row in rows:
        text = str(row.get("requirement_text") or row.get("requirement") or "")
        if not any(keyword.lower() in text.lower() for keyword in keywords):
            continue
        evidence = list(row.get("verification_evidence") or [])
        result.append({
            "requirement": text,
            "status": row.get("status", ""),
            "kernel": row.get("verification_kernel", ""),
            "evidence": [
                {
                    "document": item.get("document") or item.get("source_file") or "",
                    "section": item.get("document_type") or item.get("section") or "",
                    "page": item.get("page") or item.get("source_page") or "",
                    "locator": item.get("locator") or item.get("source_locator") or "",
                }
                for item in evidence[:3]
            ],
        })
    return result


def build_summary(documents: list[dict], findings: list[dict], comparisons: list[dict]) -> dict:
    first = documents[0] if documents else {}
    assignment = list(first.get("assignment_compliance") or [])
    checklist = list((first.get("automatic_checklist_review") or {}).get("results") or [])
    checklist_actionable = [row for row in checklist if not row.get("is_heading")]
    baseline = list(first.get("composition_baseline") or [])
    gate = dict(first.get("report_quality_gate") or {})
    pipeline_errors = []
    for document in documents:
        for error in document.get("pipeline_errors") or []:
            if error not in pipeline_errors:
                pipeline_errors.append(error)

    positions = [str(row.get("Позиция по ГП") or "") for row in baseline]
    names = [str(row.get("Наименование объекта") or "") for row in baseline]
    kernel_counts = Counter(str(row.get("verification_kernel") or "") for row in assignment)
    kernel_counts.pop("", None)

    return {
        "version": VERSION,
        "input": {
            "documents": len(documents),
            "document_types": dict(sorted(Counter(str(row.get("Тип документа") or "") for row in documents).items())),
        },
        "output": {
            "findings": len(findings),
            "comparisons": len(comparisons),
            "pipeline_errors": pipeline_errors,
        },
        "registry": {
            "objects": len(baseline),
            "positions": positions,
            "contains_position_5": "5" in positions,
            "contains_position_9": "9" in positions,
            "contains_position_4_17": "4.17" in positions,
            "contains_ethernet_legend": any("ethernet" in name.lower() for name in names),
            "position_4_18_names": [name for row, name in zip(baseline, names) if str(row.get("Позиция по ГП") or "") == "4.18"],
        },
        "assignment": {
            "total": len(assignment),
            "statuses": _status_counts(assignment),
            "kernels": dict(sorted(kernel_counts.items())),
            "flood_protection": _keyword_cases(assignment, ("подтоп", "затоп", "павод")),
            "equipment": _keyword_cases(assignment, ("shantui", "sinotr", "sino track", "погрузчик")),
            "capacity": _keyword_cases(assignment, ("500 т/ч", "500 т", "производительност")),
            "grounding": _keyword_cases(assignment, ("заземлен", "молниезащит")),
        },
        "checklists": {
            "total": len(checklist_actionable),
            "statuses": _status_counts(checklist_actionable),
            "wrong_section_evidence": int(gate.get("wrong_section_evidence", 0) or 0),
        },
        "cross_section": {
            "total": len(comparisons),
            "statuses": _status_counts(comparisons),
        },
        "quality_gate": gate,
        "deep_evidence": dict(first.get("deep_evidence_review") or {}).get("metrics") or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path, help="Directory containing the validation PDF/XML set")
    parser.add_argument("--output", type=Path, default=ROOT / "VALIDATION_104_ALPHA1.json")
    parser.add_argument("--reports", type=Path, help="Optional directory for three XLSX validation reports")
    args = parser.parse_args()

    source_paths = sorted(
        path for path in args.source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".xml"}
    )
    if not source_paths:
        raise SystemExit(f"No PDF/XML files found in {args.source_dir}")

    documents, findings, comparisons = analyze_uploaded(
        [Upload(path) for path in source_paths],
        ROOT,
        ai_options={"enabled": False},
    )
    summary = build_summary(documents, findings, comparisons)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.reports:
        args.reports.mkdir(parents=True, exist_ok=True)
        checklist = list((documents[0].get("automatic_checklist_review") or {}).get("results") or []) if documents else []
        report_names = {
            "manager": "ExpertCheck_Резюме_руководителя_10.4A1.xlsx",
            "gip": "ExpertCheck_Отчёт_ГИПа_10.4A1.xlsx",
            "technical": "ExpertCheck_Техническое_приложение_10.4A1.xlsx",
        }
        for kind, name in report_names.items():
            payload = structured_excel_report(
                "Контрольный комплект ДСК",
                VERSION,
                documents,
                findings,
                comparisons,
                report_kind=kind,
                checklist_results=checklist,
            )
            (args.reports / name).write_bytes(payload)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["quality_gate"].get("status") == "PASSED" and not summary["output"]["pipeline_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
