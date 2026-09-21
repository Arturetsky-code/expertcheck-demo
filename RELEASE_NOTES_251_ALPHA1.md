# ExpertCheck 25.1 Alpha 1 — Runtime Integrity

Branch: `codex/expertcheck-25.1-runtime-integrity`

## Purpose

25.1 is deliberately not a coverage release. It fixes contradictions exposed by the
first real user Test 78 on 25.0 before the project moves into the coverage-first
25.2 phase.

## Test 78 baseline that triggered this release

- Assignment: 56 requirements; Core25 UI showed 2 categorical matches, while XLSX
  demoted them back to review.
- AI telemetry: cumulative counters reported more completed Judge/Critic work than
  the row-level execution trace could prove.
- Completeness: the report wrote «Подтверждена» although the matrix itself showed
  an incomplete package; confirmation and completeness were conflated.
- Risk Intelligence: review-only comparison diagnostics could be promoted to
  «Высокий» by historical scenario severity.
- Positive result retained: object/parameter binding no longer confuses the
  89.9 m² building area with the 23.5 m² dust-suppression module area.

## 25.1 changes

1. **Single categorical Assignment verdict path**
   - Core25 public rows carry an explicit integrity-passed marker.
   - The legacy Verified Core gate no longer re-adjudicates a valid Core25 proof
     with incompatible 17.0 proof vocabulary.
   - A Core25 categorical result is still fail-closed unless decision, proof state,
     proof id, trace id and addressable evidence are mutually consistent.

2. **Fail-closed AI telemetry**
   - Current L4 packet rows are authoritative for the queue size.
   - A completed response counts only when it is attached to the current packet row
     and can be reproduced from the checkpoint.
   - Stale/orphan checkpoint ids are pruned and reopened instead of inflating
     completion counters.
   - XLSX exposes telemetry integrity/repair counters.

3. **Risk severity integrity**
   - Knowledge-base recurrence may prioritize a real finding, but cannot elevate a
     REVIEW question above the maximum level allowed by finding qualification.

4. **Completeness semantics**
   - «Неполный комплект» / «Комплект формируется» / «Требует уточнения» is now kept
     separate from «матрица подтверждена пользователем».
   - Reports show actual completeness status, coverage and missing mandatory
     sections separately from user confirmation.

## Automated validation

Validated code HEAD: `30cc031a34764191377398efccf184cdfbd153a5`

- Core25 suite: **80 passed / 0 failed**.
- Core20 regression suite: **95 passed / 0 failed**.
- Results/report integrity suite: **17 passed / 0 failed**.
- Full release-gate diagnostic: **521 passed / 32 classified historical failures / 0 blockers**.
- Historical failure classes: **3 fixture-bound / 4 obsolete / 25 baseline-existing**.
- Core25 compile/release gate: **SUCCESS**.

The AI ledger intentionally keeps the checkpoint as the durable record of
completed provider calls, but 25.1 intersects those responses with the current
eligible packet universe. This preserves valid completed calls while pruning
responses for packets that no longer exist. The report now labels current-run
attempts separately from cumulative checkpoint responses instead of presenting
them as the same counter.

## Release gate

Status: **READY_FOR_SHORT_MANUAL_INTEGRITY_TEST**.

The intended manual check is a short Test 78 integrity rerun. Do **not** spend
quota completing the full AI queue. Verify verdict parity, telemetry semantics,
completeness semantics and risk-level integrity first. A full coverage run is
deferred to 25.2 Coverage Breakthrough.
