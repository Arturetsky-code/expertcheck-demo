from __future__ import annotations

"""Telemetry reconciliation for ExpertCheck 18.4 advisory dual review."""

from collections import Counter
from typing import Any, Iterable

from core import semantic_evidence_engine as see

_INSTALLED = False


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    current = see.run_semantic_evidence_engine
    if getattr(current, "_expertcheck_184_audit_reconciled", False):
        _INSTALLED = True
        return

    def audited_run(
        rows: list[dict[str, Any]],
        *,
        fact_graph: dict[str, Any],
        page_corpus: Iterable[dict[str, Any]] = (),
        judge_provider: Any = None,
        critic_provider: Any = None,
        level: str = "off",
        limit: int = 0,
        progress_callback: Any = None,
        checkpoint: dict[str, Any] | None = None,
        candidate_cap: int = 0,
    ) -> dict[str, Any]:
        result = current(
            rows,
            fact_graph=fact_graph,
            page_corpus=page_corpus,
            judge_provider=judge_provider,
            critic_provider=critic_provider,
            level=level,
            limit=limit,
            progress_callback=progress_callback,
            checkpoint=checkpoint,
            candidate_cap=candidate_cap,
        )
        if not result.get("advisory_dual_review"):
            return result

        levels = Counter(str(row.get("evidence_level") or "L0") for row in rows or [])
        result["evidence_levels"] = {
            level_name: levels.get(level_name, 0)
            for level_name in getattr(see, "EVIDENCE_LEVELS", ("L0", "L1", "L2", "L3", "L4", "L5"))
        }
        result["evidence_ready"] = levels.get("L3", 0) + levels.get("L4", 0) + levels.get("L5", 0)
        result["strictly_completed"] = levels.get("L5", 0)

        for event in result.get("execution_log") or []:
            if not event.get("selected"):
                continue
            if event.get("judge_response_received") or event.get("critic_response_received"):
                event["execution_mode"] = "ADVISORY_DUAL_REVIEW"
            if event.get("critic_response_received"):
                event["consensus_state"] = "ADVISORY_DUAL_REVIEW"
                event["selection_reason"] = (
                    "Judge и независимый Critic реально выполнили проверку; "
                    "результат удержан на L4 до квалификации точных provider/model маршрутов."
                )
        result["telemetry_reconciled"] = True
        return result

    audited_run._expertcheck_184_audit_reconciled = True  # type: ignore[attr-defined]
    see.run_semantic_evidence_engine = audited_run

    # atomic_verification_engine keeps a direct imported reference.
    from core import atomic_verification_engine as ave
    ave.run_semantic_evidence_engine = audited_run
    _INSTALLED = True
