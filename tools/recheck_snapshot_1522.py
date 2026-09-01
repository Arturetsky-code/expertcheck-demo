#!/usr/bin/env python3
"""Repeat deterministic ExpertCheck gates from a portable project snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.project_snapshot import load_project_snapshot, recheck_project_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Повторить Quality Gate и расчёт покрытия без исходных PDF."
    )
    parser.add_argument("snapshot", type=Path, help="ExpertCheck_Цифровой_снимок.json.gz")
    args = parser.parse_args()
    result = recheck_project_snapshot(load_project_snapshot(args.snapshot.read_bytes()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if (result.get("quality_gate") or {}).get("status") == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
