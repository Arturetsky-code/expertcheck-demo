from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from .atomic_verification_engine import (
    aggregate_atomic_results,
    atomic_evidence_facts,
    parent_assignment_summary,
    verify_atomic_requirements,
    verify_checklist_rows,
)
from .coverage_matrix import build_coverage_matrix
from .deep_evidence_intelligence import (
    apply_deep_evidence_decisions, compact_deep_evidence_review,
    run_deep_evidence_review,
)
from .project_review_planner import build_review_plan
from .project_snapshot import corpus_fingerprint
from .report_quality_gate import validate_review_plan
from .semantic_evidence_engine import build_semantic_project_graph
from .verification_core import domain_summary
from .verified_verdict_gate import enforce_project_verdicts
from .ai_continuation_ledger import (
    LEDGER_VERSION,
    queue_status_from_document,
    reconcile_domain_audit,
)


CONTINUATION_VERSION = "18.4.1-cumulative-ai-ledger"


def _progress(callback: Callable[..., Any] | None, value: int, stage: str, detail: str) -> None:
    if callback is None:
        return
    try:
        callback(value, stage, detail)
    except Exception:
        pass


def _checklist_summary(review: dict[str, Any]) -> dict[str, Any]:
    rows = list(review.get("results") or [])
    actionable = [row for row in rows if not row.get("is_heading")]
    summary = dict(review.get("summary") or {})
    domain = domain_summary(rows, "checklist")
    summary.update({
        "yes": sum(str(row.get("status") or "") == "Да" for row in actionable),
        "no": sum(str(row.get("status") or "") == "Нет" for row in actionable),
        "review": sum(str(row.get("status") or "") == "Требует проверки" for row in actionable),
        "unsupported": sum(str(row.get("status") or "") == "Не проверено системой" for row in actionable),
        "verified_completed": domain["completed"],
        "system_limitations": domain["system_limitations"],
        "review_questions": domain["review_questions"],
        "automatic_coverage_pct": domain["automatic_coverage_pct"],
        "evidence_coverage_pct": domain["evidence_coverage_pct"],
        "semantic_consensus_completed": domain["semantic_consensus_completed"],
    })
    return summary


