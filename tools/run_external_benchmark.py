from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.external_benchmark import build_corpus_manifest, evaluate_benchmark, load_benchmark


def _json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="ExpertCheck external/offline benchmark runner")
    sub = parser.add_subparsers(dest="command", required=True)

    index = sub.add_parser("index", help="Create or incrementally update a corpus hash manifest")
    index.add_argument("--corpus", required=True)
    index.add_argument("--cache", required=True)
    index.add_argument("--output")

    evaluate = sub.add_parser("evaluate", help="Evaluate exported ExpertCheck results against external cases")
    evaluate.add_argument("--benchmark", required=True)
    evaluate.add_argument("--before-results")
    evaluate.add_argument("--after-results")
    evaluate.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "index":
        result = build_corpus_manifest(args.corpus, args.cache)
        target = Path(args.output or args.cache)
    else:
        if not args.before_results and not args.after_results:
            parser.error("evaluate requires --before-results and/or --after-results")
        result = evaluate_benchmark(
            load_benchmark(args.benchmark),
            before_payload=_json(args.before_results) if args.before_results else None,
            after_payload=_json(args.after_results) if args.after_results else None,
        )
        target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in ("version", "benchmark_id", "cases", "evaluations", "file_count", "total_bytes", "summary") if key in result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