def continuation_pending(
    doc: dict[str, Any],
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return cumulative package/role counters from the persisted checkpoint."""
    return queue_status_from_document(doc, checkpoint)


def continue_semantic_analysis(
    result: tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]],
    *, knowledge_root: str, judge_provider: Any = None, critic_provider: Any = None,
    semantic_level: str = "extended", checkpoint: dict[str, Any] | None = None,
    progress_callback: Callable[..., Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Continue Judge/Critic from a stored corpus without reparsing source files.

    The input result is copied before mutation.  Checkpoints are bound to the
    exact page-corpus fingerprint, so responses cannot leak across projects.
    Every public metric and the report quality gate are rebuilt after the run.
    """
    if not result or len(result) != 3:
        raise ValueError("Нет результата проекта для продолжения AI-проверки.")
    source_documents, source_findings, source_comparisons = result
    # Copy only structures that this continuation mutates.  A full deepcopy of
    # the complete project evidence graph can briefly double memory on large
    # Streamlit Cloud projects and defeat the purpose of snapshot continuation.
    documents = [dict(row) for row in source_documents]
    findings = list(source_findings)
    comparisons = list(source_comparisons)
    if not documents:
        raise ValueError("В результате проекта отсутствуют документы.")
    first = documents[0]
    previous_semantic = dict(first.get("semantic_evidence_engine") or {})
    snapshot = dict(first.get("analysis_snapshot") or {})
    page_corpus = list(snapshot.get("page_corpus") or [])
    if not page_corpus:
        raise ValueError("Цифровой снимок не содержит корпуса страниц; требуется повторный анализ комплекта.")

    snapshot_id = str(snapshot.get("snapshot_id") or corpus_fingerprint(page_corpus))
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    if checkpoint.get("_project_fingerprint") != snapshot_id:
        checkpoint.clear()
        checkpoint["_project_fingerprint"] = snapshot_id
    assignment_checkpoint = checkpoint.setdefault("assignment", {})
    checklist_checkpoint = checkpoint.setdefault("checklist", {})

    budget = dict(first.get("coverage_acceleration_budget") or {})
    assignment_target = int(budget.get("assignment_semantic_limit") or 200)
    checklist_target = min(50, int(budget.get("checklist_semantic_limit") or 50))
    assignment_limit = min(
        assignment_target,
        int(budget.get("continuation_assignment_batch_limit") or 8),
    )
    checklist_limit = min(
        checklist_target,
        int(budget.get("continuation_checklist_batch_limit") or 16),
    )
    fact_graph = dict(first.get("universal_project_fact_graph") or {})
    fact_graph["passages"] = page_corpus
    graph = dict(first.get("atomic_requirement_graph") or {})
    atoms = deepcopy(list(graph.get("atoms") or []))
    if not atoms:
        atoms = deepcopy(list(first.get("assignment_atomic_compliance") or []))
    parent_rows = list(first.get("assignment_compliance") or [])

    def semantic_progress(domain: str):
        def callback(role: str, completed: int, total: int) -> None:
            role_label = "Judge" if role == "JUDGE" else "Critic"
            base = 15 if domain == "assignment" else 50
            _progress(
                progress_callback, base,
                "Продолжение AI-проверки",
                f"{domain}: {role_label} — обработано {completed} из {total}",
            )
        return callback

    _progress(progress_callback, 5, "Продолжение AI-проверки", "Восстанавливаем точный корпус и checkpoint")
    assignment_atomic = verify_atomic_requirements(
        atoms,
        knowledge_root=knowledge_root,
        fact_graph=fact_graph,
        page_corpus=page_corpus,
        judge_provider=judge_provider,
        critic_provider=critic_provider,
        semantic_level=semantic_level,
        semantic_limit=assignment_limit,
        semantic_checkpoint=assignment_checkpoint,
        semantic_progress_callback=semantic_progress("Задание"),
    )
    assignment_rows = aggregate_atomic_results(parent_rows, assignment_atomic)

    _progress(progress_callback, 48, "Продолжение AI-проверки", "Продолжаем очередь корпоративных чек-листов")
    automatic_review = deepcopy(dict(first.get("automatic_checklist_review") or {}))
    checklist_atomic = verify_checklist_rows(
        list(automatic_review.get("results") or []),
        knowledge_root=knowledge_root,
        fact_graph=fact_graph,
        page_corpus=page_corpus,
        judge_provider=judge_provider,
        critic_provider=critic_provider,
        semantic_level=semantic_level,
        semantic_limit=checklist_limit,
        semantic_checkpoint=checklist_checkpoint,
        semantic_progress_callback=semantic_progress("Чек-листы"),
        # Continuation must see the full L4 queue. The per-click network budget
        # is already bounded by semantic_limit/checklist_limit. Capping the
        # candidate set at the historical initial-review target (50) made any
        # additional eligible packets permanently unreachable after checkpoint
        # resume (Test 77: 60 eligible, first 50 completed, last 10 deadlocked).
        semantic_candidate_cap=0,
    )
    automatic_review["atomic_verification"] = checklist_atomic

    normative_rows = deepcopy(list(first.get("normative_compliance_audit") or []))
    gate_inputs = dict(snapshot.get("quality_gate_inputs") or {})
    gate_comparisons = list(gate_inputs.get("comparisons") or comparisons)
    evidence_plan = build_review_plan(
        assignment_rows=assignment_atomic,
        normative_rows=normative_rows,
        checklist_review=automatic_review,
        comparisons=[],
    )
    _progress(progress_callback, 82, "Контроль доказательств", "Повторяем fail-closed проверку адресных доказательств")
    deep_review = run_deep_evidence_review(
        evidence_plan.get("items") or [],
        documents=documents,
        facts=list(findings) + atomic_evidence_facts(assignment_atomic) + atomic_evidence_facts(checklist_atomic.get("atoms") or []),
        comparisons=gate_comparisons,
        page_corpus=page_corpus,
    )
    deep_review["merge_summary"] = apply_deep_evidence_decisions(
        deep_review,
        assignment_rows=assignment_atomic,
        normative_rows=normative_rows,
        checklist_review=automatic_review,
    )
    verified_core_gate = enforce_project_verdicts(
        assignment_rows=assignment_atomic,
        normative_rows=normative_rows,
        checklist_review=automatic_review,
        comparisons=gate_comparisons,
    )
    assignment_rows = aggregate_atomic_results(parent_rows, assignment_atomic)
    from .verified_verdict_gate import enforce_verified_verdicts
    assignment_parent_gate = enforce_verified_verdicts(assignment_rows, domain="assignment")
    verified_core_gate["domains"]["assignment_parent"] = assignment_parent_gate
    for metric in ("checked", "passed", "blocked"):
        verified_core_gate[metric] += assignment_parent_gate[metric]
    deep_review["verified_core_gate"] = verified_core_gate
    deep_review = compact_deep_evidence_review(deep_review)
    assignment_summary = parent_assignment_summary(
        assignment_rows, assignment_atomic, graph.get("summary") or {},
    )
    assignment_audit = dict((assignment_atomic[0] if assignment_atomic else {}).get("semantic_engine_audit") or {})
    previous_root_ledger = checkpoint.get("_ledger") if isinstance(checkpoint.get("_ledger"), dict) else {}
    previous_ledger_domains = dict((previous_root_ledger or {}).get("domains") or {})
    assignment_audit, assignment_ledger = reconcile_domain_audit(
        assignment_audit,
        rows=assignment_atomic,
        checkpoint_domain=assignment_checkpoint,
        previous_audit=dict(previous_semantic.get("assignment") or {}),
        previous_ledger_domain=dict(previous_ledger_domains.get("assignment") or {}),
    )
    if assignment_atomic:
        assignment_atomic[0]["semantic_engine_audit"] = assignment_audit
    assignment_summary["ai_evidence_review"] = {
        "reviewed": assignment_audit.get("judge_responses", 0),
        "confirmed": assignment_audit.get("promoted_verified", 0),
        "contradicted": assignment_audit.get("project_findings", 0),
        "semantic_evidence_engine": assignment_audit,
    }
    automatic_review["summary"] = _checklist_summary(automatic_review)
    review_plan = build_review_plan(
        assignment_rows=assignment_rows,
        normative_rows=normative_rows,
        checklist_review=automatic_review,
        comparisons=gate_comparisons,
    )
    coverage = build_coverage_matrix(review_plan.get("items") or [])
    checklist_audit = dict(checklist_atomic.get("semantic_engine_audit") or {})
    checklist_audit, checklist_ledger = reconcile_domain_audit(
        checklist_audit,
        rows=list(checklist_atomic.get("atoms") or []),
        checkpoint_domain=checklist_checkpoint,
        previous_audit=dict(previous_semantic.get("checklist") or {}),
        previous_ledger_domain=dict(previous_ledger_domains.get("checklist") or {}),
    )
    checklist_atomic["semantic_engine_audit"] = checklist_audit
    checklist_atoms = list(checklist_atomic.get("atoms") or [])
    if checklist_atoms:
        checklist_atoms[0]["semantic_engine_audit"] = checklist_audit
    checkpoint["_ledger"] = {
        "version": LEDGER_VERSION,
        "snapshot_id": snapshot_id,
        "domains": {
            "assignment": assignment_ledger,
            "checklist": checklist_ledger,
        },
    }
    semantic_summary = {
        "version": "18.4.1-cumulative-ai-ledger",
        "assignment": assignment_audit,
        "checklist": checklist_audit,
        "evidence_coverage_pct": coverage.get("evidence_coverage_pct", 0),
        "strict_coverage_pct": coverage.get("coverage_pct", 0),
        "semantic_consensus_completed": coverage.get("semantic_consensus_completed", 0),
    }
    packets = [
        dict(row.get("semantic_evidence_packet") or {})
        for row in assignment_atomic + list(checklist_atomic.get("atoms") or [])
        if row.get("semantic_evidence_packet")
    ]
    quality_gate = validate_review_plan(
        review_plan,
        object_registry=list(gate_inputs.get("object_registry") or []),
        checklist_rows=list(automatic_review.get("results") or []),
        comparisons=gate_comparisons,
    )

    first.update({
        "core_version": CONTINUATION_VERSION,
        "assignment_compliance": assignment_rows,
        "assignment_atomic_compliance": assignment_atomic,
        "assignment_compliance_summary": assignment_summary,
        "automatic_checklist_review": automatic_review,
        "normative_compliance_audit": normative_rows,
        "deep_evidence_review": deep_review,
        "project_review_plan": review_plan,
        "coverage_matrix": coverage,
        "semantic_evidence_engine": semantic_summary,
        "semantic_project_graph": build_semantic_project_graph(fact_graph, packets),
        "report_quality_gate": quality_gate,
        "verified_core_gate": verified_core_gate,
        "semantic_continuation": {
            "version": CONTINUATION_VERSION,
            "ledger_version": LEDGER_VERSION,
            "snapshot_id": snapshot_id,
            "source_pdf_required": False,
            "cumulative_ai_ledger": checkpoint.get("_ledger"),
            "assignment_checkpoint_entries": sum(len(value) for value in assignment_checkpoint.values() if isinstance(value, dict)),
            "checklist_checkpoint_entries": sum(len(value) for value in checklist_checkpoint.values() if isinstance(value, dict)),
            "quality_gate": quality_gate.get("status"),
            "batch_limits": {
                "assignment": assignment_limit,
                "checklist": checklist_limit,
            },
        },
    })
    for document in documents:
        document["core_version"] = CONTINUATION_VERSION
    _progress(progress_callback, 100, "Готово", "Очередь продолжена; отчёт и Quality Gate пересчитаны")
    return documents, findings, comparisons
